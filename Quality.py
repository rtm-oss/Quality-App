import pandas as pd 
import numpy as np
import streamlit as st
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="📈 QA Dynamic Dashboard", layout="wide")
st.title(" Quality Agents Dynamic Analysis")

# 2. Data Preparation - Columns to keep
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
def load_and_process_data(uploaded_file):
    df_raw = pd.read_csv(uploaded_file)
    df_cleaned = df_raw[[col for col in COLUMNS_TO_KEEP if col in df_raw.columns]].copy()
    
    df_cleaned["Call duration"] = pd.to_numeric(df_cleaned["Call duration"], errors='coerce').fillna(0)
    df_cleaned["Work duration"] = pd.to_numeric(df_cleaned["Work duration"], errors='coerce').fillna(0)
    
    df_cleaned["Duration Difference"] = df_cleaned["Call duration"] - df_cleaned["Work duration"]
        
    date_cols = ["Created Time", "Modified Time", "Date of Sale", "Finish Date", "Assign Date"]
    for col in date_cols:
        if col in df_cleaned.columns:
            df_cleaned[col] = pd.to_datetime(df_cleaned[col], dayfirst=True, errors='coerce')
            
    return df_raw, df_cleaned
    
# --- FILE UPLOADER SECTION ---
uploaded_file = st.file_uploader("📥 Upload your CSV file (O_Plan_Leads.csv)", type="csv")

