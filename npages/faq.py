import streamlit as st
from collections import Counter
from models import FAQ
from config import STATUS_ICONS, MESSAGES, APP_CONFIG, source_path
from utils import initial_page_config, initialize_session_state
from datetime import datetime
import os

# 初始化页面
# initial_page_config("faq")

# 获取当前语言
lang = st.session_state.get("language", "zh-CN")

# 缓存示例数据
@st.cache_data
def load_faqs():
    l = []
    try:
        for i in st.session_state.get('data', []):
            # 验证图片路径
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
                date=i.get('Date', '2025-01-01'),  # 统一格式为 %Y-%m-%d
                customer=i['Customer Name'],
                status=i["EQ Status"],
                stg=i.get('STG P/N', 'Unknown'),
                image=q_images,
                answer=customer_decision.get('text', 'No decision yet'),
                answer_image=a_images,
                engineer=i.get('Engineer Name', 'Unknown'),
                closedate=i.get('Closed Date', '2025-01-01')  # 统一格式为 %Y-%m-%d
            ))
        return l
    except Exception as e:
        st.error(f"加载 FAQ 数据失败: {str(e)}")
        return []

faqs = load_faqs()

# 初始化 session state
initialize_session_state({
    "selected_customer": "All Customers",
    "current_page": 1,  # 当前页码
    "items_per_page": 10  # 默认每页 10 条
})

# 两列布局
col1, col2 = st.columns([1, 3])

# 左侧列：客户筛选
with col1:
    st.subheader("按客户筛选")
    customer_counts = Counter([faq.customer for faq in faqs])
    top_customers = customer_counts.most_common(15)
    unique_customers = list(set([faq.customer for faq in faqs]))

    selected_customer = st.selectbox(
        "选择客户",
        ["All Customers"] + unique_customers,
        index=0 if st.session_state.selected_customer == "All Customers" else unique_customers.index(st.session_state.selected_customer) + 1,
        key="customer_select"
    )

    if selected_customer != st.session_state.selected_customer:
        st.session_state.selected_customer = selected_customer
        st.session_state.current_page = 1  # 重置到第一页
        st.rerun()

    for customer, count in top_customers:
        if st.button(f"{customer} ({count})", key=f"btn_{customer}"):
            st.session_state.selected_customer = customer
            st.session_state.current_page = 1  # 重置到第一页
            st.rerun()

# 右侧列：FAQ 内容
with col2:
    title = MESSAGES[lang].get("faq_title", APP_CONFIG["pages"]["faq"]["title"])
    st.subheader(title)

    # 过滤栏
    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns([2, 2, 2, 2, 2])
    with filter_col1:
        keyword = st.text_input("关键词", key="keyword")
    with filter_col2:
        start_date = st.date_input("开始日期", value=None, key="start_date")
    with filter_col3:
        end_date = st.date_input("结束日期", value=None, key="end_date")
    with filter_col4:
        status = st.selectbox("状态", ["All Statuses", "Closed", "Pending", "Reviewing"], key="status")
    with filter_col5:
        stg_pn = st.text_input("STG P/N", key="stg_pn")

    # 分页设置
    items_per_page = st.selectbox(
        "每页显示条数",
        [10, 20, 50],
        index=[10, 20, 50].index(st.session_state.items_per_page),
        key="items_per_page_select"
    )
    if items_per_page != st.session_state.items_per_page:
        st.session_state.items_per_page = items_per_page
        st.session_state.current_page = 1  # 重置到第一页
        st.rerun()

    # 筛选 FAQ
    filtered_faqs = faqs
    if st.session_state.selected_customer != "All Customers":
        filtered_faqs = [faq for faq in filtered_faqs if faq.customer == st.session_state.selected_customer]
    if keyword:
        filtered_faqs = [faq for faq in filtered_faqs if keyword.lower() in faq.question.lower()]
    if start_date:
        filtered_faqs = [faq for faq in filtered_faqs if datetime.strptime(faq.date, "%Y-%m-%d").date() >= start_date]
    if end_date:
        filtered_faqs = [faq for faq in filtered_faqs if datetime.strptime(faq.closedate, "%Y-%m-%d").date() <= end_date]
    if status != "All Statuses":
        filtered_faqs = [faq for faq in filtered_faqs if faq.status == status]
    if stg_pn:
        filtered_faqs = [faq for faq in filtered_faqs if stg_pn.lower() in faq.stg.lower()]

    # 分页逻辑
    total_items = len(filtered_faqs)
    total_pages = max(1, (total_items + st.session_state.items_per_page - 1) // st.session_state.items_per_page)
    current_page = st.session_state.current_page

    # 确保当前页码有效
    if current_page < 1:
        current_page = 1
    elif current_page > total_pages:
        current_page = total_pages
    st.session_state.current_page = current_page

    start_idx = (current_page - 1) * st.session_state.items_per_page
    end_idx = min(start_idx + st.session_state.items_per_page, total_items)
    paginated_faqs = filtered_faqs[start_idx:end_idx]

    # 延迟加载 FAQ 内容
    with st.container():
        if paginated_faqs:
            for idx, faq in enumerate(paginated_faqs):
                with st.expander(f"{faq.question}"):
                    with st.container(border=True):
                        # 问题卡
                        col0, col1, col2 = st.columns([1, 1, 1])
                        col0.write("时间: " + str(faq.date))
                        col0.write('客户: ' + str(faq.customer))
                        col1.write('状态: ' + str(faq.status))
                        col1.write('STG P/N : ' + str(faq.stg))
                        col2.write('engineer: ' + str(faq.engineer))
                        col0, col1 = st.columns([2, 1])
                        with col0:
                            if faq.image:
                                if isinstance(faq.image, list):
                                    for img in faq.image:
                                        st.image(img)
                                else:
                                    st.image(faq.image)

                    with st.container(border=True):
                        # 答案卡
                        st.write('客户回复: ' + str(faq.answer))
                        col0, col1 = st.columns([2, 1])
                        with col0:
                            if faq.answer_image:
                                if isinstance(faq.answer_image, list):
                                    for img in faq.answer_image:
                                        st.image(img)
                                else:
                                    st.image(faq.answer_image)

        else:
            st.write(MESSAGES[lang]["noDataFound"])

    # 分页导航
    if total_pages > 1:
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.button("上一页", disabled=(current_page == 1)):
                st.session_state.current_page -= 1
                st.rerun()
        with col_info:
            st.write(f"第 {current_page} 页 / 共 {total_pages} 页 (总计 {total_items} 条)")
        with col_next:
            if st.button("下一页", disabled=(current_page == total_pages)):
                st.session_state.current_page += 1
                st.rerun()