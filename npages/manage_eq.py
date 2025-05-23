import streamlit as st
import pandas as pd
from models import EQ
from config import MESSAGES, DATE_FORMAT
import math
import datetime
from message import MANAGE_MESSAGES


lang = st.session_state.get("language", "zh-CN")
T = MANAGE_MESSAGES[lang]

def load_eqs_cached(_data):
    """
    缓存 EQ 数据加载，优化性能
    :param _data: session_state.data（不可哈希，需加下划线避免缓存失效）
    :return: EQ 对象列表
    """
    t = []
    for i in _data:
        t.append(EQ(id=i['Index'], eqStatus=i['EQ Status'], closedate=i.get('Date', '3000-01-01'), customer=i['Customer Name'],
                    customerPN=i.get('Customer P/N', 'Unknown'), factoryPN=i.get('Factory P/N', "Unknown"), selected=False,
                    engineer=i.get('Engineer Name', 'Unknown'), stgpn=i.get('STG P/N', 'Unknown'), basematerial=i.get('Base Material', "Unknown"),
                    soldermask=i.get('Solder Mask', 'Unknown'), filepath=i.get('FileName', ""), plugging=i.get('Via Plugging Type', 'Unknown')))
    return t

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
    # 初始化 session state
    if "page" not in st.session_state:
        st.session_state.page = 1
    if "page_size" not in st.session_state:
        st.session_state.page_size = page_size
    if "select_all" not in st.session_state:
        st.session_state.select_all = False
    if "selected_rows" not in st.session_state:
        st.session_state.selected_rows = pd.DataFrame(columns=df.columns)

    # 确保 selected 列存在并位于首位
    if "ID" not in df.columns:
        df.insert(1, "ID", False)
    else:
        df = df[["ID"] + [col for col in df.columns if col != "ID"]]
    if "selected" not in df.columns:
        df.insert(0, "selected", False)
    else:
        df = df[["selected"] + [col for col in df.columns if col != "selected"]]

    # 分页计算
    total_rows = len(df)
    total_pages = math.ceil(total_rows / st.session_state.page_size) if total_rows > 0 else 1
    start_idx = (st.session_state.page - 1) * st.session_state.page_size
    end_idx = min(start_idx + st.session_state.page_size, total_rows)
    #st.write(start_idx,end_idx,st.session_state.page-1,st.session_state.page_size)
    paginated_df = df.iloc[start_idx:end_idx].copy()
    #st.write(df)

    # 按钮区域（仅 manage_eq.py）
    if show_buttons:
        col_buttons = st.columns(4)
        with col_buttons[0]:
            select_all = st.checkbox(T["selectAll"], value=st.session_state.select_all, key=f"select_all_{table_key}")
        with col_buttons[1]:
            if st.button(T["createNew"], key=f"create_{table_key}"):
                if button_callbacks and "create" in button_callbacks:
                    button_callbacks["create"]()
        with col_buttons[2]:
            if st.button(T["editEQ"], key=f"edit_{table_key}"):
                if button_callbacks and "edit" in button_callbacks:
                    button_callbacks["edit"](st.session_state.selected_rows)
        with col_buttons[3]:
            if st.button(T["exportEQ"], key=f"export_{table_key}"):
                if button_callbacks and "export" in button_callbacks:
                    button_callbacks["export"](st.session_state.selected_rows)
    else:
        select_all = st.checkbox(T["selectAll"], value=st.session_state.select_all, key=f"select_all_{table_key}")

    # 更新全选状态
    if select_all:
        paginated_df["selected"] = True
        st.session_state.select_all = True
    else:
        paginated_df["selected"] = False
        st.session_state.select_all = False

    # 渲染表格
    with st.container():
        if paginated_df.empty:
            st.write(T["noDataFound"])
            return paginated_df
        edited_df = st.data_editor(
            paginated_df,
            column_config=column_config,
            hide_index=True,
            use_container_width=True,
            key=table_key
        )

        # 更新全选状态
        if edited_df["selected"].all() and len(edited_df) > 0:
            st.session_state.select_all = True
        elif not edited_df["selected"].any():
            st.session_state.select_all = False

        # 更新 selected 列
        paginated_df["selected"] = edited_df["selected"]
        st.session_state.selected_rows = paginated_df[paginated_df["selected"] == True]

        # 分页控件
    col_page1, col_page2, col_page3 = st.columns([2, 3, 2])
    with col_page2:
        st.write(f"{T['page']} {st.session_state.page} / {total_pages}")
    with col_page1:
        if st.button(T["prevPage"], disabled=st.session_state.page <= 1, key=f"prev_{table_key}"):
            st.session_state.page = max(1, st.session_state.page - 1)
            st.rerun()
    with col_page3:
        if st.button(T["nextPage"], disabled=st.session_state.page >= total_pages, key=f"next_{table_key}"):
            st.session_state.page = min(total_pages, st.session_state.page + 1)
            st.rerun()
    return paginated_df


