import streamlit as st
from collections import Counter
from models import FAQ
from config import MESSAGES, APP_CONFIG, source_path
from utils import initialize_session_state
from datetime import datetime
import os

# Initialize page
# initial_page_config("faq")

# Get current language

current_language = st.session_state.language
if current_language != st.session_state.language:
    st.session_state.language = current_language
    st.rerun()

# Cache FAQ data
@st.cache_data
def load_faqs():
    l = []
    try:
        for i in st.session_state.get('data', []):
            # Verify image paths
            q_images = [
                os.path.join(source_path['images'], image)
                for image in i['Description'].get('image', [])
                if os.path.exists(os.path.join(source_path['images'], image))
            ]
            customer_decision = i.get('Customer Decision', {'text': 'No decision yet', 'image': []})
            a_images = [
                os.path.join(source_path['images'], image)
                for image in customer_decision.get('image', [])
                if os.path.exists(os.path.join(source_path['images'], image))
            ]
            l.append(FAQ(
                similarity=100,
                question=i['Description']['text'],
                date=i.get('Date', '2025-01-01'),
                customer=i['Customer Name'],
                status=i["EQ Status"],
                stg=i.get('STG P/N', 'Unknown'),
                image=q_images,
                answer=customer_decision.get('text', 'No decision yet'),
                answer_image=a_images,
                engineer=i.get('Engineer Name', 'Unknown'),
                closedate=i.get('Closed Date', '2025-01-01')
            ))
        return l
    except Exception as e:
        st.error(MESSAGES[current_language]["loadFaqError"].format(error=str(e)))
        return []

faqs = load_faqs()

# Initialize session state
initialize_session_state({
    "selected_customer": MESSAGES[current_language]["allCustomers"],
    "current_page": 1,
    "items_per_page": 10
})
if 'allCustomers' not in st.session_state:
    st.session_state.allCustomers = MESSAGES[current_language]["allCustomers"]
# Two-column layout
col1, col2 = st.columns([1, 3])

# Left column: Customer filter
with col1:
    st.subheader(MESSAGES[current_language]["filterByCustomer"])
    customer_counts = Counter([faq.customer for faq in faqs])
    top_customers = customer_counts.most_common(15)
    unique_customers = list(set([faq.customer for faq in faqs]))

    # Calculate the index for selectbox
    default_index = 0  # Default to "All Customers"
    if st.session_state.selected_customer != MESSAGES[current_language]["allCustomers"]:
        try:
            default_index = unique_customers.index(st.session_state.selected_customer) + 1
        except ValueError:
            # If selected_customer is not in unique_customers, keep default_index as 0
            st.session_state.selected_customer = MESSAGES[current_language]["allCustomers"]

    selected_customer = st.selectbox(
        MESSAGES[current_language]["selectCustomer"],
        [MESSAGES[current_language]["allCustomers"]] + unique_customers,
        index=default_index,
        key="customer_select"
    )

    if selected_customer != st.session_state.selected_customer:
        st.session_state.selected_customer = selected_customer
        st.session_state.current_page = 1
        st.rerun()
    
    for customer, count in top_customers:
        if st.button(f"{customer} ({count})", key=f"btn_{customer}"):
            st.session_state.selected_customer = customer
            st.session_state.current_page = 1  # 重置到第一页
            st.rerun()


