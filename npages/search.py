import streamlit as st
import pandas as pd
from models import EQ
from config import MESSAGES, DATE_FORMAT
from utils import initial_page_config, filter_dataframe
from components import render_data_table, render_filter_controls
from message import SEARCH_MESSAGES

# 获取当前语言
lang = st.session_state.get("language", "zh-CN")
T = SEARCH_MESSAGES[lang]

# 初始化页面
#initial_page_config("eq_search")

# 缓存示例数据
@st.cache_data
def load_eqs():
    return [
        EQ(id="057539", eqStatus="1. EQ to customer", prodData="For approval", paste="Required", last="days(5)", changed="2025-01-09", pn="QEN1007583-A00", techClass="Standard", spe="Sensodec SA", customer="Sensodec SA", endCustomer="NA–Not available", customerPN="527.1P1018", project="BH 4.5 Screw Compressor", factory="JST", selected=False, image="images/starteam-logo.png"),
        EQ(id="076263", eqStatus="1. EQ to customer", prodData="For record list",paste="", last="70", changed="2025-02-09", pn="QEN1002549-A03", techClass="Standard", spe="", customer="Clipped SA", endCustomer="NA–Not available", customerPN="1000C80200-1", project="BH 4.5 Screw Compressor", factory="JST", selected=False, image="images/starteam-logo.png"),
        EQ(id="076264", eqStatus="2. EQ confirmed", prodData="In progress", paste="Required", last="35", changed="2025-03-09", pn="QEN1002550-A01", techClass="Advanced", spe="MechCorp", customer="MechCorp GmbH", endCustomer="BioSolutions Ltd", customerPN="MC-2025-10", project="Medical Imaging System", factory="TYN", selected=False, image="images/starteam-logo.png"),
        EQ(id="076265", eqStatus="3. EQ completed", prodData="Completed", paste="", last="42", changed="2025-04-09", pn="QEN1002551-A02", techClass="Standard", spe="", customer="ElectroPro Inc", endCustomer="Automotive Solutions", customerPN="EP-5422-B", project="Electric Vehicle Controller", factory="GZ", selected=False, image="images/starteam-logo.png"),
        EQ(id="076266", eqStatus="1. EQ to customer", prodData="For approval", paste="Required", last="28", changed="2025-05-09", pn="QEN1002552-A00", techClass="Complex", spe="TechVision", customer="TechVision AG", endCustomer="Smart Home Solutions", customerPN="TV-2025-SH1", project="Smart Home Hub", factory="SZ", selected=False, image="images/starteam-logo.png")
    ]

# 加载数据
eqs = load_eqs()
df = pd.DataFrame([vars(eq) for eq in eqs])

# 🔍 过滤控件
st.subheader(T["searchEQ"])
filters = {}
filters = render_filter_controls(filters, lang=lang)

# 数据过滤
filtered_df = filter_dataframe(df, filters)

# 📊 表格列配置
column_config = {
    "selected": st.column_config.CheckboxColumn(T["select"], default=False),
    "image": st.column_config.ImageColumn(label=MESSAGES[lang]["image"], width="medium"),
    "id": st.column_config.TextColumn("ID"),
    "eqStatus": st.column_config.TextColumn(T["eqStatus"]),
    "prodData": st.column_config.TextColumn(T["prodData"]),
    "paste": st.column_config.TextColumn("Paste"),
    "last": st.column_config.TextColumn(T["duration"]),
    "changed": st.column_config.TextColumn(T["changeDate"]),
    "pn": st.column_config.TextColumn("P/N"),
    "techClass": st.column_config.TextColumn(T["techClass"]),
    "spe": st.column_config.TextColumn("SPE"),
    "customer": st.column_config.TextColumn(T["customer"]),
    "endCustomer": st.column_config.TextColumn(T["endCustomer"]),
    "customerPN": st.column_config.TextColumn(T["customerPN"]),
    "project": st.column_config.TextColumn(T["project"]),
    "factory": st.column_config.TextColumn(T["factory"])
}

# 🧾 渲染表格（无按钮）
edited_df = render_data_table(filtered_df, column_config, lang=lang, table_key="eq_table", show_buttons=False)

# 🔙 返回按钮
if st.button(T["backToDashboard"]):
    st.switch_page("pages/main_new.py")
    