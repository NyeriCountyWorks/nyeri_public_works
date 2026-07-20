import streamlit as st
import sqlite3
import pandas as pd
import io
import os
from datetime import datetime

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Project Registry - Ministry MIS", layout="wide")

# 2. SECURITY & AUTHENTICATION CHECK
if 'authenticated' not in st.session_state or not st.session_state['authenticated']:
    st.error("🔒 Access Denied. Please log in from the main Executive Dashboard first.")
    if st.button("🔑 Go to Login Page"):
        st.switch_page("app.py")
    st.stop()

username = st.session_state.get('username', 'Unknown')
role = st.session_state.get('role', 'Viewer')

# 3. SIDEBAR USER INFO & LOGOUT
st.sidebar.markdown(f"**👤 User:** {username}")
st.sidebar.markdown(f"**🛡️ Role:** {role}")
if st.sidebar.button("Logout"):
    st.session_state['authenticated'] = False
    st.session_state['role'] = None
    st.session_state['username'] = None
    st.rerun()

st.sidebar.markdown("---")

st.title("📂 Project Registry & Governance")

# 4. DATABASE & FILE UPLOAD SETUP
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

conn = sqlite3.connect('nyeri_public_works.db')
cursor = conn.cursor()

# --- DYNAMIC SCHEMA MIGRATION ---
columns_to_ensure = [
    ("tracking_number", "TEXT"),
    ("sub_county_ward", "TEXT"),
    ("budget", "REAL"),
    ("attachment", "TEXT"),
    ("department_assigned", "TEXT"),
    ("current_status", "TEXT")
]

for col_name, col_type in columns_to_ensure:
    try:
        cursor.execute(f"ALTER TABLE ProjectRegistry ADD COLUMN {col_name} {col_type};")
        conn.commit()
    except sqlite3.OperationalError:
        pass  # Column already exists

# Ensure AuditLog table exists
cursor.execute("""
    CREATE TABLE IF NOT EXISTS AuditLog (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        username TEXT,
        role TEXT,
        action TEXT,
        project_name TEXT,
        details TEXT
    )
""")
conn.commit()

# Audit log helper
def log_audit_event(action, project_name, details=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO AuditLog (timestamp, username, role, action, project_name, details)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (timestamp, username, role, action, project_name, details))
    conn.commit()

# Fetch latest project data
try:
    df = pd.read_sql("SELECT rowid as id, * FROM ProjectRegistry", conn)
except Exception:
    try:
        df = pd.read_sql("SELECT * FROM ProjectRegistry", conn)
    except:
        df = pd.DataFrame()

# 5. DYNAMIC TABS BASED ON USER ROLE
if role == "Admin":
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📋 View Registry", "➕ Add Project", "✏️ Edit Project", 
        "🗑️ Delete Project", "📥 Export Reports", "📜 Audit Trail"
    ])
elif role == "Officer":
    tab1, tab2, tab3, tab5, tab6 = st.tabs([
        "📋 View Registry", "➕ Add Project", "✏️ Edit Project", 
        "📥 Export Reports", "📜 Audit Trail"
    ])
    tab4 = None
else: # Viewer
    tab1, tab5 = st.tabs(["📋 View Registry", "📥 Export Reports"])
    tab2, tab3, tab4, tab6 = None, None, None, None

# --- TAB 1: VIEW REGISTRY & LIVE SEARCH ---
with tab1:
    st.subheader("All Registered Projects")
    
    if not df.empty:
        search_query = st.text_input(
            "🔍 Live Search Projects", 
            placeholder="Type project name, tracking number, ward, status, or department..."
        ).strip()
        
        if search_query:
            mask = df.astype(str).apply(
                lambda row: row.str.contains(search_query, case=False, na=False)
            ).any(axis=1)
            display_df = df[mask]
            st.caption(f"Showing **{len(display_df)}** of **{len(df)}** total projects matching '{search_query}'")
        else:
            display_df = df
            st.caption(f"Showing all **{len(df)}** registered projects")
            
        st.dataframe(display_df, use_container_width=True)
        
        # Project Attachment Previewer
        if 'attachment' in df.columns:
            st.markdown("---")
            st.subheader("📎 Project Attachment Viewer")
            proj_with_files = df[df['attachment'].notna() & (df['attachment'] != "")]
            if not proj_with_files.empty:
                selected_file_proj = st.selectbox("Select Project to Inspect Attachment", proj_with_files['project_name'].tolist())
                file_row = proj_with_files[proj_with_files['project_name'] == selected_file_proj].iloc[0]
                filename = file_row['attachment']
                file_path = os.path.join(UPLOAD_DIR, filename)
                
                if os.path.exists(file_path):
                    st.write(f"**Filename:** `{filename}`")
                    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                        st.image(file_path, caption=f"Site Photo: {selected_file_proj}", use_container_width=True)
                    else:
                        st.download_button(
                            label=f"📥 Download {filename}",
                            data=open(file_path, "rb").read(),
                            file_name=filename
                        )
                else:
                    st.warning("File record found, but the file is missing from local storage.")
            else:
                st.info("No projects currently have file attachments.")
    else:
        st.info("No projects found in the registry.")

