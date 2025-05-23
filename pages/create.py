# new_create.py
import streamlit as st
from datetime import datetime
from utils import initialize_session_state, render_QA_card
from config import DATE_FORMAT, MESSAGES, LANGUAGES, source_path
from PIL import Image
from ustai import AI
from EC import Engine
import os 

# Initialize session state
initialize_session_state({
    "current_eq": None,
    "questions": [],
    "filepath": None,
    "language": "en"  # Default language, consistent with LANGUAGES in config.py
})

current_language = st.session_state.language
if current_language not in LANGUAGES:
    st.session_state.language = "en"  # Fallback to English if invalid language
    current_language = "en"
    st.rerun()

# Template for empty EQ card
empty_eq_card_temp = {
    "Index": len(st.session_state.data) + 1 if "data" in st.session_state else 1,
    "No": len(st.session_state.questions) + 1,
    "Description": {
        "text": MESSAGES[current_language]["questionDescription"],
        "image": []
    },
    "Factory Suggestion": {
        "text": MESSAGES[current_language]["engineerSuggestion"],
        "image": []
    },
    "STG Proposal": {
        "text": "",
        "image": []
    },
    "EQ Status": MESSAGES[current_language]["pendingStatus"],
    "Customer Name": st.session_state.current_eq.get("Customer Name", "") if st.session_state.current_eq else "",
    "Customer P/N": st.session_state.current_eq.get("Customer P/N", "") if st.session_state.current_eq else "",
    "Factory P/N": st.session_state.current_eq.get("Factory P/N", "") if st.session_state.current_eq else "",
    "Base Material": st.session_state.current_eq.get("Base Material", "") if st.session_state.current_eq else "",
    "Solder Mask": st.session_state.current_eq.get("Solder Mask", "") if st.session_state.current_eq else "",
    "Via Plugging Type": st.session_state.current_eq.get("Via Plugging Type", "") if st.session_state.current_eq else "",
    "Engineer Name": st.session_state.current_eq.get("Engineer Name", "") if st.session_state.current_eq else "",
    "Panel Size": st.session_state.current_eq.get("Panel Size", "") if st.session_state.current_eq else "",
    "STG P/N": st.session_state.current_eq.get("STG P/N", "") if st.session_state.current_eq else "",
    "FileName": st.session_state.current_eq.get("FileName", "") if st.session_state.current_eq else "",
    "Previous Case": False,
    "Closed Date": "3000-01-01"
}

# Initialize engine and session state variables
if 'engine' not in st.session_state:
    st.session_state["engine"] = Engine(
        vectorstore_path=source_path["model"],
        output_excel=source_path["database"],
        output_images_dir=source_path["images"]
    )
if 'cEQ' not in st.session_state:
    st.session_state["cEQ"] = {'index': None, 'question': empty_eq_card_temp}
if "search_button" not in st.session_state:
    st.session_state['search_button'] = False
if 'final_description' not in st.session_state:
    st.session_state['final_description'] = None

# Helper function to validate index
def validate_index(index, questions):
    return isinstance(index, int) and 0 <= index < len(questions)

# Search function
def searching(final_description, customer_name):
    with st.spinner(MESSAGES[current_language]["searching"]):
        similar_issues = st.session_state.engine.search_similar_descriptions(
            final_description,
            customer_name=customer_name,
            k=source_path["search"]["default_k"]
        )
        searching_result_card(similar_issues)

def searching_result_card(issues):
    tab0, tab1, tab2 = st.tabs([
        MESSAGES[current_language]["eqList"],
        MESSAGES[current_language]["generalSpecification"] if "generalSpecification" in MESSAGES[current_language] else "General Specification",
        MESSAGES[current_language]["customerSpecification"] if "customerSpecification" in MESSAGES[current_language] else "Customer Specification"
    ])
    with tab0:
        for i, issue in enumerate(issues):
            qa_data = {
                "date": issue.get("Date"),
                "customer": issue.get("Customer Name"),
                "status": issue.get("Status"),
                "stg": issue.get("STG P/N"),
                "engineer": issue.get("Engineer"),
                "image": issue.get("Description", {'text': MESSAGES[current_language]["No Description"], 'image': []})['image'],
                "answer": issue.get('Customer Decision', {'text': MESSAGES[current_language]["noReply"], 'image': []})['text'],
                "answer_image": issue.get('Customer Decision', {'text': MESSAGES[current_language]["noReply"], 'image': []})['image'],
                'question': issue.get("Description", {'text': MESSAGES[current_language]["No Description"], 'image': []})['text'],
                'similarity': issue.get("similarity_score")
            }
            render_QA_card(qa_data)