if uploaded_file is not None:
    # 3. Load Data from Uploaded File
    df_raw, df_processed = load_and_process_data(uploaded_file)
    total_leads_in_sheet = len(df_raw)
    df_agents_full = df_processed.dropna(subset=["Quality Agent Name"])

    # --- DYNAMIC FILTER PANEL ---
    all_agents = sorted(df_agents_full["Quality Agent Name"].unique().tolist())
    if 'selected_agents' not in st.session_state:
        st.session_state.selected_agents = all_agents

    def select_all():
        st.session_state.selected_agents = all_agents

    def clear_all():
        st.session_state.selected_agents = []

    with st.container():
        f_col1, _ = st.columns([1, 1])
        with f_col1:
            valid_dates = df_agents_full["Date of Sale"].dropna()
            if not valid_dates.empty:
                min_d = valid_dates.min().date()
                max_d = valid_dates.max().date()
                date_range = st.date_input("📅 Date Range (Date of Sale)", [min_d, max_d])
            else:
                st.warning("No valid 'Date of Sale' found.")
                date_range = []

        st.write("🎧 **Select Quality Agent(s):**")
        btn_col1, btn_col2, _ = st.columns([1, 1, 6])
        with btn_col1:
            st.button("✅ Select All", on_click=select_all, use_container_width=True)
        with btn_col2:
            st.button("❌ Clear All", on_click=clear_all, use_container_width=True)

        selected_agents = st.multiselect(
            "Agent List", 
            options=all_agents, 
            key='selected_agents',
            label_visibility="collapsed"
        )

    st.divider()

    # --- APPLY FINAL FILTERS ---
    mask = (df_agents_full["Quality Agent Name"].isin(selected_agents))
    if len(date_range) == 2:
        mask = mask & (df_agents_full["Date of Sale"].dt.date >= date_range[0]) & (df_agents_full["Date of Sale"].dt.date <= date_range[1])

    df_filtered = df_agents_full[mask]

    if not selected_agents:
        st.warning("⚠️ Please select at least one agent.")
        st.stop()
    if df_filtered.empty:
        st.warning("⚠️ No data found for the selected criteria.")
        st.stop()

    # 4. Aggregated Statistics
    Qa_stats = df_filtered.groupby("Quality Agent Name").agg(
        Total_Call_Duration=("Call duration", "sum"),
        Total_Work_Duration=("Work duration", "sum"),
        Total_Efficiency_Gap=("Duration Difference", "sum"),
        Total_Agent_Leads=("Quality Agent Name", "count") 
    ).reset_index()

    Qa_stats = Qa_stats.sort_values(by="Total_Efficiency_Gap", ascending=False)

    # --- SECTION 1: PERFORMANCE OVERVIEW (DYNAMIC CARDS) ---
    st.header("📊 Performance Overview")

    leads_in_selection = len(df_filtered)
    total_call_time = df_filtered["Call duration"].sum()
    total_work_time = df_filtered["Work duration"].sum()
    total_gap_sum = df_filtered["Duration Difference"].sum()

    avg_call_time = df_filtered["Call duration"].mean()
    avg_work_time = df_filtered["Work duration"].mean()
    avg_gap = df_filtered["Duration Difference"].mean()

    total_gap_color = "#2ECC71" if total_gap_sum >= 0 else "#E74C3C"
    avg_gap_color = "#2ECC71" if avg_gap >= 0 else "#E74C3C"

    def create_card(label, value, color="#FFFFFF", bg_opacity=0.1):
        st.markdown(
            f"""
            <div style="
                background-color: rgba(255, 255, 255, {bg_opacity});
                border-left: 5px solid {color};
                padding: 20px;
                border-radius: 10px;
                box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
                text-align: center;
                margin-bottom: 10px;
            ">
                <p style="color: #BDC3C7; font-size: 14px; text-transform: uppercase; font-weight: bold; margin-bottom: 5px;">{label}</p>
                <p style="color: {color}; font-size: 24px; font-weight: bold; margin: 0;">{value}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.subheader("📌 Global Totals")
    t1, t2, t3, t4, t5 = st.columns(5)
    with t1: create_card("Total Leads", f"{total_leads_in_sheet:,}", color="#F1C40F")
    with t2: create_card("Leads Selected", f"{leads_in_selection:,}", color="#3498DB")
    with t3: create_card("Total Call Time", f"{total_call_time:,.0f} min", color="#2ECC71")
    with t4: create_card("Total Work Time", f"{total_work_time:,.0f} min", color="#9B59B6")
    with t5: create_card("Total Efficiency Gap", f"{total_gap_sum:,.1f} min", color=total_gap_color)

    st.subheader("💡 Performance Averages (Per Lead)")
    a1, a2, a3 = st.columns(3)
    with a1: create_card("Avg Call Duration", f"{avg_call_time:.2f} min", color="#2ECC71")
    with a2: create_card("Avg Work Duration", f"{avg_work_time:.2f} min", color="#9B59B6")
    with a3: create_card("Avg Efficiency Gap", f"{avg_gap:.2f} min", color=avg_gap_color)

    st.divider()

    # SECTION 2: CHARTS
    st.header("📈 Agent Analysis Charts")
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.subheader("📊 Total Duration & Gap Comparison")
        plot_durations = Qa_stats.melt(id_vars="Quality Agent Name", value_vars=["Total_Call_Duration", "Total_Work_Duration", "Total_Efficiency_Gap"], var_name="Metric", value_name="Minutes")
        fig_durations = px.bar(plot_durations, x="Quality Agent Name", y="Minutes", color="Metric", barmode="group", text_auto='.1f', 
                               color_discrete_map={"Total_Call_Duration": "#2ECC71", "Total_Work_Duration": "#E74C3C", "Total_Efficiency_Gap": "#3498DB"}, template="plotly_dark")
        fig_durations.update_traces(textposition='outside', cliponaxis=False)
        st.plotly_chart(fig_durations, use_container_width=True)

    with chart_col2:
        st.subheader("🔢 Leads Distribution per Agent")
        fig_leads = px.bar(Qa_stats, x="Quality Agent Name", y="Total_Agent_Leads", color="Total_Agent_Leads", color_continuous_scale="YlOrRd", text_auto=True, template="plotly_dark")
        fig_leads.update_traces(textposition='outside')
        st.plotly_chart(fig_leads, use_container_width=True)

    st.subheader("📉 Total Efficiency Gap Trend")
    fig_line = px.line(Qa_stats, x="Quality Agent Name", y="Total_Efficiency_Gap", markers=True, text=Qa_stats["Total_Efficiency_Gap"].round(1), template="plotly_dark")
    fig_line.update_traces(line_color="#2ECC71", textposition="top center")
    st.plotly_chart(fig_line, use_container_width=True)

    # SECTION 2.1: VALIDATION ANALYSIS
    st.divider()
    st.header("✅ Validation Analysis")
    v_col1, v_col2 = st.columns([2, 1])

    with v_col1:
        st.subheader("Distribution by Agent")
        validation_counts = df_filtered.groupby(['Quality Agent Name', 'Validation']).size().reset_index(name='Lead Count')
        fig_validation_bar = px.bar(validation_counts, x="Quality Agent Name", y="Lead Count", color="Validation", text_auto=True, barmode="stack",
                                    color_discrete_map={"Smooth": "#2ECC71", "Handled": "#F1C40F", "Having Issue": "#E74C3C"}, template="plotly_dark")
        st.plotly_chart(fig_validation_bar, use_container_width=True)

    with v_col2:
        st.subheader("Overall Status %")
        overall_val_counts = df_filtered['Validation'].value_counts().reset_index()
        overall_val_counts.columns = ['Status', 'Count']
        fig_pie = px.pie(overall_val_counts, values='Count', names='Status', color='Status', hole=0.4,
                         color_discrete_map={"Smooth": "#2ECC71", "Handled": "#F1C40F", "Having Issue": "#E74C3C"}, template="plotly_dark")
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    st.divider()

    # SECTION 3: DATA TABLE
    st.header("🔍 Detailed Statistics Table")
    st.dataframe(Qa_stats.style.background_gradient(cmap='RdYlGn', subset=['Total_Efficiency_Gap']).format(precision=2), use_container_width=True)

    # SECTION 4: GLOBAL CLOSING DISPOSITION ANALYSIS (FULL DATA)
    st.divider()
    st.header("Closing Disposition Analysis")

    df_global = df_processed.copy()
    df_global['Closing Status'] = df_global['Closing Status'].fillna('Unknown')
    all_dispositions_global = sorted(df_global['Closing Status'].unique().tolist())

    if 'selected_dispo_global' not in st.session_state:
        st.session_state.selected_dispo_global = all_dispositions_global

    def select_all_global(): st.session_state.selected_dispo_global = all_dispositions_global
    def clear_all_global(): st.session_state.selected_dispo_global = []

    st.write("🔍 **Filter Globally by Closing Status:**")
    dg_btn_col1, dg_btn_col2, _ = st.columns([1, 1, 6])
    with dg_btn_col1: st.button("✅ Select All Status", on_click=select_all_global, key="dispo_all_global", use_container_width=True)
    with dg_btn_col2: st.button("❌ Clear All Status", on_click=clear_all_global, key="dispo_clear_global", use_container_width=True)

    selected_dispo_global = st.multiselect("Select Status:", options=all_dispositions_global, key='selected_dispo_global', label_visibility="collapsed")
    df_closing_global = df_global[df_global['Closing Status'].isin(selected_dispo_global)]

    if not selected_dispo_global:
        st.warning("⚠️ Please select at least one Closing Status to view global analysis.")
    elif df_closing_global.empty:
        st.warning("⚠️ No data matches selection.")
    else:
        st.subheader("Closing Distribution by Agent")
        df_closing_global_plot = df_closing_global.copy()
        df_closing_global_plot['Quality Agent Name'] = df_closing_global_plot['Quality Agent Name'].fillna('Not Assigned')
        closing_counts_global = df_closing_global_plot.groupby(['Quality Agent Name', 'Closing Status']).size().reset_index(name='Lead Count')
        
        fig_global_bar = px.bar(closing_counts_global, x="Quality Agent Name", y="Lead Count", color="Closing Status", text_auto=True, barmode="stack", 
                               template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
        st.plotly_chart(fig_global_bar, use_container_width=True)

        st.subheader("Global Overall Closing %")
        overall_global_counts = df_closing_global['Closing Status'].value_counts().reset_index()
        overall_global_counts.columns = ['Status', 'Count']
        fig_global_pie = px.pie(overall_global_counts, values='Count', names='Status', hole=0.4, template="plotly_dark", color_discrete_sequence=px.colors.qualitative.Pastel)
        fig_global_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_global_pie, use_container_width=True)

    # SECTION 5: DETAILED LEADS REPORT
    st.divider()
    st.header("📋 Detailed Leads Report")
    VIEW_COLUMNS = ["MCN","Quality Agent Name", "First Name", "Last Name", "Date of Sale", "Closing Status", "Validation", "Call duration", "Work duration", "Recording link"]
    final_display_cols = [col for col in VIEW_COLUMNS if col in df_closing_global.columns]

    st.write(f"Showing **{len(df_closing_global)}** leads based on your global selection:")
    st.dataframe(df_closing_global[final_display_cols], column_config={"Recording link": st.column_config.LinkColumn("🔗 Recording link"), "Date of Sale": st.column_config.DateColumn("📅 Sale Date"),
                 "Call duration": st.column_config.NumberColumn("📞 Call (m)", format="%.1f"), "Work duration": st.column_config.NumberColumn("⏱️ Work (m)", format="%.1f")}, use_container_width=True, hide_index=True)

    csv = df_closing_global.to_csv(index=False).encode('utf-8')
    st.download_button(label="📥 Download Filtered Leads as CSV", data=csv, file_name='Global_Filtered_QA_Report.csv', mime='text/csv')

    # --- SECTION 6: DATA INTEGRITY ALERTS (FINAL REVIEW) ---
st.divider()
st.header("🛡️ Missing Data Report & Analysis")

# تم إزالة QA Feedback من قائمة الأعمدة المطلوبة للفحص بناءً على طلبك
REQUIRED_FIELDS = ["Assign Date", "Finish Date", "Recording link", "Validation"]

# 1. تحديد الصفوف التي بها أي قيمة فارغة في المعايير الجديدة
missing_mask = df_filtered[REQUIRED_FIELDS].isnull().any(axis=1)
df_all_problems = df_filtered[missing_mask].copy()

if not df_all_problems.empty:
    # 2. وظيفة لتحديد ما هو المفقود بالضبط (بدون QA Feedback)
    def get_missing_columns(row):
        missing = [field for field in REQUIRED_FIELDS if pd.isnull(row[field]) or str(row[field]).strip() == ""]
        return ", ".join(missing)

    df_all_problems["⚠️ MISSING FIELDS"] = df_all_problems.apply(get_missing_columns, axis=1)
    
    # الحصول على القائمة الفريدة لأنواع النقص
    all_issue_types = sorted(df_all_problems["⚠️ MISSING FIELDS"].unique().tolist())

    # 3. إدارة الـ Session State للفلاتر الديناميكية
    if 'selected_issues' not in st.session_state:
        st.session_state.selected_issues = all_issue_types

    def select_all_issues(): st.session_state.selected_issues = all_issue_types
    def clear_all_issues(): st.session_state.selected_issues = []

    st.write("🔍 **Dynamic Filter: Need Update In**")
    i_btn_col1, i_btn_col2, _ = st.columns([1, 1, 6])
    with i_btn_col1:
        st.button("✅ Select All Types", on_click=select_all_issues, key="issue_all_btn", use_container_width=True)
    with i_btn_col2:
        st.button("❌ Clear All Types", on_click=clear_all_issues, key="issue_clear_btn", use_container_width=True)

    selected_issues = st.multiselect("Filter combinations:", options=all_issue_types, key='selected_issues', label_visibility="collapsed")

    # تصفية البيانات بناءً على الاختيار
    df_problems = df_all_problems[df_all_problems["⚠️ MISSING FIELDS"].isin(selected_issues)]

    if not selected_issues:
        st.warning("⚠️ Please select at least one combination to view the report.")
    elif df_problems.empty:
        st.info("ℹ️ No leads found for this selection.")
    else:
        # 4. العدادات الملونة المحدثة
        st.subheader("📊 Missing Data Summary")
        issue_counts = df_problems["⚠️ MISSING FIELDS"].value_counts()
        
        cols = st.columns(len(issue_counts) if len(issue_counts) < 5 else 4)
        colors = ["#FF4B4B", "#FFA500", "#1F77B4", "#9B59B6", "#00D2FF", "#FF00FF"]
        
        for i, (issue_type, count) in enumerate(issue_counts.items()):
            col_idx = i % (len(cols))
            color = colors[i % len(colors)]
            with cols[col_idx]:
                st.markdown(
                    f"""
                    <div style="
                        background-color: rgba(255, 255, 255, 0.05);
                        border: 1px solid {color};
                        border-left: 10px solid {color};
                        padding: 15px;
                        border-radius: 8px;
                        text-align: left;
                        margin-bottom: 10px;
                        min-height: 120px;
                    ">
                        <p style="color: {color}; font-size: 13px; font-weight: bold; margin: 0; min-height: 40px;">{issue_type}</p>
                        <h2 style="color: white; margin: 5px 0 0 0;">{count} <span style="font-size: 14px; color: #888;">Leads</span></h2>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # 5. الجدول المخصص (بدون عرض QA Feedback كأولوية في البحث)
        st.markdown("<br>", unsafe_allow_html=True)
        st.subheader("📋 Targeted Issues List")
        
        SPECIFIC_COLUMNS = [
            "⚠️ MISSING FIELDS", "MCN", "Opener Status", "Client", "Campaign", 
            "Dialer", "Closing Status", "Date of Sale", "Assign Date","Finish Date","Call duration", 
            "Work duration", "Quality Agent Name", "Validation", "Recording link"
        ]
        available_cols = [col for col in SPECIFIC_COLUMNS if col in df_problems.columns]

        st.dataframe(
            df_problems[available_cols],
            column_config={
                "Recording link": st.column_config.LinkColumn("🔗 Link"),
                "Date of Sale": st.column_config.DateColumn("📅 Sale Date"),
                "Call duration": st.column_config.NumberColumn("📞 Call (m)", format="%.1f"),
                "Work duration": st.column_config.NumberColumn("⏱️ Work (m)", format="%.1f"),
                "⚠️ MISSING FIELDS": st.column_config.TextColumn("⚠️ NEEDS UPDATE IN:", width="medium")
            },
            use_container_width=True,
            hide_index=True
        )

        # 6. زر تحميل الاختيار الحالي
        csv_problems = df_problems[available_cols].to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download This Selection (CSV)",
            data=csv_problems,
            file_name='Targeted_Issues_Report.csv',
            mime='text/csv',
        )
else:
    st.success("✅ Excellent! All records in this selection are complete for Dates, Links, and Validation.")