# Right column: FAQ content
with col2:
    title = MESSAGES[current_language].get("faq_title", APP_CONFIG["pages"]["faq"]["title"])
    st.subheader(title)

    # Filter bar
    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([2, 2, 2, 2, 2])
    with filter_col1:
        keyword = st.text_input(MESSAGES[current_language]["keyword"], key="keyword")
    with filter_col2:
        start_date = st.date_input(MESSAGES[current_language]["startDate"], value=None, key="start_date")
    with filter_col3:
        end_date = st.date_input(MESSAGES[current_language]["endDate"], value=None, key="end_date")
    with filter_col4:
        status = st.selectbox(
            MESSAGES[current_language]["status"],
            [MESSAGES[current_language]["allStatuses"], "Closed", "Pending", "Reviewing"],
            key="status"
        )
    with filter_col5:
        stg_pn = st.text_input(MESSAGES[current_language]["stgPN"], key="stg_pn")

    # Pagination settings
    items_per_page = st.selectbox(
        MESSAGES[current_language]["itemsPerPage"],
        [10, 20, 50],
        index=[10, 20, 50].index(st.session_state.items_per_page),
        key="items_per_page_select"
    )
    if items_per_page != st.session_state.items_per_page:
        st.session_state.items_per_page = items_per_page
        st.session_state.current_page = 1
        st.rerun()

    # Filter FAQs
    filtered_faqs = faqs
    if st.session_state.selected_customer != MESSAGES[current_language]["allCustomers"]:
        filtered_faqs = [faq for faq in filtered_faqs if faq.customer == st.session_state.selected_customer]
    if keyword:
        filtered_faqs = [faq for faq in filtered_faqs if keyword.lower() in faq.question.lower()]
    if start_date:
        filtered_faqs = [faq for faq in filtered_faqs if datetime.strptime(faq.date, "%Y-%m-%d").date() >= start_date]
    if end_date:
        filtered_faqs = [faq for faq in filtered_faqs if datetime.strptime(faq.closedate, "%Y-%m-%d").date() <= end_date]
    if status != MESSAGES[current_language]["allStatuses"]:
        filtered_faqs = [faq for faq in filtered_faqs if faq.status == status]
    if stg_pn:
        filtered_faqs = [faq for faq in filtered_faqs if stg_pn.lower() in faq.stg.lower()]

    # Pagination logic
    total_items = len(filtered_faqs)
    total_pages = max(1, (total_items + st.session_state.items_per_page - 1) // st.session_state.items_per_page)
    current_page = st.session_state.current_page

    # Ensure valid page number
    if current_page < 1:
        current_page = 1
    elif current_page > total_pages:
        current_page = total_pages
    st.session_state.current_page = current_page

    start_idx = (current_page - 1) * st.session_state.items_per_page
    end_idx = min(start_idx + st.session_state.items_per_page, total_items)
    paginated_faqs = filtered_faqs[start_idx:end_idx]

    # Display FAQs
    with st.container():
        if paginated_faqs:
            for idx, faq in enumerate(paginated_faqs):
                with st.expander(f"{faq.question}"):
                    with st.container(border=True):
                        # Question card
                        col0, col1, col2 = st.columns([1, 1, 1])
                        col0.write(MESSAGES[current_language]["faqTime"] + str(faq.date))
                        col0.write(MESSAGES[current_language]["faqCustomer"] + str(faq.customer))
                        col1.write(MESSAGES[current_language]["faqStatus"] + str(faq.status))
                        col1.write(MESSAGES[current_language]["faqStgPN"] + str(faq.stg))
                        col2.write(MESSAGES[current_language]["faqEngineer"] + str(faq.engineer))
                        col0, col1 = st.columns([2, 1])
                        with col0:
                            if faq.image:
                                if isinstance(faq.image, list):
                                    for img in faq.image:
                                        st.image(img)
                                else:
                                    st.image(faq.image)

                    with st.container(border=True):
                        # Answer card
                        st.write(MESSAGES[current_language]["faqCustomerReply"] + str(faq.answer))
                        col0, col1 = st.columns([2, 1])
                        with col0:
                            if faq.answer_image:
                                if isinstance(faq.answer_image, list):
                                    for img in faq.answer_image:
                                        st.image(img)
                                else:
                                    st.image(faq.answer_image)

        else:
            st.write(MESSAGES[current_language]["noDataFound"])

    # Pagination navigation
    if total_pages > 1:
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button(MESSAGES[current_language]["previousPage"], disabled=(current_page == 1)):
                st.session_state.current_page -= 1
                st.rerun()
        with col_info:
            st.write(MESSAGES[current_language]["pageInfo"].format(
                current_page=current_page,
                total_pages=total_pages,
                total_items=total_items
            ))
        with col_next:
            if st.button(MESSAGES[current_language]["nextPage"], disabled=(current_page == total_pages)):
                st.session_state.current_page += 1
                st.rerun()