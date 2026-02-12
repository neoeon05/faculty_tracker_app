import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px

# -----------------------------
# CONFIG
# -----------------------------
st.set_page_config(
    page_title="Guest Faculty Checklist", 
    layout="wide",
    initial_sidebar_state="expanded"
)

DATA_FILE = "faculty_checklist_data.csv"
EXCEL_FILE = "Faculty_Check_List.xlsx"

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    .stProgress > div > div > div > div {
        background-color: #1f77b4;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# LOAD INITIAL DATA
# -----------------------------
@st.cache_data
def load_initial_data():
    df = pd.read_excel(EXCEL_FILE)
    df = df.rename(columns={df.columns[1]: "Checklist Item"})
    return df

def initialize_data():
    if not os.path.exists(DATA_FILE):
        df_excel = load_initial_data()
        
        checklist_items = df_excel["Checklist Item"]
        faculty_columns = df_excel.columns[2:]

        records = []

        for faculty in faculty_columns:
            for item in checklist_items:
                records.append({
                    "Name": faculty.strip(),
                    "Designation": "",
                    "Session Name": "",
                    "Session Date": "",
                    "Checklist Item": item,
                    "Status": "Pending",
                    "Remarks": "",
                    "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Updated By": "System"
                })

        df = pd.DataFrame(records)
        df.to_csv(DATA_FILE, index=False)

def load_data():
    df = pd.read_csv(DATA_FILE)
    # Add new columns if they don't exist (for backward compatibility)
    if "Last Updated" not in df.columns:
        df["Last Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if "Updated By" not in df.columns:
        df["Updated By"] = "System"
    return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def add_new_faculty(name, designation, session_name, session_date):
    df = load_data()

    if name.strip() == "":
        return "Name cannot be empty", None

    # Check if faculty with same name and date already exists
    existing = df[(df["Name"] == name.strip()) & (df["Session Date"] == str(session_date))]
    if not existing.empty:
        return "Faculty with this name and session date already exists", None

    checklist_items = df["Checklist Item"].unique()

    new_records = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in checklist_items:
        new_records.append({
            "Name": name.strip(),
            "Designation": designation.strip(),
            "Session Name": session_name.strip(),
            "Session Date": str(session_date),
            "Checklist Item": item,
            "Status": "Pending",
            "Remarks": "",
            "Last Updated": timestamp,
            "Updated By": "Admin"
        })

    new_df = pd.DataFrame(new_records)
    df = pd.concat([df, new_df], ignore_index=True)
    save_data(df)

    return "Success", df

def delete_faculty(name, session_date):
    df = load_data()
    df = df[~((df["Name"] == name) & (df["Session Date"] == str(session_date)))]
    save_data(df)
    return df

def edit_faculty(old_name, old_session_date, new_name, new_designation, new_session_name, new_session_date):
    """Edit faculty details - updates all records for a faculty member"""
    df = load_data()
    
    # Check if new name/date combination already exists (and it's not the same faculty we're editing)
    if (new_name != old_name or str(new_session_date) != old_session_date):
        existing = df[(df["Name"] == new_name) & (df["Session Date"] == str(new_session_date))]
        if not existing.empty:
            return "Faculty with this name and session date already exists", None
    
    # Update all records for this faculty
    mask = (df["Name"] == old_name) & (df["Session Date"] == old_session_date)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    df.loc[mask, "Name"] = new_name.strip()
    df.loc[mask, "Designation"] = new_designation.strip()
    df.loc[mask, "Session Name"] = new_session_name.strip()
    df.loc[mask, "Session Date"] = str(new_session_date)
    df.loc[mask, "Last Updated"] = timestamp
    df.loc[mask, "Updated By"] = "Admin"
    
    save_data(df)
    return "Success", df

def export_to_excel(df, filename="faculty_checklist_export.xlsx"):
    """Export data to Excel with formatting"""
    output_path = f"/mnt/user-data/outputs/{filename}"
    
    with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Checklist Data', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['Checklist Data']
        
        # Add formatting
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1
        })
        
        # Format headers
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            worksheet.set_column(col_num, col_num, 15)
    
    return output_path