def render_question_form(info, index):
    col0, col1, col2 = st.columns([5, 1, 1])
    if isinstance(index, int):
        col0.write(f'{MESSAGES[current_language]["questionLabel"]} {index + 1}')
    else:
        col0.write(MESSAGES[current_language]["NewQ"])

    save_button = col1.button(MESSAGES[current_language]["save"], key=f"save_{index}")
    delete_button = col2.button(MESSAGES[current_language]["delete"], key=f"delete_{index}")

    if info:
        question = st.text_area(
            MESSAGES[current_language]["descriptionLabel"],
            key=f"question_{index}",
            placeholder=MESSAGES[current_language]["questionDescription"]
        )

        current_images = info.get("Description", {'text': MESSAGES[current_language]["questionDescription"], 'image': []})['image']
        image = st.file_uploader(
            MESSAGES[current_language]["uploadImageLabel"],
            type=["jpg", "jpeg", "png"],
            key=f"image_{index}"
        )
        if image:
            current_images = [image]
        for img in current_images:
            if img:
                st.write(img)
                #st.image(img, caption=MESSAGES[current_language]["uploadedImageCaption"])

        convert = st.button(MESSAGES[current_language]["aiWriter"], key=f"convert_{index}")
        text = ''
        if convert:
            if current_images:
                text = AI().analyze_image(
                    [Image.open(i) for i in current_images],
                    prompt=MESSAGES[current_language]["aiWriter"].format(question=question)
                )
            else:
                text = AI().get_response(
                    question,
                    MESSAGES[current_language]["aiWriter"]
                )
            info.update({"Description": {'text': text, 'image': current_images}})

        final_description = st.text_area(
            MESSAGES[current_language]["finalDescriptionLabel"],
            key=f"final_description_{index}",
            placeholder=MESSAGES[current_language]["finalDescription"]
        )
        st.session_state['final_description'] = final_description
        search = st.button(MESSAGES[current_language]["searchButton"], key=f"search_{index}")
        st.session_state.search_button = search
        answer = st.text_area(
            MESSAGES[current_language]["engineerSuggestionLabel"],
            key=f"answer_{index}",
            placeholder=MESSAGES[current_language]["engineerSuggestion"]
        )

        attachments = st.file_uploader(
            MESSAGES[current_language]["attachmentLabel"],
            type=["jpg", "jpeg", "png"],
            key=f"attachments_{index}",
            accept_multiple_files=True
        )

        # Update info with form inputs
        info.update({
            "Description": {"text": question, "image": current_images},
            "Factory Suggestion": {"text": answer, "image": attachments if attachments else []}
        })

    if save_button:
        if index is None:
            info["No"] = len(st.session_state.questions) + 1
            st.session_state.questions.append(info)
            st.session_state.cEQ = {'index': len(st.session_state.questions) - 1, 'question': info}
        elif validate_index(index, st.session_state.questions):
            st.session_state.questions[index] = info
        else:
            st.error(MESSAGES[current_language]["invalidIndexError"] if "invalidIndexError" in MESSAGES[current_language] else "Invalid question index")
        st.rerun()

    if delete_button:
        if validate_index(index, st.session_state.questions):
            del st.session_state.questions[index]
            st.session_state.cEQ = {'index': None, 'question': empty_eq_card_temp}
            st.rerun()
        else:
            st.error(MESSAGES[current_language]["cannotDeleteError"] if "cannotDeleteError" in MESSAGES[current_language] else "Cannot delete question")

def render_EQ_list(eqlist):
    st.subheader(MESSAGES[current_language]["eqList"])
    if not eqlist:
        st.write(MESSAGES[current_language]["noQuestionsError"])
        return
    for eq in range(len(eqlist)):
        q = eqlist[eq]
        if st.button(f"{MESSAGES[current_language]['questionLabel']} {eq + 1}", key=f"Question Button {eq}"):
            st.session_state.cEQ = {'index': eq, 'question': q}
            st.rerun()

