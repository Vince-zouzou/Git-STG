import streamlit as st
import pandas as pd
from models import EQ
from config import MESSAGES, DATE_FORMAT
import math
import datetime
from utils import show_error_message


current_language = st.session_state.language 
if current_language != st.session_state.language:
    st.session_state.language = current_language
    st.rerun()

def load_eqs_cached(_data):
    """
    缓存 EQ 数据加载，优化性能
    :param _data: session_state.data（不可哈希，需加下划线避免缓存失效）
    :return: EQ 对象列表
    """    
    return [
        EQ(
            id=i['Index'],
            eqStatus=i['EQ Status'],
            closedate=i.get('Date', '3000-01-01'),
            customer=i['Customer Name'],
            customerPN=i.get('Customer P/N', 'Unknown'),
            factoryPN=i.get('Factory P/N', "Unknown"),
            selected=False,
            engineer=i.get('Engineer Name', 'Unknown'),
            stgpn=i.get('STG P/N', 'Unknown'),
            basematerial=i.get('Base Material', "Unknown"),
            soldermask=i.get('Solder Mask', 'Unknown'),
            filepath=i.get('FileName', ""),
            plugging=i.get('Via Plugging Type', 'Unknown')
        )
        for i in _data
    ]    

@st.cache_data
def preprocess_dataframe(_eqs):
    """
    缓存 DataFrame 预处理，优化去重和 ID 生成
    :param _eqs: EQ 对象列表（不可哈希，需加下划线）
    :return: 预处理后的 DataFrame
    """
    df = pd.DataFrame([vars(eq) for eq in _eqs])
    df = df.drop_duplicates(subset=['filepath'], keep='first').reset_index(drop=True)
    df['ID'] = df.index
    df.drop(columns=['id'], axis=1, inplace=True)
    return df

def render_data_table(df, column_config, page_size=10, table_key="data_table", lang="en", show_buttons=False, button_callbacks=None):
    """
    渲染带分页和选择框的数据表格，支持按钮区域、固定列顺序和分页控件
    :param df: 数据 DataFrame
    :param column_config: 表格列配置
    :param page_size: 每页显示条数
    :param table_key: 表格唯一键
    :param lang: 语言（en 或 zh）
    :param show_buttons: 是否显示按钮区域（用于 manage_eq.py）
    :param button_callbacks: 按钮回调函数字典，包含 create、edit、export
    :return: 编辑后的 DataFrame
    """
    # Initialize session state
    if "page" not in st.session_state:
        st.session_state.page = 1
    if "page_size" not in st.session_state:
        st.session_state.page_size = page_size
    if "select_all" not in st.session_state:
        st.session_state.select_all = False
    if "selected_rows" not in st.session_state:
        st.session_state.selected_rows = pd.DataFrame(columns=df.columns)

    # Ensure selected and ID columns are present and ordered
    if "ID" not in df.columns:
        df.insert(1, "ID", False)
    else:
        df = df[["ID"] + [col for col in df.columns if col != "ID"]]
    if "selected" not in df.columns:
        df.insert(0, "selected", False)
    else:
        df = df[["selected"] + [col for col in df.columns if col != "selected"]]



    # Pagination calculation
    total_rows = len(df)
    total_pages = math.ceil(total_rows / st.session_state.page_size) if total_rows > 0 else 1
    start_idx = (st.session_state.page - 1) * st.session_state.page_size
    end_idx = min(start_idx + st.session_state.page_size, total_rows)
    paginated_df = df.iloc[start_idx:end_idx].copy()

    # Button area (for manage_eq.py)
    if show_buttons:
        col_buttons = st.columns(4)
        with col_buttons[0]:
            select_all = st.checkbox(MESSAGES[lang]["selectAll"], value=st.session_state.select_all, key=f"select_all_{table_key}")
        with col_buttons[1]:
            if st.button(MESSAGES[lang]["createNewCase"], key=f"create_{table_key}"):
                if button_callbacks and "create" in button_callbacks:
                    button_callbacks["create"]()
        with col_buttons[2]:
            if st.button(MESSAGES[lang]["editEQ"], key=f"edit_{table_key}"):
                if button_callbacks and "edit" in button_callbacks:
                    button_callbacks["edit"](st.session_state.selected_rows)
        with col_buttons[3]:
            if st.button(MESSAGES[lang]["exportEQ"], key=f"export_{table_key}"):
                if button_callbacks and "export" in button_callbacks:
                    button_callbacks["export"](st.session_state.selected_rows)
    else:
        select_all = st.checkbox(MESSAGES[lang]["selectAll"], value=st.session_state.select_all, key=f"select_all_{table_key}")

    # Update select all state
    if select_all:
        paginated_df["selected"] = True
        st.session_state.select_all = True

    else:
        paginated_df["selected"] = False
        st.session_state.select_all = False

    # Render table
    with st.container():
        if paginated_df.empty:
            st.write(MESSAGES[lang]["noDataFound"])
            return paginated_df
        edited_df = st.data_editor(
            paginated_df,
            column_config=column_config,
            hide_index=True,
            use_container_width=True,
            key=table_key
        )

        # Update select all state
        if edited_df["selected"].all() and len(edited_df) > 0:
            st.session_state.select_all = True
        elif not edited_df["selected"].any():
            st.session_state.select_all = False

        # Update selected column
        paginated_df["selected"] = edited_df["selected"]
        st.session_state.selected_rows = paginated_df[paginated_df["selected"] == True]

        # Pagination controls
        col_page1, col_page2, col_page3 = st.columns([2, 3, 2])
        with col_page2:
            st.write(MESSAGES[lang]["pageInfo"].format(
                current_page=st.session_state.page,
                total_pages=total_pages,
                total_items=total_rows
            ))
        with col_page1:
            if st.button(MESSAGES[lang]["previousPage"], disabled=st.session_state.page <= 1, key=f"prev_{table_key}"):
                st.session_state.page = max(1, st.session_state.page - 1)
                st.rerun()
        with col_page3:
            if st.button(MESSAGES[lang]["nextPage"], disabled=st.session_state.page >= total_pages, key=f"next_{table_key}"):
                st.session_state.page = min(total_pages, st.session_state.page + 1)
                st.rerun()
    return paginated_df

