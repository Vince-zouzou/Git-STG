import streamlit as st
import docx
import PyPDF2
from PIL import Image
import pytesseract
from models import TranslationResult
from config import MESSAGES, TRANSLATOR_CONFIG
from utils import initial_page_config

# Initialize page
# initial_page_config("translator")


current_language = st.session_state.language

if current_language != st.session_state.language:
    st.session_state.language = current_language
    st.rerun()

# Cache translator config
@st.cache_data
def get_translator_config():
    return TRANSLATOR_CONFIG

# Header
st.header(MESSAGES[current_language]["translatorHeader"])

# Language selection
col0, col1,col2 = st.columns([3,1,3])
source_lang = col0.selectbox(
    MESSAGES[current_language]["sourceLang"],
    options=TRANSLATOR_CONFIG["languages"],
    index=0
)
target_lang = col2.selectbox(
    MESSAGES[current_language]["targetLang"],
    options=[lang for lang in TRANSLATOR_CONFIG["languages"] if lang != "Auto Detect"],
    index=1 if source_lang != "English" else 2
)

# Mock translation function
def mock_translate(text, source_lang, target_lang):
    if not text:
        return TranslationResult(source_text=text, translated_text="", source_lang=source_lang, target_lang=target_lang)
    translated_text = f"[Translated] {text} (from {source_lang} to {target_lang})"
    return TranslationResult(source_text=text, translated_text=translated_text, source_lang=source_lang, target_lang=target_lang)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs([
    MESSAGES[current_language]["tabText"],
    MESSAGES[current_language]["tabDocument"],
    MESSAGES[current_language]["tabImage"],
    MESSAGES[current_language]["tabWeb"]
])

# Text translation
with tab1:
    input_text = st.text_area(
        MESSAGES[current_language]["inputText"],
        height=150,
        placeholder=MESSAGES[current_language]["inputText"]
    )
    if st.button(MESSAGES[current_language]["translateText"]):
        with st.container():
            if input_text:
                with st.spinner(MESSAGES[current_language]["translating"]):
                    result = mock_translate(input_text, source_lang, target_lang)
                    st.text_area(
                        MESSAGES[current_language]["translationResult"],
                        value=result.translated_text,
                        height=150
                    )
            else:
                st.warning(MESSAGES[current_language]["enterTextWarning"])

# Document translation
with tab2:
    uploaded_file = st.file_uploader(
        MESSAGES[current_language]["uploadDocument"],
        type=TRANSLATOR_CONFIG["file_types"][:3]
    )
    if uploaded_file and st.button(MESSAGES[current_language]["translateDocument"]):
        with st.container():
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
                    st.error(MESSAGES[current_language]["unsupportedFileType"])
                    text = None

                if text:
                    with st.spinner(MESSAGES[current_language]["translating"]):
                        result = mock_translate(text, source_lang, target_lang)
                        st.text_area(
                            MESSAGES[current_language]["translationResult"],
                            value=result.translated_text,
                            height=300
                        )
            except Exception as e:
                st.error(f"{MESSAGES[current_language]['translationFailed']}: {str(e)}")

# Image translation
with tab3:
    uploaded_image = st.file_uploader(
        MESSAGES[current_language]["uploadImage"],
        type=TRANSLATOR_CONFIG["file_types"][3:]
    )
    if uploaded_image and st.button(MESSAGES[current_language]["translateImage"]):
        with st.container():
            try:
                image = Image.open(uploaded_image)
                text = pytesseract.image_to_string(image)
                if text:
                    with st.spinner(MESSAGES[current_language]["translating"]):
                        result = mock_translate(text, source_lang, target_lang)
                        st.text_area(
                            MESSAGES[current_language]["extractedText"],
                            value=text,
                            height=150
                        )
                        st.text_area(
                            MESSAGES[current_language]["translationResult"],
                            value=result.translated_text,
                            height=150
                        )
                else:
                    st.warning(MESSAGES[current_language]["noTextExtracted"])
            except Exception as e:
                st.error(f"{MESSAGES[current_language]['translationFailed']}: {str(e)}")

# Web translation
with tab4:
    url = st.text_input(
        MESSAGES[current_language]["inputUrl"],
        placeholder="https://example.com"
    )
    if url and st.button(MESSAGES[current_language]["translateWeb"]):
        with st.container():
            text = f"Mock web content: {url}"
            with st.spinner(MESSAGES[current_language]["translating"]):
                result = mock_translate(text, source_lang, target_lang)
                st.text_area(
                    MESSAGES[current_language]["translationResult"],
                    value=result.translated_text,
                    height=300
                )

# Usage instructions
st.markdown(MESSAGES[current_language]["usageInstructions"], unsafe_allow_html=True)