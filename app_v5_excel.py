import streamlit as st
import pandas as pd
import os
import hashlib
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
USERS_FILE = "users_data.csv"

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
    .login-container {
        max-width: 400px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #f0f2f6;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# USER AUTHENTICATION FUNCTIONS
# -----------------------------
def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def initialize_users():
    """Initialize users file with default admin account"""
    if not os.path.exists(USERS_FILE):
        default_users = pd.DataFrame([{
            'username': 'admin',
            'password': hash_password('admin123'),
            'role': 'admin',
            'full_name': 'Administrator',
            'email': 'admin@example.com',
            'created_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'active': True
        }])
        default_users.to_csv(USERS_FILE, index=False)

def load_users():
    """Load users from CSV file"""
    initialize_users()
    return pd.read_csv(USERS_FILE)

def save_users(df):
    """Save users to CSV file"""
    df.to_csv(USERS_FILE, index=False)

def authenticate_user(username, password):
    """Authenticate user credentials"""
    users_df = load_users()
    user = users_df[users_df['username'] == username]
    
    if user.empty:
        return False, None, None
    
    user = user.iloc[0]
    
    if not user['active']:
        return False, None, "Account is inactive"
    
    if user['password'] == hash_password(password):
        return True, user['role'], user['full_name']
    
    return False, None, "Invalid password"

def add_user(username, password, role, full_name, email):
    """Add a new user"""
    users_df = load_users()
    
    if username in users_df['username'].values:
        return False, "Username already exists"
    
    new_user = pd.DataFrame([{
        'username': username,
        'password': hash_password(password),
        'role': role,
        'full_name': full_name,
        'email': email,
        'created_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'active': True
    }])
    
    users_df = pd.concat([users_df, new_user], ignore_index=True)
    save_users(users_df)
    return True, "User added successfully"

def update_user(username, full_name=None, email=None, password=None, active=None):
    """Update user details"""
    users_df = load_users()
    
    if username not in users_df['username'].values:
        return False, "User not found"
    
    idx = users_df[users_df['username'] == username].index[0]
    
    if full_name:
        users_df.at[idx, 'full_name'] = full_name
    if email:
        users_df.at[idx, 'email'] = email
    if password:
        users_df.at[idx, 'password'] = hash_password(password)
    if active is not None:
        users_df.at[idx, 'active'] = active
    
    save_users(users_df)
    return True, "User updated successfully"

def delete_user(username):
    """Delete a user (and their faculty data)"""
    users_df = load_users()
    
    if username == 'admin':
        return False, "Cannot delete admin account"
    
    # Delete user's faculty data
    df = load_data()
    df = df[df['Owner'] != username]
    save_data(df)
    
    # Delete user
    users_df = users_df[users_df['username'] != username]
    save_users(users_df)
    return True, "User deleted successfully"

# -----------------------------
# LOAD INITIAL DATA
# -----------------------------
@st.cache_data
def load_initial_data():
    df = pd.read_excel(EXCEL_FILE)
    df = df.rename(columns={df.columns[1]: "Checklist Item"})
    return df

def initialize_data(force=False):
    if not os.path.exists(DATA_FILE) or force:
        # Try to load from Excel if it exists, otherwise use default checklist
        try:
            if os.path.exists(EXCEL_FILE):
                df_excel = load_initial_data()
                checklist_items = df_excel["Checklist Item"]
                faculty_columns = df_excel.columns[2:]
                
                records = []
                for faculty in faculty_columns:
                    for item in checklist_items:
                        records.append({
                            "Owner": "admin",  # Add Owner field
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
            else:
                # Default checklist items for Guest Faculty Management
                default_checklist_items = [
                    "Letter to Guest Faculty",
                    "Letter to Boss",
                    "Tour Program",
                    "Room Book",
                    "Inbound Vehicle",
                    "Outbound Vehicle",
                    "Book Tickets",
                    "Protocol Officer",
                    "Link (if Online mode)",
                    "Biodata of Faculty",
                    "Name Plate",
                    "Welcome Board",
                    "Faculty Folder (OTs Biodata, Schedule, Pen)",
                    "Local Vehicle",
                    "Pre-receipt",
                    "Thanks Letter",
                    "Honorarium Put up",
                    "Protocal Office List Update",
                    "Reimbursement (if any)",
                    "Feedback from OTs",
                    "Compiling Feedback",
                    "Postal Card"
                ]
                
                records = []
                # Start with empty database - users will add faculty manually
                for item in default_checklist_items:
                    records.append({
                        "Owner": "admin",  # Add Owner field
                        "Name": "Sample Faculty",
                        "Designation": "Guest Speaker",
                        "Session Name": "Sample Session",
                        "Session Date": datetime.now().strftime("%Y-%m-%d"),
                        "Checklist Item": item,
                        "Status": "Pending",
                        "Remarks": "This is a sample entry. Add your own faculty from 'Manage Faculty' section.",
                        "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Updated By": "System"
                    })
        except Exception as e:
            # Fallback to default checklist if Excel loading fails
            default_checklist_items = [
                "Letter to Guest Faculty",
                "Letter to Boss",
                "Tour Program",
                "Room Book",
                "Inbound Vehicle",
                "Outbound Vehicle",
                "Book Tickets",
                "Protocol Officer",
                "Link (if Online mode)",
                "Biodata of Faculty",
                "Name Plate",
                "Welcome Board",
                "Faculty Folder (OTs Biodata, Schedule, Pen)",
                "Local Vehicle",
                "Pre-receipt",
                "Thanks Letter",
                "Honorarium Put up",
                "Protocal Office List Update",
                "Reimbursement (if any)",
                "Feedback from OTs",
                "Compiling Feedback",
                "Postal Card"
            ]
            
            records = []
            for item in default_checklist_items:
                records.append({
                    "Owner": "admin",  # Add Owner field
                    "Name": "Sample Faculty",
                    "Designation": "Guest Speaker",
                    "Session Name": "Sample Session",
                    "Session Date": datetime.now().strftime("%Y-%m-%d"),
                    "Checklist Item": item,
                    "Status": "Pending",
                    "Remarks": "This is a sample entry. Add your own faculty from 'Manage Faculty' section.",
                    "Last Updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "Updated By": "System"
                })

        df = pd.DataFrame(records)
        df.to_csv(DATA_FILE, index=False)

def load_data():
    try:
        # Check if file exists and is not empty
        if not os.path.exists(DATA_FILE) or os.path.getsize(DATA_FILE) == 0:
            raise ValueError("File does not exist or is empty")
            
        df = pd.read_csv(DATA_FILE)
        
        # Check if dataframe is empty
        if df.empty or len(df.columns) == 0:
            raise ValueError("Empty CSV file")
        
        # Add Owner column if it doesn't exist (for backward compatibility)
        if "Owner" not in df.columns:
            df["Owner"] = "admin"
            
        # Add new columns if they don't exist (for backward compatibility)
        if "Last Updated" not in df.columns:
            df["Last Updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if "Updated By" not in df.columns:
            df["Updated By"] = "System"
        return df
        
    except (pd.errors.EmptyDataError, ValueError, FileNotFoundError) as e:
        # If file is empty or corrupted, delete it and reinitialize
        if os.path.exists(DATA_FILE):
            os.remove(DATA_FILE)
        initialize_data(force=True)
        # Load the newly created data
        df = pd.read_csv(DATA_FILE)
        return df

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

def add_new_faculty(owner, name, designation, session_name, session_date):
    df = load_data()

    if name.strip() == "":
        return "Name cannot be empty", None

    # Check if faculty with same name and date already exists for this owner
    existing = df[(df["Owner"] == owner) & (df["Name"] == name.strip()) & (df["Session Date"] == str(session_date))]
    if not existing.empty:
        return "Faculty with this name and session date already exists", None

    checklist_items = df["Checklist Item"].unique()

    new_records = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for item in checklist_items:
        new_records.append({
            "Owner": owner,
            "Name": name.strip(),
            "Designation": designation.strip(),
            "Session Name": session_name.strip(),
            "Session Date": str(session_date),
            "Checklist Item": item,
            "Status": "Pending",
            "Remarks": "",
            "Last Updated": timestamp,
            "Updated By": owner
        })

    new_df = pd.DataFrame(new_records)
    df = pd.concat([df, new_df], ignore_index=True)
    save_data(df)
    return "Success", df

def delete_faculty(owner, name, session_date):
    df = load_data()
    df = df[~((df["Owner"] == owner) & (df["Name"] == name) & (df["Session Date"] == session_date))]
    save_data(df)
    return df

def edit_faculty(owner, old_name, old_session_date, new_name, new_designation, new_session_name, new_session_date):
    df = load_data()
    
    if new_name.strip() == "":
        return "Name cannot be empty", None
    
    # Check if new combination already exists (excluding current faculty)
    existing = df[
        (df["Owner"] == owner) &
        (df["Name"] == new_name.strip()) &
        (df["Session Date"] == str(new_session_date)) &
        ~((df["Name"] == old_name) & (df["Session Date"] == old_session_date))
    ]
    
    if not existing.empty:
        return "Faculty with this name and session date already exists", None
    
    mask = (df["Owner"] == owner) & (df["Name"] == old_name) & (df["Session Date"] == old_session_date)
    
    if df[mask].empty:
        return "Faculty not found", None
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df.loc[mask, "Name"] = new_name.strip()
    df.loc[mask, "Designation"] = new_designation.strip()
    df.loc[mask, "Session Name"] = new_session_name.strip()
    df.loc[mask, "Session Date"] = str(new_session_date)
    df.loc[mask, "Last Updated"] = timestamp
    df.loc[mask, "Updated By"] = owner
    
    save_data(df)
    return "Success", df

def export_to_excel(df, filename="faculty_checklist_export.xlsx"):
    """Export data to Excel with formatting"""
    output_path = filename
    
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
    faculty_list = df[["Owner", "Name", "Session Date", "Designation", "Session Name"]].drop_duplicates()
    
    summary = []
    for _, faculty in faculty_list.iterrows():
        faculty_data = df[
            (df["Owner"] == faculty["Owner"]) &
            (df["Name"] == faculty["Name"]) &
            (df["Session Date"] == faculty["Session Date"])
        ]
        
        total_items = len(faculty_data)
        done = len(faculty_data[faculty_data["Status"] == "Done"])
        pending = len(faculty_data[faculty_data["Status"] == "Pending"])
        na = len(faculty_data[faculty_data["Status"] == "NA"])
        
        progress = (done / total_items * 100) if total_items > 0 else 0
        
        summary.append({
            "Owner": faculty["Owner"],
            "Name": faculty["Name"],
            "Designation": faculty["Designation"],
            "Session Name": faculty["Session Name"],
            "Session Date": faculty["Session Date"],
            "Total Items": total_items,
            "Done": done,
            "Pending": pending,
            "N/A": na,
            "Progress %": round(progress, 1)
        })
    
    return pd.DataFrame(summary)

# -----------------------------
# SESSION STATE INITIALIZATION
# -----------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'full_name' not in st.session_state:
    st.session_state.full_name = None

# Initialize data files
initialize_users()
initialize_data()

# -----------------------------
# LOGIN PAGE
# -----------------------------
def show_login_page():
    st.markdown('<p class="main-header">🔐 Guest Faculty Checklist System</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown("### Login to Continue")
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("🔓 Login", type="primary", use_container_width=True):
                if username and password:
                    success, role, full_name = authenticate_user(username, password)
                    
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.role = role
                        st.session_state.full_name = full_name
                        st.success(f"Welcome, {full_name}!")
                        st.rerun()
                    else:
                        if full_name:  # Contains error message
                            st.error(full_name)
                        else:
                            st.error("Invalid username or password")
                else:
                    st.error("Please enter both username and password")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.info("**Default Admin Credentials:**\n\nUsername: `admin`\n\nPassword: `admin123`")

# -----------------------------
# ADMIN USER MANAGEMENT (only shown if admin)
# -----------------------------
def show_admin_user_management():
    st.markdown('<p class="main-header">👑 User Management</p>', unsafe_allow_html=True)
    
    tab1, tab2, tab3, tab4 = st.tabs(["➕ Add User", "✏️ Edit User", "📋 View Users", "📊 User Statistics"])
    
    # TAB 1: ADD USER
    with tab1:
        st.markdown("### Add New User")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Username*", key="new_user_username")
            new_full_name = st.text_input("Full Name*", key="new_user_fullname")
            new_role = st.selectbox("Role*", ["user", "admin"], key="new_user_role")
        
        with col2:
            new_password = st.text_input("Password*", type="password", key="new_user_password")
            new_email = st.text_input("Email*", key="new_user_email")
        
        if st.button("➕ Add User", type="primary"):
            if all([new_username, new_password, new_full_name, new_email]):
                success, message = add_user(new_username, new_password, new_role, new_full_name, new_email)
                if success:
                    st.success(message)
                else:
                    st.error(message)
            else:
                st.error("Please fill all required fields")
    
    # TAB 2: EDIT USER
    with tab2:
        users_df = load_users()
        
        st.markdown("### Edit User")
        
        edit_username = st.selectbox(
            "Select User to Edit",
            users_df['username'].tolist(),
            key="edit_user_select"
        )
        
        user_data = users_df[users_df['username'] == edit_username].iloc[0]
        
        col1, col2 = st.columns(2)
        
        with col1:
            edit_full_name = st.text_input("Full Name", value=user_data['full_name'], key="edit_user_fullname")
            edit_email = st.text_input("Email", value=user_data['email'], key="edit_user_email")
        
        with col2:
            edit_password = st.text_input("New Password (leave blank to keep current)", type="password", key="edit_user_password")
            edit_active = st.checkbox("Active", value=bool(user_data['active']), key="edit_user_active")
        
        if st.button("💾 Update User", type="primary"):
            success, message = update_user(
                edit_username,
                full_name=edit_full_name,
                email=edit_email,
                password=edit_password if edit_password else None,
                active=edit_active
            )
            if success:
                st.success(message)
            else:
                st.error(message)
    
    # TAB 3: VIEW USERS
    with tab3:
        st.markdown("### All Users")
        
        users_df = load_users()
        display_df = users_df[['username', 'full_name', 'email', 'role', 'active', 'created_date']].copy()
        display_df.columns = ['Username', 'Full Name', 'Email', 'Role', 'Active', 'Created Date']
        
        st.dataframe(display_df, use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Delete User")
        st.warning("⚠️ This will delete the user and ALL their faculty data!")
        
        delete_username = st.selectbox(
            "Select User to Delete",
            [u for u in users_df['username'].tolist() if u != 'admin'],
            key="delete_user_select"
        )
        
        confirm_delete = st.checkbox("✅ I confirm deletion", key="confirm_user_delete")
        
        if st.button("🗑️ Delete User", type="primary", disabled=not confirm_delete):
            success, message = delete_user(delete_username)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    # TAB 4: USER STATISTICS
    with tab4:
        st.markdown("### User Statistics")
        
        users_df = load_users()
        df = load_data()
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Users", len(users_df))
        with col2:
            st.metric("Active Users", len(users_df[users_df['active'] == True]))
        with col3:
            st.metric("Admin Users", len(users_df[users_df['role'] == 'admin']))
        with col4:
            st.metric("Regular Users", len(users_df[users_df['role'] == 'user']))
        
        st.markdown("---")
        st.markdown("### Faculty by User")
        
        # Count faculty per user
        faculty_counts = df.groupby('Owner')[['Name', 'Session Date']].apply(
            lambda x: len(x.drop_duplicates())
        ).reset_index()
        faculty_counts.columns = ['User', 'Faculty Count']
        
        fig = px.bar(
            faculty_counts,
            x='User',
            y='Faculty Count',
            title='Number of Faculty per User',
            color='Faculty Count',
            color_continuous_scale='Blues'
        )
        st.plotly_chart(fig, use_container_width=True)

# =============================================================================
# MAIN APP - All original functionality preserved below
# =============================================================================

if not st.session_state.logged_in:
    show_login_page()
else:
    # Filter data for current user (admin sees all, users see only their own)
    current_user = st.session_state.username
    current_role = st.session_state.role
    
    # -----------------------------
    # INITIALIZE
    # -----------------------------
    if 'df' not in st.session_state:
        st.session_state.df = load_data()

    # Initialize success message state
    if 'success_message' not in st.session_state:
        st.session_state.success_message = None

    df = st.session_state.df
    
    # Filter data based on role
    if current_role != 'admin':
        df = df[df['Owner'] == current_user]

    # -----------------------------
    # SIDEBAR
    # -----------------------------
    st.sidebar.markdown(f"### Welcome, {st.session_state.full_name}!")
    st.sidebar.markdown(f"**Role:** {current_role.title()}")
    
    if st.sidebar.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.session_state.role = None
        st.session_state.full_name = None
        st.rerun()
    
    st.sidebar.markdown("---")
    st.sidebar.title("🎯 Navigation")

    # Admin gets extra menu option
    if current_role == 'admin':
        menu_options = ["📋 Checklist Management", "📊 Dashboard & Analytics", "👥 Manage Faculty", "👑 User Management"]
    else:
        menu_options = ["📋 Checklist Management", "📊 Dashboard & Analytics", "👥 Manage Faculty"]

    menu = st.sidebar.radio(
        "Select View",
        menu_options,
        label_visibility="collapsed"
    )

    st.sidebar.markdown("---")

    # Show admin user management if selected
    if menu == "👑 User Management":
        show_admin_user_management()
    
    # =============================================
    # VIEW 1: CHECKLIST MANAGEMENT
    # =============================================
    elif menu == "📋 Checklist Management":
        
        # Display success message if exists
        if st.session_state.success_message:
            st.success(st.session_state.success_message)
            st.session_state.success_message = None
        
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
                
                # Apply role-based filtering for non-admin users
                if current_role != 'admin':
                    mask = mask & (st.session_state.df["Owner"] == current_user)
                
                # Apply bulk action to all matching rows
                if bulk_action == "Mark All as Done":
                    st.session_state.df.loc[mask, "Status"] = "Done"
                elif bulk_action == "Mark All as Pending":
                    st.session_state.df.loc[mask, "Status"] = "Pending"
                elif bulk_action == "Clear All Remarks":
                    st.session_state.df.loc[mask, "Remarks"] = ""
                
                # Update timestamp and user for all affected rows
                st.session_state.df.loc[mask, "Last Updated"] = timestamp
                st.session_state.df.loc[mask, "Updated By"] = current_user
                
                save_data(st.session_state.df)
                st.session_state.success_message = f"✅ {bulk_action} applied successfully!"
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
                export_df = st.session_state.df if current_role == 'admin' else df
                filename = "all_faculty_checklist.xlsx"
            else:  # Summary Report
                export_df = get_faculty_summary(st.session_state.df if current_role == 'admin' else df)
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
                        st.session_state.df.at[idx, "Remarks"] = str(remarks) if remarks else ""
                        st.session_state.df.at[idx, "Last Updated"] = timestamp
                        st.session_state.df.at[idx, "Updated By"] = current_user
                    
                    save_data(st.session_state.df)
                    st.session_state.success_message = "✅ All updates saved successfully!"
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
            
            styled_df = summary_df.style.map(
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
        
        # Display success message if exists
        if st.session_state.success_message:
            st.success(st.session_state.success_message)
            st.session_state.success_message = None
        
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
                            current_user,  # Use current logged-in user as owner
                            new_name,
                            new_designation,
                            new_session_name,
                            new_session_date
                        )
                        
                        if result == "Success":
                            st.session_state.df = updated_df
                            st.session_state.success_message = f"✅ Faculty '{new_name}' added successfully!"
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
                                current_user,  # Use current logged-in user as owner
                                selected_row["Name"],
                                selected_row["Session Date"],
                                edit_name,
                                edit_designation,
                                edit_session_name,
                                edit_session_date
                            )
                            
                            if result == "Success":
                                st.session_state.df = updated_df
                                st.session_state.success_message = f"✅ Faculty details updated successfully!"
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
                                current_user,  # Use current logged-in user as owner
                                selected_row["Name"],
                                selected_row["Session Date"]
                            )
                            st.session_state.df = updated_df
                            st.session_state.success_message = f"✅ Faculty '{selected_row['Name']}' deleted successfully!"
                            st.rerun()


    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 1rem;'>
        <small>Guest Faculty Checklist Management System | Version 5.0 with Multi-User Login</small>
    </div>
    """, unsafe_allow_html=True)