def get_faculty_summary(df):
    """Generate summary statistics for all faculty"""
    faculty_list = df[["Name", "Session Date"]].drop_duplicates()
    summary = []
    
    for _, row in faculty_list.iterrows():
        faculty_data = df[(df["Name"] == row["Name"]) & (df["Session Date"] == row["Session Date"])]
        total = len(faculty_data)
        done = len(faculty_data[faculty_data["Status"] == "Done"])
        pending = len(faculty_data[faculty_data["Status"] == "Pending"])
        na = len(faculty_data[faculty_data["Status"] == "NA"])
        
        summary.append({
            "Name": row["Name"],
            "Session Date": row["Session Date"],
            "Total Items": total,
            "Completed": done,
            "Pending": pending,
            "NA": na,
            "Progress %": round((done / total * 100) if total > 0 else 0, 1)
        })
    
    return pd.DataFrame(summary)

# -----------------------------
# INITIALIZE
# -----------------------------
initialize_data()
if 'df' not in st.session_state:
    st.session_state.df = load_data()

df = st.session_state.df

# -----------------------------
# SIDEBAR
# -----------------------------
st.sidebar.title("🎯 Navigation")

menu = st.sidebar.radio(
    "Select View",
    ["📋 Checklist Management", "📊 Dashboard & Analytics", "👥 Manage Faculty"],
    label_visibility="collapsed"
)

st.sidebar.markdown("---")

