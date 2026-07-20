import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Ministry MIS - Executive Dashboard", layout="wide")

# 2. SESSION STATE SETUP
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None

USERS = {
    "admin": {"password": "password123", "role": "Admin"},
    "officer": {"password": "officer123", "role": "Officer"},
    "viewer": {"password": "viewer123", "role": "Viewer"}
}

# 3. LOGIN LOGIC
if not st.session_state['authenticated']:
    st.title("🔒 Ministry Portal Login")
    st.write("Please enter your credentials to access the Dashboard.")
    
    user_input = st.text_input("Username")
    pass_input = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if user_input in USERS and USERS[user_input]["password"] == pass_input:
            st.session_state['authenticated'] = True
            st.session_state['username'] = user_input
            st.session_state['role'] = USERS[user_input]["role"]
            st.rerun()
        else:
            st.error("Invalid username or password")
            
    st.stop()

# --- SIDEBAR USER INFO & LOGOUT ---
st.sidebar.markdown(f"**👤 User:** {st.session_state['username']}")
st.sidebar.markdown(f"**🛡️ Role:** {st.session_state['role']}")
if st.sidebar.button("Logout"):
    st.session_state['authenticated'] = False
    st.session_state['role'] = None
    st.session_state['username'] = None
    st.rerun()

st.sidebar.markdown("---")

# 4. DASHBOARD CONTENT (Authenticated)
st.title("🏛️ Ministry of Public Works: Executive Dashboard")

try:
    conn = sqlite3.connect('nyeri_public_works.db')
    df = pd.read_sql("SELECT * FROM ProjectRegistry", conn)
    conn.close()
    
    if not df.empty:
        # Smart detect columns
        budget_col = next((col for col in df.columns if any(term in col.lower() for term in ['budget', 'cost', 'amount', 'allocation'])), None)
        dept_col = next((c for c in df.columns if 'dept' in c.lower() or 'department' in c.lower()), None)
        status_col = next((c for c in df.columns if 'status' in c.lower()), None)
        name_col = next((c for c in df.columns if 'name' in c.lower()), df.columns[0])
                
        # --- SIDEBAR FILTERS ---
        st.sidebar.header("🔍 Filter Dashboard")
        
        selected_dept = "All"
        if dept_col:
            departments = ["All"] + sorted(df[dept_col].dropna().unique().tolist())
            selected_dept = st.sidebar.selectbox("Department Assigned", departments)
        
        selected_status = "All"
        if status_col:
            statuses = ["All"] + sorted(df[status_col].dropna().unique().tolist())
            selected_status = st.sidebar.selectbox("Current Status", statuses)
        
        # Apply Filters
        filtered_df = df.copy()
        if dept_col and selected_dept != "All":
            filtered_df = filtered_df[filtered_df[dept_col] == selected_dept]
        if status_col and selected_status != "All":
            filtered_df = filtered_df[filtered_df[status_col] == selected_status]
            
        # --- KPI METRICS ---
        st.subheader(f"Executive Summary ({len(filtered_df)} Projects Displayed)")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        
        total_proj = len(filtered_df)
        active_proj = len(filtered_df[filtered_df[status_col] == 'Active']) if status_col and 'Active' in filtered_df[status_col].values else 0
        pending_proj = len(filtered_df[filtered_df[status_col] == 'Pending']) if status_col and 'Pending' in filtered_df[status_col].values else 0
        total_budget = pd.to_numeric(filtered_df[budget_col], errors='coerce').sum() if budget_col else 0.0
        
        kpi1.metric("Filtered Projects", total_proj)
        kpi2.metric("Active Projects", active_proj)
        kpi3.metric("Pending Projects", pending_proj)
        kpi4.metric("Total Budget Allocated", f"KES {total_budget:,.2f}")
        
        # --- INTERACTIVE PLOTLY CHARTS ---
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.subheader("📊 Departmental Overview")
            if dept_col and not filtered_df.empty:
                # Prepare aggregated dataset explicitly for version safety
                dept_counts = filtered_df[dept_col].value_counts().reset_index()
                dept_counts.columns = ['Department', 'Count']
                
                fig_dept = px.bar(
                    dept_counts,
                    x='Department', y='Count',
                    labels={'Department': 'Department', 'Count': 'Project Count'},
                    color='Count',
                    color_continuous_scale='Blues'  # Fixed camelCase typo
                )
                fig_dept.update_layout(xaxis_tickangle=-45, showlegend=False, margin=dict(t=20, b=20))
                st.plotly_chart(fig_dept, use_container_width=True)
            else:
                st.info("No department data available.")
                
        with col_right:
            st.subheader("🍩 Status Distribution")
            if status_col and not filtered_df.empty:
                fig_status = px.pie(
                    filtered_df, names=status_col, 
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Tealgrn
                )
                fig_status.update_layout(margin=dict(t=20, b=20))
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("No status data available.")
                
        # --- BUDGET COMPLIANCE & HIGH-VALUE PROJECTS ---
        st.subheader("⚠️ High-Value Budget Oversight")
        if budget_col and not filtered_df.empty:
            temp_df = filtered_df.copy()
            temp_df[budget_col] = pd.to_numeric(temp_df[budget_col], errors='coerce').fillna(0)
            top_budget = temp_df.sort_values(by=budget_col, ascending=False).head(5)
            cols_to_show = [c for c in [name_col, dept_col, status_col, budget_col] if c in top_budget.columns]
            st.dataframe(top_budget[cols_to_show], use_container_width=True)
        else:
            st.info("No budget data column found.")
                
        # --- FULL FILTERED TABLE ---
        st.subheader("Project Details Table")
        st.dataframe(filtered_df, use_container_width=True)
        
    else:
        st.info("The database is currently empty. Please add projects using the Registry page.")

except Exception as e:
    st.error(f"Could not load data: {e}")