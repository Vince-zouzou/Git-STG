# create.py
import streamlit as st
from datetime import datetime
from utils import initialize_session_state,render_QA_card
from config import DATE_FORMAT
import pytesseract
from PIL import Image
from ustai import AI
from EC import Engine
from config import source_path
import os
# 初始化 session state
initialize_session_state({
    "current_eq": None,
    "questions": [],
    "filepath": None  # 新增 filepath
})

# 如果有 current_eq 数据，加载到页面
if st.session_state.current_eq:
    current_eq = st.session_state.current_eq
else:
    current_eq = {}
if 'engine' not in st.session_state:
    st.session_state["engine"] = Engine(vectorstore_path="Data/Model", output_excel="Data/Dataset.csv", output_images_dir="Data/images")

# Placeholder 字典，定义所有输入字段的提示文本
PLACEHOLDERS = {
    "customer_name": "请输入客户名称，例如：ABC Company",
    "stg_pn": "请输入 STG 零件号，例如：STG12345",
    "factory_engineer": "请输入工厂工程师姓名，例如：张伟",
    "base_material": "请输入基材类型，例如：FR4",
    "customer_pn": "请输入客户零件号，例如：CUST67890",
    "factory_pn": "请输入工厂零件号，例如：FACT45678",
    "panel_size": "请输入交货板尺寸，例如：500*600 mm",
    "solder_mask": "请输入阻焊层信息，例如：绿色光泽",
    "question": "请输入问题描述，例如：关于阻焊层厚度的要求",
    "final_description": "请输入最终描述，例如：需要确保厚度符合标准",
    "answer": "请输入工程师建议，例如：建议调整工艺参数",
    "attachments": "请上传附件（支持多个 JPG/PNG 文件）"
}

def searching(final_description,customer_name):
    with st.spinner("正在搜索..."):
        similar_issues = st.session_state.engine.search_similar_descriptions(final_description,customer_name=customer_name,k=10)
        searching_result_card(similar_issues)

def searching_result_card(issues):

    for i,issue in enumerate(issues):
        qa_data = {
        "date": issue.get("Date"),
        "customer": issue.get("Customer Name"),
        "status": issue.get("Status"),
        "stg": issue.get("STG P/N"),
        "engineer": issue.get("Engineer"),
        "image": issue.get("Description", {'text':'No Description','image':[]})['image'],
        "answer": issue.get('Customer Decision',{'text':'No Description','image':[]})['text'],
        "answer_image": issue.get('Customer Decision',{'text':'No Description','image':[]})['image'],
        'question':issue.get("Description", {'text':'No Description','image':[]})['text'],
        'similarity':issue.get("similarity_score")}
        #with st.expander(f"{issue.get('question', '未知')}"+"-----"+f"相似度{issue.get('similarity')}"):
            # 问题卡

        render_QA_card(qa_data)
        
