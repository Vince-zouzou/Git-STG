# utils.py
import streamlit as st
import pandas as pd
from config import APP_CONFIG, MESSAGES, LANGUAGES, DATE_FORMAT, source_path
import os
import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def initial_page_config(page_key):
    """
    初始化页面特定配置，包括 session state 和全局 CSS
    :param page_key: 页面键，用于确定当前页面
    """
    # Initialize session state
    if "language" not in st.session_state:
        st.session_state.language = "en"  # Default to English
    if "current_page" not in st.session_state:
        st.session_state.current_page = page_key  # Track current page

    # Load global CSS
    with open("styles.css", "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

def initialize_session_state(keys_defaults):
    """
    初始化 session state 键值对
    :param keys_defaults: 字典，包含键和默认值
    """
    for key, default in keys_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

def render_pagination(total_items, page_size, page_key, lang="en"):
    """
    渲染分页控件
    :param total_items: 数据总条数
    :param page_size: 每页显示条数
    :param page_key: session state 中的页面键
    :param lang: 语言（zh-CN, zh-TW, de, en）
    :return: 总页数
    """
    total_pages = max(1, (total_items + page_size - 1) // page_size)
    col_prev, col_page, col_next, col_label, col_pages = st.columns([1, 2, 1, 2, 1])
    with col_prev:
        if st.button(MESSAGES[lang]["previousPage"], disabled=st.session_state[page_key] <= 1):
            st.session_state[page_key] -= 1
    with col_page:
        st.write(f"{MESSAGES[lang]['page']} {st.session_state[page_key]} {MESSAGES[lang]['of']} {total_pages}")
    with col_next:
        if st.button(MESSAGES[lang]["nextPage"], disabled=st.session_state[page_key] >= total_pages):
            st.session_state[page_key] += 1
    with col_pages:
        st.write(MESSAGES[lang]["perPage"])
    with col_label:
        new_page_size = st.selectbox(
            MESSAGES[lang]["perPage"],
            [10, 20, 50, 100],
            index=[10, 20, 50, 100].index(st.session_state.get("page_size", page_size)),
            label_visibility='collapsed'
        )
        if new_page_size != st.session_state.get("page_size"):
            st.session_state.page_size = new_page_size
            st.session_state[page_key] = 1
    return total_pages

def filter_dataframe(df, filters, date_column="changed", date_format=DATE_FORMAT):
    """
    根据过滤条件筛选 DataFrame
    :param df: 输入 DataFrame
    :param filters: 字典，包含过滤条件
    :param date_column: 日期列名
    :param date_format: 日期格式
    :return: 筛选后的 DataFrame
    """
    filtered_df = df.copy()
    if filters.get("keyword"):
        mask = filtered_df[["customer", "customerPN"]].apply(
            lambda x: x.str.contains(filters["keyword"], case=False, na=False)).any(axis=1)
        filtered_df = filtered_df[mask]
    if filters.get("item_code"):
        filtered_df = filtered_df[filtered_df["pn"].str.contains(filters["item_code"], case=False, na=False)]
    if filters.get("start_date"):
        filtered_df = filtered_df[pd.to_datetime(filtered_df[date_column], format=date_format) >= pd.to_datetime(filters["start_date"])]
    if filters.get("end_date"):
        filtered_df = filtered_df[pd.to_datetime(filtered_df[date_column], format=date_format) <= pd.to_datetime(filters["end_date"])]
    if filters.get("status"):
        filtered_df = filtered_df[filtered_df["eqStatus"] == filters["status"]]
    if filters.get("factory"):
        filtered_df = filtered_df[filtered_df["factory"] == filters["factory"]]
    return filtered_df

def render_QA_card(data):
    """
    渲染一个问答卡片，包含问题和回答信息。
    
    Args:
        data (dict): 包含问答信息的字典，预期键包括：
            - date: 日期
            - customer: 客户名称
            - status: 状态
            - stg: STG P/N
            - engineer: 工程师
            - image: 问题相关图片（可选，字符串或列表）
            - answer: 客户回复
            - answer_image: 回答相关图片（可选，字符串或列表）
            - question: 问题
            - similarity: 相似度
    """
    with st.expander(
        f"{MESSAGES[st.session_state.language]['questionPrefix']} {data.get('question', MESSAGES[st.session_state.language]['unknown'])}"
        + " -------- " +
        f"{MESSAGES[st.session_state.language]['similarityLabel'].format(similarity=round(float(data.get('similarity', 0)), 3))}",
        expanded=True
    ):
        with st.container(border=True):
            col0, col1, col2 = st.columns([1, 1, 1])
            col0.write(f"{MESSAGES[st.session_state.language]['faqTime']} {data.get('date', MESSAGES[st.session_state.language]['unknown'])}")
            col0.write(f"{MESSAGES[st.session_state.language]['faqCustomer']} {data.get('customer', MESSAGES[st.session_state.language]['unknown'])}")
            col1.write(f"{MESSAGES[st.session_state.language]['faqStatus']} {data.get('status', MESSAGES[st.session_state.language]['unknown'])}")
            col1.write(f"{MESSAGES[st.session_state.language]['faqStgPN']} {data.get('stg', MESSAGES[st.session_state.language]['unknown'])}")
            col2.write(f"{MESSAGES[st.session_state.language]['faqEngineer']} {data.get('engineer', MESSAGES[st.session_state.language]['unknown'])}")
            
            col0, col1 = st.columns([2, 1])
            with col0:
                images = data.get('image')
                if images:
                    if isinstance(images, list):
                        for img in images:
                            try:
                                st.image(os.path.join(source_path['images'], img))
                            except:
                                pass

        with st.container(border=True):
            st.write(f"{MESSAGES[st.session_state.language]['faqCustomerReply']} {data.get('answer', MESSAGES[st.session_state.language]['noReply'])}")
            col0, col1 = st.columns([2, 1])
            with col0:
                answer_images = data.get('answer_image')
                if answer_images:
                    if isinstance(answer_images, list):
                        for img in answer_images:
                            try:
                                st.image(img, caption=MESSAGES[st.session_state.language]["replyImageCaption"])
                            except:
                                pass

@st.cache_data
def load_from_dataset(input_excel=source_path['database'], images_dir=source_path['images']):
    """
    从 CSV 文件加载数据集，合并图片字段，清理冗余。
    
    Args:
        input_excel (str): CSV 文件路径
        images_dir (str): 图片存储目录
    
    Returns:
        list: 数据集，包含每行数据的字典
    """
    if not os.path.exists(input_excel):
        error_msg = MESSAGES[st.session_state.language]["csvFileNotFound"].format(file=input_excel)
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)

    try:
        df = pd.read_csv(input_excel, encoding='utf-8', low_memory=False)
    except UnicodeDecodeError:
        warning_msg = MESSAGES[st.session_state.language]["csvUtf8Warning"].format(file=input_excel)
        logger.warning(warning_msg)
        df = pd.read_csv(input_excel, encoding='latin1', low_memory=False)
    except Exception as e:
        error_msg = MESSAGES[st.session_state.language]["csvReadError"].format(file=input_excel, error=str(e))
        logger.error(error_msg)
        raise ValueError(error_msg)

    if df.empty:
        warning_msg = MESSAGES[st.session_state.language]["csvEmptyWarning"].format(file=input_excel)
        logger.warning(warning_msg)
        return []

    columns = df.columns.tolist()
    dataset = []
    image_fields = ['Description', 'Factory Suggestion', 'STG Proposal', 'Customer Decision']
    image_files = set(os.listdir(images_dir))
    missing_images = set()

    for idx, row in df.iterrows():
        try:
            issue = {}
            for col in columns:
                if pd.isna(row.get(col)):
                    if col in image_fields:
                        issue[col] = issue.get(col, {'text': None, 'image': []})
                    else:
                        issue[col] = None
                    continue

                if col.endswith('_Images'):
                    field_name = col.replace('_Images', '')
                    images = str(row[col]).split(';') if isinstance(row[col], str) else []
                    valid_images = set(img.strip() for img in images if img.strip() and img.strip() in image_files)
                    for img in images:
                        if img.strip() and img.strip() not in image_files:
                            missing_images.add((idx + 2, img.strip()))
                    issue[field_name] = issue.get(field_name, {'text': None, 'image': []})
                    issue[field_name]['image'].extend(valid_images)
                elif col in image_fields:
                    issue[col] = issue.get(col, {'text': None, 'image': []})
                    issue[col]['text'] = row[col]
                else:
                    issue[col] = row[col]

            issue = {k: v for k, v in issue.items() if not (v is None or (isinstance(v, dict) and v.get('text') is None and not v.get('image')))}
            dataset.append(issue)
        except Exception as e:
            warning_msg = MESSAGES[st.session_state.language]["rowProcessingError"].format(row=idx + 2, error=str(e))
            logger.warning(warning_msg)
            continue

    for row_num, img in missing_images:
        warning_msg = MESSAGES[st.session_state.language]["imageNotFoundWarning"].format(row=row_num, image=img, dir=images_dir)
        logger.warning(warning_msg)

    if not dataset:
        warning_msg = MESSAGES[st.session_state.language]["csvNoDataWarning"].format(file=input_excel)
        logger.warning(warning_msg)
    
    success_msg = MESSAGES[st.session_state.language]["csvLoadSuccess"].format(file=input_excel, count=len(dataset))
    logger.info(success_msg)
    return dataset

def show_error_message(message):
    error_html = f"""
    <div class="error-box">
        {message}
    </div>
    """
    st.markdown(error_html, unsafe_allow_html=True)