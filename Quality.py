import pandas as pd 
import numpy as np
import streamlit as st
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="📈 QA Dynamic Dashboard", layout="wide")
st.title("⚖️ Quality Agents Dynamic Analysis")

# 2. Data Preparation Settings
COLUMNS_TO_KEEP = [
    "Assigned To", "First Name", "Last Name", "Products", "Date of Birth",
    "Pain Level", "MCN", "Team Leader", "Insurance", "Address", "Site",
    "City", "Opener Status", "State.", "Client", "ZIP Code", "Campaign",
    "Last Modified By", "Dialer", "Created Time", "Modified Time",
    "Closer Name", "Type Of Sale", "Closing Status", "Products Closed For",
    "Date of Sale", "Call duration", "Approval Date", "Dr Name",
    "Phone Number", "Fax Number", "City.", "Address.", "Postal Code.",
    "State..", "NPI Number", "Telemed Status", "Work duration",
    "Quality Agent Name", "Validation", "Recording link", "Finish Date",
    "Assign Date", "QA Feedback"
]

@st.cache_data
def process_uploaded_data(uploaded_file):
    df_raw = pd.read_csv(uploaded_file)
    df_cleaned = df_raw[[col for col in COLUMNS_TO_KEEP if col in df_raw.columns]].copy()
    
    # Numeric Cleanup
    df_cleaned["Call duration"] = pd.to_numeric(df_cleaned["Call duration"], errors='coerce').fillna(0)
    df_cleaned["Work duration"] = pd.to_numeric(df_cleaned["Work duration"], errors='coerce').fillna(0)
    df_cleaned["Duration Difference"] = df_cleaned["Call duration"] - df_cleaned["Work duration"]
    
    # Date Processing
    date_cols = ["Created Time", "Modified Time", "Date of Sale", "Finish Date", "Assign Date"]
    for col in date_cols:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_datetime(df_cleaned[col], dayfirst=True, errors='coerce')
            
    return df_raw, df_cleaned