def render_filter_controls(filters, df, lang="en"):
    """
    渲染过滤控件，选项从 DataFrame 中动态获取
    :param filters: 过滤条件字典
    :param df: 数据 DataFrame，用于提取唯一值
    :param lang: 语言
    :return: 更新后的过滤条件
    """
    customer_options = [""] + sorted(df['customer'].dropna().unique().tolist())
    engineer_options = [""] + sorted(df['engineer'].dropna().unique().tolist())
    status_options = [""] + sorted(df['eqStatus'].dropna().unique().tolist())

    col1, col2, col3 = st.columns(3)
    with col1:
        filters["keyword"] = st.text_input(MESSAGES[lang]["keywordSearch"], value=filters.get("keyword", ""))
    with col2:
        filters["start_date"] = st.date_input(MESSAGES[lang]["startDate"], value=filters.get("start_date"))
    with col3:
        filters["end_date"] = st.date_input(MESSAGES[lang]["endDate"], value=filters.get("end_date"))

    col6, col7, col8 = st.columns(3)
    with col6:
        filters['customer'] = st.selectbox(MESSAGES[lang]["customerName"], customer_options, index=0)
    with col7:
        filters["engineer_name"] = st.selectbox(MESSAGES[lang]["engineerName"], engineer_options, index=0)
    with col8:
        filters["status"] = st.selectbox(MESSAGES[lang]["allStatus"], status_options, index=0)

    return filters

def filter_dataframe(df, filters, date_column="closedate", date_format=DATE_FORMAT):
    """
    根据过滤条件筛选 DataFrame
    :param df: 输入 DataFrame
    :param filters: 字典，包含过滤条件
    :param date_column: 日期列名
    :param date_format: 日期格式
    :return: 筛选后的 DataFrame
    """
    if df.empty:
        return df
    
    filtered_df = df.copy()
    
    try:
        # Keyword filtering
        if filters.get("keyword"):
            search_columns = ["customerPN", "factoryPN", "stgpn", "customer", "engineer", "basematerial", "soldermask", "plugging"]
            mask = pd.Series(False, index=filtered_df.index)
            for col in search_columns:
                if col in filtered_df.columns:
                    mask |= filtered_df[col].astype(str).str.contains(
                        filters["keyword"], case=False, na=False
                    )
            filtered_df = filtered_df[mask]
            st.session_state.page = 1

        # Customer filtering
        if filters.get("customer"):
            filtered_df = filtered_df[filtered_df["customer"].astype(str) == str(filters["customer"])]
            st.session_state.page = 1
        # Engineer filtering
        if filters.get("engineer_name"):
            filtered_df = filtered_df[filtered_df["engineer"].astype(str) == str(filters["engineer_name"])]
            st.session_state.page = 1
        # Status filtering
        if filters.get("status"):
            filtered_df = filtered_df[filtered_df["eqStatus"].astype(str) == str(filters["status"])]
            st.session_state.page = 1   
        # Date range filtering
        if filters.get("start_date") or filters.get("end_date"):
            if filters.get("start_date") and filters.get("end_date"):
                if filters["start_date"] > filters["end_date"]:
                    show_error_message(MESSAGES[current_language]["invalidDateRangeError"])
                    return pd.DataFrame(columns=df.columns)
            
            try:
                filtered_df["_temp_date"] = pd.to_datetime(
                    filtered_df[date_column], 
                    format='mixed',
                    errors='coerce'
                ).dt.date
                
                if filters.get("start_date"):
                    filtered_df = filtered_df[filtered_df["_temp_date"] >= filters["start_date"]]
                    
                if filters.get("end_date"):
                    filtered_df = filtered_df[filtered_df["_temp_date"] <= filters["end_date"]]

                st.session_state.page = 1
            except Exception as e:
                show_error_message(MESSAGES[current_language]["dateFilterError"].format(error=str(e)))
            finally:
                if "_temp_date" in filtered_df.columns:
                    filtered_df = filtered_df.drop(columns=["_temp_date"])

    except Exception as e:
        show_error_message(MESSAGES[current_language]["filterError"].format(error=str(e)))
        return pd.DataFrame(columns=df.columns)
        
    return filtered_df