# 函数：渲染 Question 编辑界面
def render_question_form(info,index):
    with st.expander(f'问题 {index+1}', expanded=True):
        if info:
            question = st.text_area("问题描述", 
                                value=info.get("Description", {'text':'No Description','image':[]})['text'], 
                                key=f"question_{index}", 
                                placeholder=PLACEHOLDERS["question"])
            
            # 处理图片显示
            current_images = info.get("Description", {'text':'No Description','image':[]})['image']
            image = st.file_uploader("上传相关图片 (请注意Gerber File不可使用)", 
                                type=["jpg", "jpeg", "png"], 
                                key=f"image_{index}")
            if image:
                current_images = [image]  # 新上传的图片替换现有图片
            for img in current_images:
                if img:  # 确保img不是None
                    #st.write(img)
                    st.image(os.path.join(source_path['images'],img), caption="已上传图片")
            convert = st.button("转换", key=f"convert_{index}")
            text = ''
            if convert:
                #text = pytesseract.image_to_string(Image.open(current_images[0]))
                if len(current_images) != 0:
                    text = AI().analyze_image([Image.open(i) for i in current_images],prompt="这个图片大概率是一个和PCB零部件制造相关的内容,结合这段针对这个图片提出的问题:{},用标准英文描述这张图片的内容。你输出的text是用来进行语义搜索的,请你按照这个要求输出最适合用来语义搜索的格式的内容".format(question))
                else:
                    text = AI().get_response(question,"你输出的text是用来进行语义搜索的,请你按照这个要求输出最适合用来语义搜索的格式的内容")
                info.update({"Description": {'text':text,'image':current_images}})
                #st.write(info)
            # 其他字段
            final_description = st.text_area("最终描述", 
                                        value=info.get("Description", {'text':'No Description','image':[]})['text'],
                                        key=f"final_description_{index}", 
                                        placeholder=PLACEHOLDERS["final_description"])
            
            search = st.button("搜索", key=f"search_{index}")
            if search:
                searching(final_description,st.session_state.current_eq.get('Customer Name'))
                
            answer = st.text_input("工程师建议", 
                                value=info.get("Factory Suggestion", {'text':'No Description','image':[]})['text'],
                                key=f"answer_{index}", 
                                placeholder=PLACEHOLDERS["answer"])
            
            attachments = st.file_uploader("附件", 
                                        type=["jpg", "jpeg", "png"], 
                                        key=f"attachments_{index}", 
                                        accept_multiple_files=True)
            
            # 操作按钮
            col0, col1 = st.columns(2)
            if col0.button("保存", key=f"save_{index}"):
                st.success(f"问题 {index+1} 已保存！")
                
            if col1.button("删除", key=f"delete_{index}"):
                if 0 <= index < len(st.session_state.questions):
                    st.session_state.questions.pop(index)
                    st.rerun()


# EQ Information Card
with st.container(border=True):
    st.subheader("EQ 信息")
    col1, col2 = st.columns(2)

    with col1:
        customer_name = st.text_input("客户名称", value=st.session_state.current_eq.get("Customer Name", "") if st.session_state.current_eq else "", placeholder=PLACEHOLDERS["customer_name"])
        stg_pn = st.text_input("STG P/N", value=st.session_state.current_eq.get("STG P/N", "") if st.session_state.current_eq else "", placeholder=PLACEHOLDERS["stg_pn"])
        factory_engineer = st.text_input("工厂工程师", value=st.session_state.current_eq.get("Engineer Name", "") if st.session_state.current_eq else "", placeholder=PLACEHOLDERS["factory_engineer"])
        via_plugging_type = st.text_input("塞孔类型",value=st.session_state.current_eq.get("Via Plugging Type", "") if st.session_state.current_eq else "",placeholder="VIA Plugging Type")
        base_material = st.text_input("基材", value=st.session_state.current_eq.get("Base Material", "") if st.session_state.current_eq else "", placeholder=PLACEHOLDERS["base_material"])

    with col2:
        customer_pn = st.text_input("客户 P/N", value=st.session_state.current_eq.get("Customer P/N", "") if st.session_state.current_eq else "", placeholder=PLACEHOLDERS["customer_pn"])
        factory_pn = st.text_input("工厂 P/N", value=st.session_state.current_eq.get("Factory P/N", "") if st.session_state.current_eq else "", placeholder=PLACEHOLDERS["factory_pn"])
        def parse_date(date_str):
            try:
                # 尝试标准格式
                return datetime.strptime(date_str, DATE_FORMAT).date()
            except ValueError:
                try:
                    # 尝试处理点分隔符格式
                    date_str = date_str.replace(".", "-")
                    return datetime.strptime(date_str, DATE_FORMAT).date()
                except ValueError:
                    # 如果都失败，返回当天日期
                    return datetime.today().date()

        issue_date = st.date_input(
            "日期",
            value=parse_date(st.session_state.current_eq.get("issue_date", datetime.today().strftime(DATE_FORMAT))) if st.session_state.current_eq and st.session_state.current_eq.get("issue_date") else datetime.today()
        )
        panel_size = st.text_input("交货板尺寸 (mm*mm)", value=st.session_state.current_eq.get("Panel Size", "") if st.session_state.current_eq else "", placeholder=PLACEHOLDERS["panel_size"])
        solder_mask = st.text_input("阻焊层", value=st.session_state.current_eq.get("Solder Mask", "") if st.session_state.current_eq else "", placeholder=PLACEHOLDERS["solder_mask"])

    status = st.session_state.current_eq.get("status", "Reviewing") if st.session_state.current_eq else "Reviewing"
    st.selectbox(
        "状态",
        ["Reviewing", "Pending", "Closed"],
        index=["Reviewing", "Pending", "Closed"].index(status),
    )