# --- FILE UPLOADER SECTION ---
st.info("👋 Welcome! Please upload your 'O_Plan_Leads.csv' file to start the analysis.")
uploaded_file = st.file_uploader("📤 Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Load and Process the uploaded file
    df_raw, df_processed = process_uploaded_data(uploaded_file)
    total_leads_in_sheet = len(df_raw)
    df_agents_full = df_processed.dropna(subset=["Quality Agent Name"])

    # --- DYNAMIC FILTER PANEL ---
    st.write("### 🛠️ Global Filters")
    all_agents = sorted(df_agents_full["Quality Agent Name"].unique().tolist())
    
    if 'selected_agents' not in st.session_state:
        st.session_state.selected_agents = all_agents

    def select_all(): st.session_state.selected_agents = all_agents
    def clear_all(): st.session_state.selected_agents = []

    with st.container():
        f_col1, _ = st.columns([1, 1])
        with f_col1:
            valid_dates = df_agents_full["Date of Sale"].dropna()
            if not valid_dates.empty:
                min_d, max_d = valid_dates.min().date(), valid_dates.max().date()
                date_range = st.date_input("📅 Date Range (Date of Sale)", [min_d, max_d])
            else:
                date_range = []

        st.write("🎧 **Select Quality Agent(s):**")
        btn_col1, btn_col2, _ = st.columns([1, 1, 6])
        with btn_col1: st.button("✅ Select All Agents", on_click=select_all, use_container_width=True)
        with btn_col2: st.button("❌ Clear All Agents", on_click=clear_all, use_container_width=True)

        selected_agents = st.multiselect("Agent List", options=all_agents, key='selected_agents', label_visibility="collapsed")

    # Apply Filters
    mask = (df_agents_full["Quality Agent Name"].isin(selected_agents))
    if len(date_range) == 2:
        mask = mask & (df_agents_full["Date of Sale"].dt.date >= date_range[0]) & (df_agents_full["Date of Sale"].dt.date <= date_range[1])

    df_filtered = df_agents_full[mask]

    if not selected_agents or df_filtered.empty:
        st.warning("⚠️ Please select agents or check date range.")
    else:
        # --- SECTION 1: PERFORMANCE OVERVIEW (CARDS) ---
        st.header("📊 Performance Overview")
        leads_in_selection = len(df_filtered)
        total_call_time = df_filtered["Call duration"].sum()
        total_work_time = df_filtered["Work duration"].sum()
        total_gap_sum = df_filtered["Duration Difference"].sum()
        avg_call, avg_work, avg_gap = df_filtered["Call duration"].mean(), df_filtered["Work duration"].mean(), df_filtered["Duration Difference"].mean()

        def create_card(label, value, color="#FFFFFF"):
            st.markdown(f"""<div style="background-color: rgba(255, 255, 255, 0.05); border-left: 5px solid {color}; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 10px;">
            <p style="color: #BDC3C7; font-size: 14px; text-transform: uppercase; font-weight: bold; margin-bottom: 5px;">{label}</p>
            <p style="color: {color}; font-size: 24px; font-weight: bold; margin: 0;">{value}</p></div>""", unsafe_allow_html=True)

        t1, t2, t3, t4, t5 = st.columns(5)
        with t1: create_card("Total Leads", f"{total_leads_in_sheet:,}", "#F1C40F")
        with t2: create_card("Leads Selected", f"{leads_in_selection:,}", "#3498DB")
        with t3: create_card("Total Call Time", f"{total_call_time:,.0f} m", "#2ECC71")
        with t4: create_card("Total Work Time", f"{total_work_time:,.0f} m", "#9B59B6")
        with t5: create_card("Total Gap", f"{total_gap_sum:,.1f} m", "#2ECC71" if total_gap_sum >= 0 else "#E74C3C")

        # --- SECTION 2: CHARTS ---
        Qa_stats = df_filtered.groupby("Quality Agent Name").agg(
            Total_Call_Duration=("Call duration", "sum"),
            Total_Work_Duration=("Work duration", "sum"),
            Total_Efficiency_Gap=("Duration Difference", "sum"),
            Total_Agent_Leads=("Quality Agent Name", "count")
        ).reset_index().sort_values(by="Total_Efficiency_Gap", ascending=False)

        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📊 Duration & Gap Comparison")
            plot_dur = Qa_stats.melt(id_vars="Quality Agent Name", value_vars=["Total_Call_Duration", "Total_Work_Duration", "Total_Efficiency_Gap"], var_name="Metric", value_name="Minutes")
            fig1 = px.bar(plot_dur, x="Quality Agent Name", y="Minutes", color="Metric", barmode="group", text_auto='.1f', template="plotly_dark",
                         color_discrete_map={"Total_Call_Duration": "#2ECC71", "Total_Work_Duration": "#E74C3C", "Total_Efficiency_Gap": "#3498DB"})
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            st.subheader("🔢 Leads per Agent")
            fig2 = px.bar(Qa_stats, x="Quality Agent Name", y="Total_Agent_Leads", color="Total_Agent_Leads", color_continuous_scale="YlOrRd", text_auto=True, template="plotly_dark")
            st.plotly_chart(fig2, use_container_width=True)

        # --- SECTION 4: GLOBAL CLOSING (FULL DATA) ---
        st.divider()
        st.header("🌍 Global Closing Analysis (Full Data)")
        df_global = df_processed.copy()
        df_global['Closing Status'] = df_global['Closing Status'].fillna('Unknown')
        all_dispo_global = sorted(df_global['Closing Status'].unique().tolist())

        if 'g_dispo' not in st.session_state: st.session_state.g_dispo = all_dispo_global
        def set_g_all(): st.session_state.g_dispo = all_dispo_global
        def set_g_none(): st.session_state.g_dispo = []

        st.write("🔍 **Filter Globally by Closing Status:**")
        dg1, dg2, _ = st.columns([1, 1, 6])
        with dg1: st.button("✅ Select All", on_click=set_g_all, key="g_btn_a", use_container_width=True)
        with dg2: st.button("❌ Clear All", on_click=set_g_none, key="g_btn_c", use_container_width=True)

        selected_dispo_g = st.multiselect("Status:", options=all_dispo_global, key='g_dispo', label_visibility="collapsed")
        df_final_g = df_global[df_global['Closing Status'].isin(selected_dispo_g)]

        if not selected_dispo_g:
            st.warning("Select status to view report.")
        else:
            # Charts
            cg1, cg2 = st.columns([2, 1])
            with cg1:
                df_p_g = df_final_g.copy()
                df_p_g['Quality Agent Name'] = df_p_g['Quality Agent Name'].fillna('Not Assigned')
                fig6 = px.bar(df_p_g.groupby(['Quality Agent Name', 'Closing Status']).size().reset_index(name='Count'), 
                             x="Quality Agent Name", y="Count", color="Closing Status", barmode="stack", text_auto=True, template="plotly_dark")
                st.plotly_chart(fig6, use_container_width=True)
            with cg2:
                fig7 = px.pie(df_final_g, names='Closing Status', hole=0.4, template="plotly_dark")
                st.plotly_chart(fig7, use_container_width=True)

            # --- SECTION 6: DATA INTEGRITY (MISSING DATA) ---
            st.divider()
            st.header("🛡️ Missing Data Report & Analysis")
            REQ_FIELDS = ["Assign Date", "Finish Date", "Recording link", "Validation", "QA Feedback"]
            df_all_probs = df_filtered[df_filtered[REQ_FIELDS].isnull().any(axis=1)].copy()

            if not df_all_probs.empty:
                def get_miss(row): return ", ".join([f for f in REQ_FIELDS if pd.isnull(row[f]) or str(row[f]).strip() == ""])
                df_all_probs["⚠️ MISSING FIELDS"] = df_all_probs.apply(get_miss, axis=1)
                
                all_iss = sorted(df_all_probs["⚠️ MISSING FIELDS"].unique().tolist())
                if 'sel_iss' not in st.session_state: st.session_state.sel_iss = all_iss
                def iss_all(): st.session_state.sel_iss = all_iss
                def iss_none(): st.session_state.sel_iss = []

                st.write("🔍 **Filter by Missing Type:**")
                ib1, ib2, _ = st.columns([1, 1, 6])
                with ib1: st.button("✅ All Types", on_click=iss_all, key="i_a", use_container_width=True)
                with ib2: st.button("❌ Clear", on_click=iss_none, key="i_n", use_container_width=True)

                sel_iss = st.multiselect("Issues:", options=all_iss, key='sel_iss', label_visibility="collapsed")
                df_probs = df_all_probs[df_all_probs["⚠️ MISSING FIELDS"].isin(sel_iss)]

                if sel_iss:
                    # Issue Cards
                    iss_counts = df_probs["⚠️ MISSING FIELDS"].value_counts()
                    cols = st.columns(min(len(iss_counts), 4))
                    colors = ["#FF4B4B", "#FFA500", "#1F77B4", "#9B59B6"]
                    for i, (iss_t, count) in enumerate(iss_counts.items()):
                        with cols[i % 4]:
                            st.markdown(f'<div style="border-left: 5px solid {colors[i%4]}; padding:10px; background:rgba(255,255,255,0.05); border-radius:5px;">'
                                        f'<p style="font-size:12px; color:{colors[i%4]}; font-weight:bold; margin:0;">{iss_t}</p>'
                                        f'<h3 style="margin:0;">{count} Leads</h3></div>', unsafe_allow_html=True)

                    # Table
                    st.write("### 📋 Targeted Issues List")
                    SPEC_COLS = ["⚠️ MISSING FIELDS", "MCN", "Opener Status", "Client", "Campaign", "Dialer", "Closing Status", "Date of Sale", "Call duration", "Work duration", "Quality Agent Name", "Validation", "Recording link"]
                    st.dataframe(df_probs[[c for c in SPEC_COLS if c in df_probs.columns]], use_container_width=True, hide_index=True,
                                 column_config={"Recording link": st.column_config.LinkColumn("🔗 Link"), "Date of Sale": st.column_config.DateColumn("Sale Date")})
            else:
                st.success("✅ Data is 100% complete!")

else:
    st.warning("📂 Please upload the CSV file to view the dashboard.")