# --- TAB 2: ADD PROJECT (Admin & Officer) ---
if tab2 is not None:
    with tab2:
        st.subheader("Add a New Project & Attachments")
        
        # Auto-generate tracking number default
        next_id = len(df) + 1 if not df.empty else 1
        auto_tracking = f"NYR-PW-2026-{next_id:03d}"
        
        with st.form("add_project_form"):
            c1, c2 = st.columns(2)
            with c1:
                tracking_number = st.text_input("Tracking Number", value=auto_tracking)
                project_name = st.text_input("Project Name")
                sub_county_ward = st.text_input("Sub-County / Ward", value="Mathira East")
            with c2:
                department = st.selectbox("Department Assigned", ["Civil Works", "Electrical", "Mechanical", "Administration", "Roads", "Roads & Infrastructure"])
                status = st.selectbox("Current Status", ["Active", "Pending", "Completed", "Stalled"])
                budget = st.number_input("Budget Allocated (KES)", min_value=0.0, step=10000.0)
            
            uploaded_file = st.file_uploader("Attach Site Photo / Document (PDF, PNG, JPG, XLSX)")
            
            submit_add = st.form_submit_button("Save Project")
            if submit_add:
                if project_name:
                    filename = None
                    if uploaded_file is not None:
                        filename = uploaded_file.name
                        save_path = os.path.join(UPLOAD_DIR, filename)
                        with open(save_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                    
                    try:
                        # Inspect actual database columns dynamically
                        cursor.execute("PRAGMA table_info(ProjectRegistry)")
                        db_cols = [row[1] for row in cursor.fetchall()]
                        
                        data_map = {
                            "tracking_number": tracking_number,
                            "project_name": project_name,
                            "sub_county_ward": sub_county_ward,
                            "department_assigned": department,
                            "current_status": status,
                            "budget": budget,
                            "attachment": filename
                        }
                        
                        # Build query using only valid columns that exist in the target table
                        valid_map = {k: v for k, v in data_map.items() if k in db_cols}
                        col_names = ", ".join(valid_map.keys())
                        placeholders = ", ".join(["?"] * len(valid_map))
                        values = list(valid_map.values())
                        
                        insert_query = f"INSERT INTO ProjectRegistry ({col_names}) VALUES ({placeholders})"
                        cursor.execute(insert_query, values)
                        conn.commit()
                        
                        # Audit Log Entry
                        log_audit_event("CREATE", project_name, f"Tracking: {tracking_number}, Dept: {department}, Budget: KES {budget:,.2f}")
                        
                        st.success(f"Project '{project_name}' ({tracking_number}) registered successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error adding project: {e}")
                else:
                    st.error("Please enter a project name.")

# --- TAB 3: EDIT PROJECT (Admin & Officer) ---
if tab3 is not None:
    with tab3:
        st.subheader("Edit Existing Project")
        if not df.empty:
            project_options = df['project_name'].tolist() if 'project_name' in df.columns else []
            selected_proj = st.selectbox("Select Project to Modify", project_options)
            
            if selected_proj:
                proj_row = df[df['project_name'] == selected_proj].iloc[0]
                
                with st.form("edit_project_form"):
                    new_name = st.text_input("Project Name", value=str(proj_row.get('project_name', '')))
                    
                    depts = ["Civil Works", "Electrical", "Mechanical", "Administration", "Roads", "Roads & Infrastructure"]
                    current_dept = str(proj_row.get('department_assigned', depts[0]))
                    dept_idx = depts.index(current_dept) if current_dept in depts else 0
                    new_dept = st.selectbox("Department Assigned", depts, index=dept_idx)
                    
                    statuses = ["Active", "Pending", "Completed", "Stalled"]
                    current_status = str(proj_row.get('current_status', statuses[0]))
                    status_idx = statuses.index(current_status) if current_status in statuses else 0
                    new_status = st.selectbox("Current Status", statuses, index=status_idx)
                    
                    current_budget = float(proj_row.get('budget', 0.0) if proj_row.get('budget') is not None else 0.0)
                    new_budget = st.number_input("Budget Allocated (KES)", value=current_budget, min_value=0.0, step=10000.0)
                    
                    submit_edit = st.form_submit_button("Update Project Details")
                    if submit_edit:
                        try:
                            if 'id' in df.columns:
                                proj_id = proj_row['id']
                                cursor.execute("""
                                    UPDATE ProjectRegistry 
                                    SET project_name = ?, department_assigned = ?, current_status = ?, budget = ?
                                    WHERE rowid = ?
                                """, (new_name, new_dept, new_status, new_budget, proj_id))
                            else:
                                cursor.execute("""
                                    UPDATE ProjectRegistry 
                                    SET department_assigned = ?, current_status = ?, budget = ?
                                    WHERE project_name = ?
                                """, (new_dept, new_status, new_budget, new_name))
                            conn.commit()
                            
                            # Audit Log Entry
                            log_audit_event("UPDATE", new_name, f"Updated status to {new_status}, Dept: {new_dept}, Budget: KES {new_budget:,.2f}")
                            
                            st.success(f"Project '{new_name}' updated successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error updating project: {e}")
        else:
            st.info("No projects available to edit.")

# --- TAB 4: DELETE PROJECT (Admin Only) ---
if tab4 is not None:
    with tab4:
        st.subheader("⚠️ Delete Project")
        if not df.empty:
            project_options_del = df['project_name'].tolist() if 'project_name' in df.columns else []
            selected_del = st.selectbox("Select Project to Permanently Delete", project_options_del, key="delete_select")
            
            if st.button("Delete Selected Project", type="primary"):
                try:
                    if 'id' in df.columns:
                        proj_id = df[df['project_name'] == selected_del]['id'].values[0]
                        cursor.execute("DELETE FROM ProjectRegistry WHERE rowid = ?", (proj_id,))
                    else:
                        cursor.execute("DELETE FROM ProjectRegistry WHERE project_name = ?", (selected_del,))
                    conn.commit()
                    
                    # Audit Log Entry
                    log_audit_event("DELETE", selected_del, "Project removed from database registry")
                    
                    st.success(f"Project '{selected_del}' deleted successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting project: {e}")
        else:
            st.info("No projects available to delete.")

# --- TAB 5: EXPORT REPORTS (All Roles) ---
with tab5:
    st.subheader("📥 Downloadable Reports")
    if not df.empty:
        st.write("Export official registry files for external auditing and record-keeping.")
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="Download CSV Report",
                data=csv_data,
                file_name="nyeri_public_works_registry.csv",
                mime="text/csv"
            )
            
        with col2:
            try:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    df.to_excel(writer, index=False, sheet_name='Project Registry')
                excel_data = output.getvalue()
                
                st.download_button(
                    label="Download Excel (.xlsx) Report",
                    data=excel_data,
                    file_name="nyeri_public_works_registry.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except Exception as e:
                st.info("Excel export requires 'openpyxl'.")
    else:
        st.info("No data available to export.")

# --- TAB 6: AUDIT TRAIL LOG ---
if tab6 is not None:
    with tab6:
        st.subheader("📜 System Governance & Audit Log")
        st.write("Real-time chronological record of all database modifications.")
        
        audit_df = pd.read_sql("SELECT * FROM AuditLog ORDER BY id DESC", conn)
        
        if not audit_df.empty:
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Logged Actions", len(audit_df))
            m2.metric("Latest Action", audit_df.iloc[0]['action'] if 'action' in audit_df.columns else "N/A")
            m3.metric("Last User", audit_df.iloc[0]['username'] if 'username' in audit_df.columns else "N/A")
            
            st.markdown("---")
            st.dataframe(audit_df, use_container_width=True)
        else:
            st.info("No audit logs recorded yet. Perform an Add, Edit, or Delete action to generate activity logs.")

conn.close()