# Question Part
with st.container(border=True, key="question_part"):
    for i in range(len(st.session_state.questions)):
        render_question_form(st.session_state.questions[i],i)
    if st.button("添加问题"):
        st.session_state.questions.append({"Index":len(st.session_state.data)+1,
                                            "No":len(st.session_state.questions)+1,
                                            "Description":{
                                            "text":PLACEHOLDERS['question'],
                                            "image":[]},
                                            "Factory Suggestion":{
                                            "text":PLACEHOLDERS['answer'],
                                            "image":[]},
                                            "STG Proposal":{
                                            "text":"",
                                            "image":[]},
                                            "EQ Status":"Pending",
                                            "Customer Name":st.session_state.current_eq.get("Customer Name", ""),
                                            "Customer P/N":st.session_state.current_eq.get("Customer P/N", ""),
                                            "Factory P/N":st.session_state.current_eq.get("Factory P/N", ""),
                                            "Base Material":st.session_state.current_eq.get("Base Material", ""),
                                            "Solder Mask":st.session_state.current_eq.get("Solder Mask", ""),
                                            "Via Plugging Type":st.session_state.current_eq.get("Via Plugging Type", ""),
                                            "Engineer Name":st.session_state.current_eq.get("Engineer Name", ""),
                                            "Panel Size":st.session_state.current_eq.get("Panel Size", ""),
                                            "STG P/N":st.session_state.current_eq.get("STG P/N", ""),
                                            "FileName":st.session_state.current_eq.get("FileName", ""),
                                            "Previous Case":False,
                                            "Closed Date":"3000-01-01"})
        st.rerun()

# Export and Send
if st.button("导出并发送"):
    if not all([customer_name, customer_pn, stg_pn, factory_pn, factory_engineer, via_plugging_type, panel_size, base_material, solder_mask]):
        st.error("请填写所有必填字段。")
    elif not st.session_state.questions:
        st.error("请至少添加一个问题。")
    else:
        with st.spinner("正在导出并发送..."):
            if status == "Reviewing":
                st.session_state.current_eq = {
                    "id": f"EQ-{datetime.today().year}-{len(st.session_state.get('eq_list', [])) + 1:03d}",
                    "customer_name": customer_name,
                    "customer_pn": customer_pn,
                    "stg_pn": stg_pn,
                    "factory_pn": factory_pn,
                    "factory_engineer": factory_engineer,
                    "issue_date": issue_date.strftime(DATE_FORMAT),
                    "created_date": datetime.today().strftime(DATE_FORMAT),
                    "status": "Pending",
                    "questions": st.session_state.questions,
                    "via_plugging_type": via_plugging_type,
                    "panel_size": panel_size,
                    "base_material": base_material,
                    "solder_mask": solder_mask
                }
                st.session_state.setdefault("eq_list", []).append(st.session_state.current_eq)
                st.session_state.questions = []
                st.success("EQ 已导出并发送！")
            elif status == "Pending":
                st.success("待处理问题已导出！")
            elif status == "Closed":
                st.success("客户回复已保存！")