import streamlit as st
import plotly.graph_objects as go
import datetime
from utils import load_from_dataset
from config import source_path, MESSAGES

# Initialize session_state
if 'navigate_to' not in st.session_state:
    st.session_state.navigate_to = None
if 'filter_days' not in st.session_state:
    st.session_state.filter_days = None
if "data" not in st.session_state:
    st.session_state.data = load_from_dataset(input_excel=source_path['database'])
if 'language' not in st.session_state:
    st.session_state.language = 'en'  # Default to English

# Language selection
current_language = st.session_state.language
if current_language != st.session_state.language:
    st.session_state.language = current_language
    st.rerun()

# Define navigation to EQ Manage page
def navigate_to_eq_manage(days_filter):
    st.session_state.navigate_to = "eq_manage"
    st.session_state.filter_days = days_filter
    st.rerun()

def count_status(data):
    reviewing = 0
    pending = 0
    closed = 0
    
    for item in data:
        status = item.get("EQ Status", "")
        if status == "Reviewing":
            reviewing += 1
        elif status == "Pending":
            pending += 1
        elif status == "Closed":
            closed += 1
    
    return {
        "Reviewing": reviewing,
        "Pending": pending,
        "Closed": closed
    }

# Calculate EQ counts by days
def calculate_days(data):
    today = datetime.datetime.now().date()
    
    over_7_days = 0
    between_2_7_days = 0
    under_2_days = 0
    
    for item in data:
        status = item.get("EQ Status", "")
        if status in ["Reviewing", "Pending"]:
            creation_date_str = item.get("Date", "")
            if creation_date_str:
                try:
                    creation_date = datetime.datetime.strptime(creation_date_str, "%Y-%m-%d").date()
                    days_diff = (today - creation_date).days
                    
                    if days_diff > 7:
                        over_7_days += 1
                    elif 2 < days_diff <= 7:
                        between_2_7_days += 1
                    elif days_diff <= 2:
                        under_2_days += 1
                except Exception as e:
                    print(f"Date parsing error: {e}, date string: {creation_date_str}")
    
    return over_7_days, between_2_7_days, under_2_days

# Calculate status and time
status_counts = count_status(st.session_state.data)
over_7_days, between_2_7_days, under_2_days = calculate_days(st.session_state.data)

# Use container for layout
container = st.container()

# Create two-column layout
with container:
    col1, col2 = st.columns([1, 1])
    
    # Left: Donut chart
    with col1:
        st.subheader(MESSAGES[current_language]["eqOverview"])
        
        fig = go.Figure(data=[
            go.Pie(
                labels=list(status_counts.keys()),
                values=list(status_counts.values()),
                hole=0.75,
                marker_colors=["#fb923c", "#10b981", "#1e3a8a"],
                textinfo="label+value",
                hoverinfo="label+percent+value"
            )
        ])

        fig.update_layout(
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            margin=dict(t=0, b=30, l=0, r=0),
            height=500,
            autosize=True
        )

        st.plotly_chart(fig, use_container_width=True)
    
    # Right: Time-based cards
    with col2:
        st.subheader(MESSAGES[current_language]["unresolvedEQs"])
        
        st.markdown(
            f"<div style='font-size: 1rem; color: #666; margin-bottom: 12px; text-align: left;'>"
            f"{MESSAGES[current_language]['unresolvedDescription']}"
            f"</div>",
            unsafe_allow_html=True
        )
        
        # Over 7 days card
        with st.container():
            st.markdown(
                f"<div style='background-color:#fee2e2; padding:10px; border-radius:5px;text-align:center'>"
                f"<h3 style='color:#b91c1c; font-size:1.5rem; margin:0;text-align:center'>{MESSAGES[current_language]['over7Days']}</h3>"
                f"<p style='color:#b91c1c; font-size:2rem; font-weight:bold; margin:8px 0 0 0;text-align:center'>{over_7_days} EQs</p>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.button(MESSAGES[current_language]["viewDetails"], key="over_7_days_btn", on_click=navigate_to_eq_manage, args=("over7",), use_container_width=True)
        
        # 2-7 days card
        with st.container():
            st.markdown(
                f"<div style='background-color:#fef3c7; padding:10px; border-radius:5px;text-align:center;'>"
                f"<h3 style='color:#b45309; font-size:1.5rem; margin:0; text-align:center'>{MESSAGES[current_language]['between2to7Days']}</h3>"
                f"<p style='color:#b45309; font-size:2rem; font-weight:bold; margin:8px 0 0 0;text-align:center'>{between_2_7_days} EQs</p>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.button(MESSAGES[current_language]["viewDetails"], key="between_2_7_days_btn", on_click=navigate_to_eq_manage, args=("between2_7",), use_container_width=True)
        
        # Under 2 days card
        with st.container():
            st.markdown(
                f"<div style='background-color:#d1fae5; padding:10px; border-radius:5px;text-align:center'>"
                f"<h3 style='color:#047857; font-size:1.5rem; margin:0;text-align:center'>{MESSAGES[current_language]['under2Days']}</h3>"
                f"<p style='color:#047857; font-size:2rem; font-weight:bold; margin:8px 0 0 0;text-align:center'>{under_2_days} EQs</p>"
                f"</div>",
                unsafe_allow_html=True
            )
            st.button(MESSAGES[current_language]["viewDetails"], key="under_2_days_btn", on_click=navigate_to_eq_manage, args=("under2",), use_container_width=True)

# Handle navigation logic
if st.session_state.navigate_to == "eq_manage":
    days_filter = st.session_state.filter_days
    st.session_state.navigate_to = None  # Reset navigation state
    
    # Map filter values to translated labels
    filter_labels = {
        "over7": MESSAGES[current_language]["filterOver7"],
        "between2_7": MESSAGES[current_language]["filterBetween2to7"],
        "under2": MESSAGES[current_language]["filterUnder2"]
    }
    filter_label = filter_labels.get(days_filter, days_filter)
    
    st.success(MESSAGES[current_language]["navigateToEQManage"].format(filter=filter_label))

# st.write(st.session_state.data)