def create_new_case():
    """
    处理创建新案例的点击事件
    """
    st.session_state.current_eq = {}
    st.session_state.questions = []
    st.session_state.filepath = '' 
    st.switch_page("pages/create.py")

def edit_eq(selected_rows):
    """
    处理编辑 EQ 的点击事件
    :param selected_rows: 选中的行数据
    """
    if len(selected_rows) == 1:
        selected_eq = selected_rows.iloc[0]
        filepath = selected_eq['filepath']
        
        eq_data = next((item for item in st.session_state.data if item.get('FileName') == filepath), None)
        if not eq_data:
            st.error(MESSAGES[current_language]["eqNotFoundError"])
            return

        eq_info = {
            'Index': eq_data.get('Index'),
            'Customer Name': eq_data.get('Customer Name', ''),
            'Customer P/N': eq_data.get('Customer P/N', ''),
            'STG P/N': eq_data.get('STG P/N', ''),
            'Factory P/N': eq_data.get('Factory P/N', ''),
            'Engineer Name': eq_data.get('Engineer Name', ''),
            'Date': eq_data.get('Date', datetime.datetime.today().strftime(DATE_FORMAT)),
            'EQ Status': eq_data.get('EQ Status', 'Reviewing'),
            'Via Plugging Type': eq_data.get('Via Plugging Type', ''),
            'Panel Size': eq_data.get('Panel Size', ''),
            'Base Material': eq_data.get('Base Material', ''),
            'Solder Mask': eq_data.get('Solder Mask', ''),
        }

        questions = []
        eq_list_entry = [item for item in st.session_state.data if item.get('FileName') == filepath]
        questions = eq_list_entry

        st.session_state.current_eq = eq_info
        st.session_state.questions = questions
        st.session_state.filepath = filepath

        st.switch_page("pages/create.py")
    else:
        st.error(MESSAGES[current_language]["singleEQEditError"])

def export_eq(selected_rows):
    """
    处理导出 EQ 的点击事件
    :param selected_rows: 选中的行数据
    """
    if not selected_rows.empty:
        with st.spinner(MESSAGES[current_language]["exportingEQs"].format(count=len(selected_rows))):
            csv = selected_rows.to_csv(index=False)
            st.download_button(
                label=MESSAGES[current_language]["downloadCSV"],
                data=csv,
                file_name=MESSAGES[current_language]["exportedEQsFile"],
                mime="text/csv",
                key="download_csv"
            )
            st.success(MESSAGES[current_language]["exportSuccess"].format(count=len(selected_rows)))
    else:
        st.error(MESSAGES[current_language]["selectEQExportError"])

# Main page logic
st.subheader(MESSAGES[current_language]["searchEQHeader"])

# Load data (cached)
eqs = load_eqs_cached(st.session_state.data)
df = preprocess_dataframe(eqs)

# Filter controls
filters = {}
filters = render_filter_controls(filters, df, lang=current_language)

# Data filtering
filtered_df = filter_dataframe(df, filters)

# Table column configuration
column_config = {
    "selected": st.column_config.CheckboxColumn(MESSAGES[current_language]["selectColumn"], default=False, width="small"),
    "ID": st.column_config.NumberColumn(MESSAGES[current_language]["idColumn"], width="small"),
    "eqStatus": st.column_config.TextColumn(MESSAGES[current_language]["eqStatusColumn"], width="small"),
    "closedate": st.column_config.TextColumn(MESSAGES[current_language]["closeDateColumn"], width="small"),
    "customer": st.column_config.TextColumn(MESSAGES[current_language]["customerColumn"], width="medium"),
    "customerPN": st.column_config.TextColumn(MESSAGES[current_language]["customerPNColumn"], width="medium"),
    "factoryPN": st.column_config.TextColumn(MESSAGES[current_language]["factoryPNColumn"], width="medium"),
    "engineer": st.column_config.TextColumn(MESSAGES[current_language]["engineerColumn"], width="medium"),
    "stgpn": st.column_config.TextColumn(MESSAGES[current_language]["stgPNColumn"], width="medium"),
    "basematerial": st.column_config.TextColumn(MESSAGES[current_language]["baseMaterialColumn"], width="medium"),
    "soldermask": st.column_config.TextColumn(MESSAGES[current_language]["solderMaskColumn"], width="medium"),
    "filepath": st.column_config.TextColumn(MESSAGES[current_language]["filePathColumn"], width="large"),
    "plugging": st.column_config.TextColumn(MESSAGES[current_language]["pluggingColumn"], width="medium"),
}

# Render table with button area
button_callbacks = {
    "create": create_new_case,
    "edit": edit_eq,
    "export": export_eq
}

edited_df = render_data_table(
    filtered_df,
    column_config,
    lang=current_language,
    table_key="eq_table",
    show_buttons=True,
    button_callbacks=button_callbacks
)

# Back to dashboard button
if st.button(MESSAGES[current_language]["backToDashboard"]):
    st.switch_page("pages/main_new.py")