# app.py
import streamlit as st
from config import APP_CONFIG, MESSAGES, LANGUAGES
import pandas as pd 
from utils import load_from_dataset
from EC import Engine
# 设置页面配置（仅在此处调用一次）
st.set_page_config(
    page_title="STG 应用",
    layout=APP_CONFIG["page_layout"],
    initial_sidebar_state="expanded"
)
st.logo(APP_CONFIG["logo_path"], size=APP_CONFIG["logo_size"])

# 初始化 session state
if "language" not in st.session_state:
    st.session_state.language = "zh-CN"  # 默认简体中文

if 'engine' not in st.session_state:
    st.session_state["engine"] = Engine(vectorstore_path="Data/Model", output_excel="Data/Dataset.csv", output_images_dir="Data/images")


# 获取当前语言
lang = st.session_state.language

# 定义页面
pages = [
    st.Page(
        page="pages/main.py",
        title=MESSAGES[lang].get("dashboard_title", "仪表板"),
    ),
    st.Page(
        page="pages/faq.py",
        title=MESSAGES[lang].get("faq_title", "常见问题"),
    ),
    st.Page(
        page="pages/translator.py",
        title=MESSAGES[lang].get("translator_title", "翻译器"),
    ),
    st.Page(
        page="pages/manage_eq.py",
        title=MESSAGES[lang].get("manage_eq_title", "Manage EQ"),
    ),
    
    st.Page(
        page="pages/create.py",
        title=MESSAGES[lang].get("create_eq_title", "Create EQ"),
    ),

]

# 创建导航栏
navigation = st.navigation(pages)

# 在 sidebar 添加语言选择
with st.sidebar:
    st.header(MESSAGES[st.session_state.language]['Setting'])
    selected_language = st.selectbox(
        MESSAGES[lang]["languageSelect"],
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        index=list(LANGUAGES.keys()).index(st.session_state.language),
        key="language_select"
    )
    if st.session_state.language != selected_language:
        st.session_state.language = selected_language
        st.rerun()
    

# 加载全局 CSS
with open("styles.css", "r") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


## 加载全局数据
if st.session_state.get('data') is None:
    st.session_state['data'] = load_from_dataset()

# 运行导航
navigation.run()