# =============================================
# VIEW 1: CHECKLIST MANAGEMENT
# =============================================
if menu == "📋 Checklist Management":
    
    # -------- Faculty Selection --------
    st.sidebar.markdown("### Select Faculty")
    
    faculty_list = df[["Name", "Session Date", "Designation", "Session Name"]].drop_duplicates()
    
    if faculty_list.empty:
        st.info("📝 No faculty added yet. Please add a faculty from the 'Manage Faculty' section.")
        st.stop()
    
    # Search/Filter options
    search_name = st.sidebar.text_input("🔍 Search by Name", "")
    
    if search_name:
        faculty_list = faculty_list[faculty_list["Name"].str.contains(search_name, case=False)]
    
    # Date range filter
    col1, col2 = st.sidebar.columns(2)
    with col1:
        filter_date = st.checkbox("Filter by Date Range")
    
    if filter_date:
        with col2:
            pass  # Placeholder for alignment
        date_from = st.sidebar.date_input("From Date")
        date_to = st.sidebar.date_input("To Date")
        
        # FIXED: Convert dates with proper format handling
        faculty_list = faculty_list[
            (pd.to_datetime(faculty_list["Session Date"], format='mixed', errors='coerce') >= pd.to_datetime(date_from)) &
            (pd.to_datetime(faculty_list["Session Date"], format='mixed', errors='coerce') <= pd.to_datetime(date_to))
        ]
    
    if faculty_list.empty:
        st.warning("No faculty found matching your filters.")
        st.stop()
    
    faculty_list["Display"] = (
        faculty_list["Name"] +
        " | " +
        faculty_list["Session Date"].astype(str) +
        " | " +
        faculty_list["Session Name"]
    )
    
    selected_display = st.sidebar.selectbox(
        "Faculty Member",
        faculty_list["Display"]
    )
    
    selected_row = faculty_list[
        faculty_list["Display"] == selected_display
    ].iloc[0]
    
    selected_name = selected_row["Name"]
    selected_date = selected_row["Session Date"]
    
    faculty_df = df[
        (df["Name"] == selected_name) &
        (df["Session Date"] == str(selected_date))
    ]
    
    # Bulk Actions
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚡ Bulk Actions")
    
    bulk_action = st.sidebar.selectbox(
        "Select Action",
        ["None", "Mark All as Done", "Mark All as Pending", "Clear All Remarks"]
    )
    
    if st.sidebar.button("Apply Bulk Action"):
        if bulk_action != "None":
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create mask to filter current faculty's rows
            mask = (st.session_state.df["Name"] == selected_name) & \
                   (st.session_state.df["Session Date"] == str(selected_date))
            
            # Apply bulk action to all matching rows
            if bulk_action == "Mark All as Done":
                st.session_state.df.loc[mask, "Status"] = "Done"
            elif bulk_action == "Mark All as Pending":
                st.session_state.df.loc[mask, "Status"] = "Pending"
            elif bulk_action == "Clear All Remarks":
                st.session_state.df.loc[mask, "Remarks"] = ""
            
            # Update timestamp and user for all affected rows
            st.session_state.df.loc[mask, "Last Updated"] = timestamp
            st.session_state.df.loc[mask, "Updated By"] = "Admin"
            
            save_data(st.session_state.df)
            st.sidebar.success(f"✅ {bulk_action} applied!")
            st.rerun()
    
    # Export Options
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📥 Export Options")
    
    export_option = st.sidebar.selectbox(
        "Export Format",
        ["Current Faculty", "All Faculty Data", "Summary Report"]
    )
    
    if st.sidebar.button("Export Data"):
        if export_option == "Current Faculty":
            export_df = faculty_df
            filename = f"{selected_name.replace(' ', '_')}_checklist.xlsx"
        elif export_option == "All Faculty Data":
            export_df = st.session_state.df
            filename = "all_faculty_checklist.xlsx"
        else:  # Summary Report
            export_df = get_faculty_summary(st.session_state.df)
            filename = "faculty_summary_report.xlsx"
        
        output_path = export_to_excel(export_df, filename)
        st.sidebar.success(f"✅ Exported to {filename}")
        
        # Provide download button
        with open(output_path, "rb") as file:
            st.sidebar.download_button(
                label="⬇️ Download File",
                data=file,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    # -----------------------------
    # MAIN CONTENT - CHECKLIST
    # -----------------------------
    st.markdown('<p class="main-header">📋 Guest Faculty Checklist Management</p>', unsafe_allow_html=True)
    
    # Faculty Info Card
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("### 👤 Faculty")
        st.markdown(f"**{selected_name}**")
    
    with col2:
        st.markdown("### 💼 Designation")
        st.markdown(f"**{faculty_df['Designation'].iloc[0] if not faculty_df.empty else 'N/A'}**")
    
    with col3:
        st.markdown("### 📚 Session")
        st.markdown(f"**{faculty_df['Session Name'].iloc[0] if not faculty_df.empty else 'N/A'}**")
    
    with col4:
        st.markdown("### 📅 Date")
        st.markdown(f"**{selected_date}**")
    
    st.markdown("---")
    
    # Progress Summary at Top
    total = len(faculty_df)
    completed = len(faculty_df[faculty_df["Status"] == "Done"])
    pending = len(faculty_df[faculty_df["Status"] == "Pending"])
    na = len(faculty_df[faculty_df["Status"] == "NA"])
    progress = completed / total if total > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Items", total)
    with col2:
        st.metric("✅ Completed", completed, f"{progress*100:.1f}%")
    with col3:
        st.metric("⏳ Pending", pending)
    with col4:
        st.metric("🚫 N/A", na)
    
    st.progress(progress)
    
    st.markdown("---")
    
    # Filter options for checklist items
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Checklist Items")
    with col2:
        filter_status = st.selectbox(
            "Filter by Status",
            ["All", "Pending", "Done", "NA"],
            key="filter_status"
        )
    
    # Apply filter
    if filter_status != "All":
        display_df = faculty_df[faculty_df["Status"] == filter_status]
    else:
        display_df = faculty_df
    
    if display_df.empty:
        st.info(f"No items with status '{filter_status}'")
    else:
        # -----------------------------
        # CHECKLIST DISPLAY
        # -----------------------------
        updated_rows = []
        
        for index, row in display_df.iterrows():
            with st.container():
                col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
                
                with col1:
                    st.markdown(f"**{row['Checklist Item']}**")
                
                with col2:
                    status = st.selectbox(
                        "Status",
                        ["Pending", "Done", "NA"],
                        index=["Pending", "Done", "NA"].index(row["Status"]),
                        key=f"status_{index}",
                        label_visibility="collapsed"
                    )
                
                with col3:
                    remarks = st.text_input(
                        "Remarks",
                        value=row["Remarks"],
                        key=f"remarks_{index}",
                        placeholder="Add remarks..."
                    )
                
                with col4:
                    # Show last updated info
                    if "Last Updated" in row:
                        st.caption(f"Updated: {row['Last Updated'][:10]}")
                
                updated_rows.append((index, status, remarks))
                
                st.markdown("---")
        
        # -----------------------------
        # SAVE BUTTON
        # -----------------------------
        col1, col2, col3 = st.columns([2, 1, 2])
        with col2:
            if st.button("💾 Save All Updates", type="primary", use_container_width=True):
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                for idx, status, remarks in updated_rows:
                    st.session_state.df.at[idx, "Status"] = status
                    st.session_state.df.at[idx, "Remarks"] = remarks
                    st.session_state.df.at[idx, "Last Updated"] = timestamp
                    st.session_state.df.at[idx, "Updated By"] = "Admin"
                
                save_data(st.session_state.df)
                st.success("✅ All updates saved successfully!")
                st.rerun()

# =============================================
# VIEW 2: DASHBOARD & ANALYTICS
# =============================================
elif menu == "📊 Dashboard & Analytics":
    
    st.markdown('<p class="main-header">📊 Analytics Dashboard</p>', unsafe_allow_html=True)
    
    # Overall Statistics
    st.markdown("### 📈 Overall Statistics")
    
    total_faculty = len(df[["Name", "Session Date"]].drop_duplicates())
    total_items = len(df)
    total_completed = len(df[df["Status"] == "Done"])
    overall_progress = (total_completed / total_items * 100) if total_items > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("👥 Total Faculty", total_faculty)
    with col2:
        st.metric("📋 Total Checklist Items", total_items)
    with col3:
        st.metric("✅ Items Completed", total_completed)
    with col4:
        st.metric("📊 Overall Progress", f"{overall_progress:.1f}%")
    
    st.markdown("---")
    
    # Faculty Summary Table
    st.markdown("### 👥 Faculty Progress Summary")
    
    summary_df = get_faculty_summary(df)
    
    if not summary_df.empty:
        # Color-code progress
        def color_progress(val):
            if val >= 80:
                color = 'lightgreen'
            elif val >= 50:
                color = 'lightyellow'
            else:
                color = 'lightcoral'
            return f'background-color: {color}'
        
        styled_df = summary_df.style.applymap(
            color_progress, 
            subset=['Progress %']
        )
        
        st.dataframe(styled_df, use_container_width=True, height=400)
        
        # Charts
        st.markdown("---")
        st.markdown("### 📊 Visual Analytics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Progress Distribution Chart
            fig_progress = px.bar(
                summary_df,
                x="Name",
                y="Progress %",
                title="Faculty Progress Distribution",
                color="Progress %",
                color_continuous_scale="RdYlGn"
            )
            fig_progress.update_layout(height=400)
            st.plotly_chart(fig_progress, use_container_width=True)
        
        with col2:
            # Status Distribution Pie Chart
            status_counts = df["Status"].value_counts()
            fig_status = px.pie(
                values=status_counts.values,
                names=status_counts.index,
                title="Overall Status Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_status.update_layout(height=400)
            st.plotly_chart(fig_status, use_container_width=True)
        
        # Timeline Chart
        st.markdown("---")
        st.markdown("### 📅 Session Timeline")
        
        timeline_df = summary_df.copy()
        # FIXED: Convert dates with proper format handling for plotting
        timeline_df['Session Date'] = pd.to_datetime(timeline_df['Session Date'], format='mixed', errors='coerce')
        timeline_df = timeline_df.dropna(subset=['Session Date'])  # Remove any invalid dates
        timeline_df = timeline_df.sort_values("Session Date")
        
        fig_timeline = px.scatter(
            timeline_df,
            x="Session Date",
            y="Progress %",
            size="Total Items",
            color="Progress %",
            hover_data=["Name"],
            title="Faculty Progress Over Time",
            color_continuous_scale="Viridis"
        )
        fig_timeline.update_layout(height=400)
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Completion Rate by Item
        st.markdown("---")
        st.markdown("### 📋 Checklist Item Analysis")
        
        item_analysis = df.groupby("Checklist Item")["Status"].apply(
            lambda x: (x == "Done").sum() / len(x) * 100
        ).reset_index()
        item_analysis.columns = ["Checklist Item", "Completion Rate %"]
        item_analysis = item_analysis.sort_values("Completion Rate %", ascending=False)
        
        fig_items = px.bar(
            item_analysis,
            x="Completion Rate %",
            y="Checklist Item",
            orientation='h',
            title="Completion Rate by Checklist Item",
            color="Completion Rate %",
            color_continuous_scale="Blues"
        )
        fig_items.update_layout(height=600)
        st.plotly_chart(fig_items, use_container_width=True)

# =============================================
# VIEW 3: MANAGE FACULTY
# =============================================
else:  # Manage Faculty
    
    st.markdown('<p class="main-header">👥 Manage Faculty</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["➕ Add New Faculty", "✏️ Edit Faculty", "🗑️ Delete Faculty"])
    
    with tab1:
        st.markdown("### Add New Guest Faculty")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_name = st.text_input("Faculty Name*", key="add_name")
            new_session_name = st.text_input("Session Name*", key="add_session")
        
        with col2:
            new_designation = st.text_input("Designation*", key="add_designation")
            new_session_date = st.date_input("Session Date*", key="add_date")
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns([2, 1, 2])
        
        with col2:
            if st.button("➕ Add Faculty", type="primary", use_container_width=True):
                if not new_name or not new_designation or not new_session_name:
                    st.error("⚠️ Please fill all required fields marked with *")
                else:
                    result, updated_df = add_new_faculty(
                        new_name,
                        new_designation,
                        new_session_name,
                        new_session_date
                    )
                    
                    if result == "Success":
                        st.session_state.df = updated_df
                        st.success(f"✅ Faculty '{new_name}' added successfully!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(f"❌ {result}")
    
    with tab2:
        st.markdown("### Edit Faculty Details")
        st.info("ℹ️ Select a faculty member to edit their information. All checklist items will be preserved.")
        
        faculty_list = df[["Name", "Session Date", "Session Name", "Designation"]].drop_duplicates()
        
        if faculty_list.empty:
            st.info("No faculty to edit.")
        else:
            faculty_list["Display"] = (
                faculty_list["Name"] +
                " | " +
                faculty_list["Session Date"].astype(str) +
                " | " +
                faculty_list["Session Name"]
            )
            
            edit_selection = st.selectbox(
                "Select Faculty to Edit",
                faculty_list["Display"],
                key="edit_select"
            )
            
            selected_row = faculty_list[
                faculty_list["Display"] == edit_selection
            ].iloc[0]
            
            st.markdown("---")
            st.markdown("### Edit Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                edit_name = st.text_input(
                    "Faculty Name*", 
                    value=selected_row["Name"],
                    key="edit_name"
                )
                edit_session_name = st.text_input(
                    "Session Name*", 
                    value=selected_row["Session Name"],
                    key="edit_session"
                )
            
            with col2:
                edit_designation = st.text_input(
                    "Designation*", 
                    value=selected_row["Designation"],
                    key="edit_designation"
                )
                # Convert session date string to date object for date_input
                try:
                    current_date = pd.to_datetime(selected_row["Session Date"]).date()
                except:
                    current_date = datetime.now().date()
                
                edit_session_date = st.date_input(
                    "Session Date*", 
                    value=current_date,
                    key="edit_date"
                )
            
            st.markdown("---")
            
            col1, col2, col3 = st.columns([2, 1, 2])
            
            with col2:
                if st.button("💾 Save Changes", type="primary", use_container_width=True):
                    if not edit_name or not edit_designation or not edit_session_name:
                        st.error("⚠️ Please fill all required fields marked with *")
                    else:
                        result, updated_df = edit_faculty(
                            selected_row["Name"],
                            selected_row["Session Date"],
                            edit_name,
                            edit_designation,
                            edit_session_name,
                            edit_session_date
                        )
                        
                        if result == "Success":
                            st.session_state.df = updated_df
                            st.success(f"✅ Faculty details updated successfully!")
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")
    
    with tab3:
        st.markdown("### Delete Faculty Member")
        st.warning("⚠️ This action cannot be undone. All checklist data for this faculty will be deleted.")
        
        faculty_list = df[["Name", "Session Date", "Session Name"]].drop_duplicates()
        
        if faculty_list.empty:
            st.info("No faculty to delete.")
        else:
            faculty_list["Display"] = (
                faculty_list["Name"] +
                " | " +
                faculty_list["Session Date"].astype(str) +
                " | " +
                faculty_list["Session Name"]
            )
            
            delete_selection = st.selectbox(
                "Select Faculty to Delete",
                faculty_list["Display"]
            )
            
            selected_row = faculty_list[
                faculty_list["Display"] == delete_selection
            ].iloc[0]
            
            st.markdown("---")
            
            # Confirmation checkbox BEFORE the button
            confirm = st.checkbox("✅ I confirm I want to delete this faculty", key="delete_confirm")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([2, 1, 2])
            
            with col2:
                if st.button("🗑️ Delete Faculty", type="primary", use_container_width=True, disabled=not confirm):
                    if confirm:
                        updated_df = delete_faculty(
                            selected_row["Name"],
                            selected_row["Session Date"]
                        )
                        st.session_state.df = updated_df
                        st.success(f"✅ Faculty '{selected_row['Name']}' deleted successfully!")
                        st.rerun()


# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
    <small>Guest Faculty Checklist Management System | Version 3.0 Enhanced</small>
</div>
""", unsafe_allow_html=True)