# EQ Information Card
with st.container(border=True):
    st.subheader(MESSAGES[current_language]["eqInformationHeader"])
    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input(
            MESSAGES[current_language]["customerName"],
            value=st.session_state.current_eq.get("Customer Name", "") if st.session_state.current_eq else "",
            placeholder=MESSAGES[current_language]["customerNamePlaceholder"]
        )
        stg_pn = st.text_input(
            MESSAGES[current_language]["stgPN"],
            value=st.session_state.current_eq.get("STG P/N", "") if st.session_state.current_eq else "",
            placeholder=MESSAGES[current_language]["stgPNPlaceholder"]
        )
        factory_engineer = st.text_input(
            MESSAGES[current_language]["factoryEngineer"],
            value=st.session_state.current_eq.get("Engineer Name", "") if st.session_state.current_eq else "",
            placeholder=MESSAGES[current_language]["factoryEngineerPlaceholder"]
        )
        via_plugging_type = st.text_input(
            MESSAGES[current_language]["viaPluggingType"],
            value=st.session_state.current_eq.get("Via Plugging Type", "") if st.session_state.current_eq else "",
            placeholder=MESSAGES[current_language]["viaPluggingTypePlaceholder"]
        )
        base_material = st.text_input(
            MESSAGES[current_language]["baseMaterialColumn"],
            value=st.session_state.current_eq.get("Base Material", "") if st.session_state.current_eq else "",
            placeholder=MESSAGES[current_language]["baseMaterialPlaceholder"]
        )

    with col2:
        customer_pn = st.text_input(
            MESSAGES[current_language]["customerPNColumn"],
            value=st.session_state.current_eq.get("Customer P/N", "") if st.session_state.current_eq else "",
            placeholder=MESSAGES[current_language]["customerPNPlaceholder"]
        )
        factory_pn = st.text_input(
            MESSAGES[current_language]["factoryPNColumn"],
            value=st.session_state.current_eq.get("Factory P/N", "") if st.session_state.current_eq else "",
            placeholder=MESSAGES[current_language]["factoryPNPlaceholder"]
        )
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, DATE_FORMAT).date()
            except ValueError:
                try:
                    date_str = date_str.replace(".", "-")
                    return datetime.strptime(date_str, DATE_FORMAT).date()
                except ValueError:
                    return datetime.today().date()

        issue_date = st.date_input(
            MESSAGES[current_language]["issueDate"],
            value=parse_date(st.session_state.current_eq.get("issue_date", datetime.today().strftime(DATE_FORMAT))) if st.session_state.current_eq and st.session_state.current_eq.get("issue_date") else datetime.today()
        )
        panel_size = st.text_input(
            MESSAGES[current_language]["panelSize"],
            value=st.session_state.current_eq.get("Panel Size", "") if st.session_state.current_eq else "",
            placeholder=MESSAGES[current_language]["panelSizePlaceholder"]
        )
        solder_mask = st.text_input(
            MESSAGES[current_language]["solderMaskColumn"],
            value=st.session_state.current_eq.get("Solder Mask", "") if st.session_state.current_eq else "",
            placeholder=MESSAGES[current_language]["solderMaskPlaceholder"]
        )

    status = st.session_state.current_eq.get("status", MESSAGES[current_language]["reviewingStatus"]) if st.session_state.current_eq else MESSAGES[current_language]["reviewingStatus"]
    status = st.selectbox(
        MESSAGES[current_language]["allStatus"],
        [
            MESSAGES[current_language]["reviewingStatus"],
            MESSAGES[current_language]["pendingStatus"],
            MESSAGES[current_language]["closedStatus"]
        ],
        index=[
            MESSAGES[current_language]["reviewingStatus"],
            MESSAGES[current_language]["pendingStatus"],
            MESSAGES[current_language]["closedStatus"]
        ].index(status)
    )

col0, col1 = st.columns([8, 2])
ques_container = col0.container(border=True, key="question_part", height=850)
list_container = col1.container(border=True, key="EQList", height=850)

with ques_container:
    if st.session_state.cEQ:
        render_question_form(st.session_state.cEQ['question'], st.session_state.cEQ['index'])

with list_container:
    with st.container(border=False, height=700):
        render_EQ_list(st.session_state.questions)
    with st.container(border=False, height=100):
        if st.button(MESSAGES[current_language]["addEQ"]):
            new_eq = empty_eq_card_temp.copy()
            st.session_state.cEQ = {'index': None, 'question': new_eq}
            st.rerun()

        if st.button(MESSAGES[current_language]["exportExcel"]):
            if not all([customer_name, customer_pn, stg_pn, factory_pn, factory_engineer, via_plugging_type, panel_size, base_material, solder_mask]):
                st.error(MESSAGES[current_language]["missingFieldsError"])
            elif not st.session_state.questions:
                st.error(MESSAGES[current_language]["noQuestionsError"])
            else:
                with st.spinner(MESSAGES[current_language]["exportingAndSending"]):
                    if status == MESSAGES[current_language]["reviewingStatus"]:
                        st.session_state.current_eq = {
                            "id": f"EQ-{datetime.today().year}-{len(st.session_state.get('eq_list', [])) + 1:03d}",
                            "customer_name": customer_name,
                            "customer_pn": customer_pn,
                            "stg_pn": stg_pn,
                            "factory_pn": factory_pn,
                            "factory_engineer": factory_engineer,
                            "issue_date": issue_date.strftime(DATE_FORMAT),
                            "created_date": datetime.today().strftime(DATE_FORMAT),
                            "status": MESSAGES[current_language]["pendingStatus"],
                            "questions": st.session_state.questions,
                            "via_plugging_type": via_plugging_type,
                            "panel_size": panel_size,
                            "base_material": base_material,
                            "solder_mask": solder_mask
                        }
                        st.session_state.setdefault("eq_list", []).append(st.session_state.current_eq)
                        st.session_state.questions = []
                        st.success(MESSAGES[current_language]["exportReviewingSuccess"])
                    elif status == MESSAGES[current_language]["pendingStatus"]:
                        st.success(MESSAGES[current_language]["exportPendingSuccess"])
                    elif status == MESSAGES[current_language]["closedStatus"]:
                        st.success(MESSAGES[current_language]["exportClosedSuccess"])

# Search results
if st.session_state.search_button:
    if st.session_state.final_description and st.session_state.current_eq.get('Customer Name'):
        search_container = st.container(border=True, key="Searching", height=850)
        with search_container:
            searching(st.session_state['final_description'], st.session_state.current_eq.get('Customer Name'))
    else:
        st.error(MESSAGES[current_language]["missingSearchDataError"] if "missingSearchDataError" in MESSAGES[current_language] else "Missing search data")
