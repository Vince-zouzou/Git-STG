import streamlit as st
import docx
import PyPDF2
from PIL import Image
import pytesseract
from models import TranslationResult
from config import MESSAGES, TRANSLATOR_CONFIG
from utils import initial_page_config
from components import render_language_selector
from message import TRANSLATOR_MESSAGES

# 获取语言设置
lang = st.session_state.get("language", "zh-CN")
T = TRANSLATOR_MESSAGES[lang]

# 初始化页面
# initial_page_config("translator")

# 模拟翻译函数
def mock_translate(text, source_lang, target_lang):
    if not text:
        return TranslationResult(source_text=text, translated_text="", source_lang=source_lang, target_lang=target_lang)
    translated_text = f"[翻译] {text} (从 {source_lang} 到 {target_lang})"
    return TranslationResult(source_text=text, translated_text=translated_text, source_lang=source_lang, target_lang=target_lang)

@st.cache_data
def get_translator_config():
    return TRANSLATOR_CONFIG

# 标题
st.header(T["title"])

# 语言选择器
source_lang, target_lang = render_language_selector(lang=lang)

# 标签页
tab1, tab2, tab3, tab4 = st.tabs([T["tabText"], T["tabDoc"], T["tabImage"], T["tabWeb"]])

# 文本翻译
with tab1:
    input_text = st.text_area(T["inputText"], height=150, placeholder=T["placeholder"])
    if st.button(T["translateText"]):
        if input_text:
            with st.spinner(T["translating"]):
                result = mock_translate(input_text, source_lang, target_lang)
                st.text_area(T["result"], value=result.translated_text, height=150)
        else:
            st.warning(T["warnNoText"])

# 文档翻译
with tab2:
    uploaded_file = st.file_uploader(T["uploadDocument"], type=TRANSLATOR_CONFIG["file_types"][:3])
    if uploaded_file and st.button(T["translateDocument"]):
        try:
            if uploaded_file.type == "application/pdf":
                pdf_reader = PyPDF2.PdfReader(uploaded_file)
                text = "".join([page.extract_text() for page in pdf_reader.pages])
            elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                doc = docx.Document(uploaded_file)
                text = "\n".join([para.text for para in doc.paragraphs])
            elif uploaded_file.type == "text/plain":
                text = uploaded_file.read().decode("utf-8")
            else:
                st.error(T["errorFileType"])
                text = None

            if text:
                with st.spinner(T["translating"]):
                    result = mock_translate(text, source_lang, target_lang)
                    st.text_area(T["result"], value=result.translated_text, height=300)
        except Exception as e:
            st.error(f"{T['translationFailed']}: {str(e)}")

# 图片翻译
with tab3:
    uploaded_image = st.file_uploader(T["uploadImage"], type=TRANSLATOR_CONFIG["file_types"][3:])
    if uploaded_image and st.button(T["translateImage"]):
        try:
            image = Image.open(uploaded_image)
            text = pytesseract.image_to_string(image)
            if text:
                with st.spinner(T["translating"]):
                    result = mock_translate(text, source_lang, target_lang)
                    st.text_area(T["extractedText"], value=text, height=150)
                    st.text_area(T["result"], value=result.translated_text, height=150)
            else:
                st.warning(T["noTextExtracted"])
        except Exception as e:
            st.error(f"{T['translationFailed']}: {str(e)}")

# 网页翻译
with tab4:
    url = st.text_input(T["inputUrl"], placeholder="https://example.com")
    if url and st.button(T["translateWeb"]):
        text = f"模拟网页内容: {url}"
        with st.spinner(T["translating"]):
            result = mock_translate(text, source_lang, target_lang)
            st.text_area(T["result"], value=result.translated_text, height=300)

# 使用说明
st.markdown(T["usageInstructions"], unsafe_allow_html=True)