def render_filter_controls(filters, df, lang="en"):
    """
    渲染过滤控件，选项从 DataFrame 中动态获取
    :param filters: 过滤条件字典
    :param df: 数据 DataFrame，用于提取唯一值
    :param lang: 语言（en 或 zh）
    :return: 更新后的过滤条件
    """

    # 提取唯一值作为选项
    customer_options = [""] + sorted(df['customer'].dropna().unique().tolist())
    engineer_options = [""] + sorted(df['engineer'].dropna().unique().tolist())
    status_options = [""] + sorted(df['eqStatus'].dropna().unique().tolist())

    col1, col2, col3 = st.columns(3)
    with col1:
        filters["keyword"] = st.text_input('关键词检索', value=filters.get("keyword", ""))
    with col2:
        filters["start_date"] = st.date_input("开始日期", value=filters.get("start_date"))
    with col3:
        filters["end_date"] = st.date_input("结束日期", value=filters.get("end_date"))

    col6, col7, col8 = st.columns(3)
    with col6:
        filters['customer'] = st.selectbox('客户名称', customer_options, index=0)
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
        # 关键词筛选（在所有文本字段中搜索）
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

        # 客户筛选
        if filters.get("customer"):
            filtered_df = filtered_df[filtered_df["customer"].astype(str) == str(filters["customer"])]
            #st.write(filtered_df)
            st.session_state.page = 1
        # 工程师筛选
        if filters.get("engineer_name"):
            filtered_df = filtered_df[filtered_df["engineer"].astype(str) == str(filters["engineer_name"])]
            st.session_state.page = 1
        # 状态筛选
        if filters.get("status"):
            filtered_df = filtered_df[filtered_df["eqStatus"].astype(str) == str(filters["status"])]
            st.session_state.page = 1   
        # 日期范围筛选
        if filters.get("start_date") or filters.get("end_date"):
            if filters.get("start_date") and filters.get("end_date"):
                if filters["start_date"] > filters["end_date"]:
                    st.error(T["startAfterEnd"])
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
                st.error(f"{T['dateFilterError']}: {str(e)}")
            finally:
                if "_temp_date" in filtered_df.columns:
                    filtered_df = filtered_df.drop(columns=["_temp_date"])

    except Exception as e:
        st.error(f"{T['filterFailed']}: {str(e)}")
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
        # 获取选中的 EQ 数据
        selected_eq = selected_rows.iloc[0]
        filepath = selected_eq['filepath']
        
        # 从 st.session_state.data 查找 EQ 详细信息
        eq_data = next((item for item in st.session_state.data if item.get('FileName') == filepath), None)
        if not eq_data:
            st.error(T["notFound"])
            return

        # 构造 EQ 信息
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
            'Panel Size': eq_data.get('Panel Size', ''),  # 假设有此字段，若无需添加
            'Base Material': eq_data.get('Base Material', ''),
            'Solder Mask': eq_data.get('Solder Mask', ''),
        }

        # 查找问题卡信息（假设存储在 st.session_state.eq_list）
        questions = []
        eq_list_entry = [item for item in st.session_state.data if item.get('FileName') == filepath]
        #st.write(eq_list_entry)
        questions = eq_list_entry

        # 将数据存入 session_state 以供 create.py 使用
        st.session_state.current_eq = eq_info
        st.session_state.questions = questions
        st.session_state.filepath = filepath  # 存储 filepath 以便保存时关联


        # 跳转到 create.py
        st.switch_page("pages/create.py")
        #st.write(st.session_state.current_eq)
        #st.write(st.session_state.questions)
        #st.write(st.session_state.filepath)
    else:
        st.error("请仅选择一个 EQ 进行编辑。")

def export_eq(selected_rows):
    """
    处理导出 EQ 的点击事件
    :param selected_rows: 选中的行数据
    """
    if not selected_rows.empty:
        with st.spinner(f"正在导出 {len(selected_rows)} 个 EQ..."):
            csv = selected_rows.to_csv(index=False)
            st.download_button(
                label="下载 CSV",
                data=csv,
                file_name="exported_eqs.csv",
                mime="text/csv",
                key="download_csv"
            )
            st.success(f"{len(selected_rows)} 个 EQ 已导出！")
    else:
        st.error(T["onlySelectOne"])

# 主页面逻辑
st.subheader(T["searchEQ"])

# 加载数据（使用缓存）
eqs = load_eqs_cached(st.session_state.data)
df = preprocess_dataframe(eqs)

# 过滤控件
filters = {}
filters = render_filter_controls(filters, df, lang="zh-CN")

# 数据过滤
filtered_df = filter_dataframe(df, filters)

# 表格列配置
column_config = {
    "selected": st.column_config.CheckboxColumn("选择", default=False, width="small"),
    "ID": st.column_config.NumberColumn("ID", width="small"),
    "eqStatus": st.column_config.TextColumn("EQ 状态", width="small"),
    "closedate": st.column_config.TextColumn("关闭日期", width="small"),
    "customer": st.column_config.TextColumn("客户", width="medium"),
    "customerPN": st.column_config.TextColumn("客户 P/N", width="medium"),
    "factoryPN": st.column_config.TextColumn("工厂 P/N", width="medium"),
    "engineer": st.column_config.TextColumn("工程师", width="medium"),
    "stgpn": st.column_config.TextColumn("STG P/N", width="medium"),
    "basematerial": st.column_config.TextColumn("基材", width="medium"),
    "soldermask": st.column_config.TextColumn("阻焊", width="medium"),
    "filepath": st.column_config.TextColumn("文件路径", width="large"),
    "plugging": st.column_config.TextColumn("塞孔类型", width="medium"),
}

# 渲染表格，启用按钮区域
button_callbacks = {
    "create": create_new_case,
    "edit": edit_eq,
    "export": export_eq
}

edited_df = render_data_table(
    filtered_df,
    column_config,
    lang="zh-CN",
    table_key="eq_table",
    show_buttons=True,
    button_callbacks=button_callbacks
)

# 返回仪表板按钮
if st.button(T["backToDashboard"]):
    st.switch_page("pages/main_new.py")