import base64
import datetime
import os
import sqlite3
import textwrap
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st


# --- 1. ENTERPRISE DATABASE & AUDIT HELPERS ---
def init_enterprise_db():
    """Initializes the database with tables for projects, documents, workflows, and audits, and seeds sample data."""
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'Viewer'
            )
        ''')

        # Insert default administrative accounts if empty
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('admin', 'admin123', 'System Administrator', 'Admin')")
            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('engineer', 'eng123', 'Lead Engineer', 'Engineer')")
            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('director', 'dir123', 'Public Works Director', 'Director')")
            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('chief', 'chief123', 'Chief Officer', 'Chief Officer')")

        # 2. Projects Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT UNIQUE,
                project_name TEXT NOT NULL,
                sub_county TEXT,
                department TEXT,
                budget_allocated REAL,
                actual_spend REAL DEFAULT 0.0,
                percentage_complete INTEGER DEFAULT 0,
                workflow_stage TEXT DEFAULT 'Draft', 
                status TEXT DEFAULT 'Active',
                created_by TEXT,
                last_updated DATETIME
            )
        ''')

        # Seed sample Nyeri County projects if table is empty
        cursor.execute("SELECT COUNT(*) FROM projects")
        if cursor.fetchone()[0] == 0:
            sample_projects = [
                ("PRJ-2026-001", "Karatina Market Modernization & Drainage", "Mathira East", "Infrastructure & Energy", 45000000.0, 38000000.0, 85, "In Progress", "Active", "admin", "2026-01-10 09:00:00"),
                ("PRJ-2026-002", "Othaya Sub-County Hospital Wing Extension", "Othaya", "Public Works", 60000000.0, 60000000.0, 100, "Completed", "Completed", "director", "2026-02-14 11:30:00"),
                ("PRJ-2026-003", "Tetu High-Altitude Training Water Pipeline", "Tetu", "Water & Sanitation", 18500000.0, 12000000.0, 65, "In Progress", "Active", "engineer", "2026-03-01 14:15:00"),
                ("PRJ-2026-004", "Mukurwe-ini Feeder Roads Tarmacking", "Mukurweini", "Roads & Transport", 82000000.0, 25000000.0, 30, "Review", "Delayed", "engineer", "2026-03-20 10:45:00"),
                ("PRJ-2026-005", "Nyeri Town Bus Park Stormwater System", "Nyeri Town", "Public Works", 12000000.0, 1500000.0, 15, "Draft", "Active", "admin", "2026-04-05 16:20:00"),
                ("PRJ-2026-006", "Kieni East Earth Dam Rehabilitation", "Kieni East", "Water & Sanitation", 35000000.0, 32000000.0, 90, "Approved", "Active", "chief", "2026-05-12 08:50:00")
            ]
            cursor.executemany("""
                INSERT INTO projects 
                (project_code, project_name, sub_county, department, budget_allocated, actual_spend, percentage_complete, workflow_stage, status, created_by, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_projects)

        # 3. Document Management Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT,
                filename TEXT,
                file_path TEXT,
                uploaded_by TEXT,
                upload_timestamp DATETIME
            )
        ''')

        # 4. Audit Trail Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                username TEXT,
                action TEXT,
                target_record TEXT,
                details TEXT
            )
        ''')

        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database Initialization error: {e}")

def log_audit_action(username, action, target, details=""):
    """Helper function to record actions in the audit trail."""
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO audit_logs (timestamp, username, action, target_record, details) VALUES (?, ?, ?, ?, ?)",
            (timestamp, username, action, target, details)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Audit log failed: {e}")

def verify_login(username, password):
    """Verify user credentials against SQLite database."""
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT username, password, full_name, role FROM users WHERE LOWER(username) = LOWER(?)",
            (username.strip(),),
        )
        row = cursor.fetchone()
        conn.close()

        if row and str(row[1]) == str(password):
            return {
                "username": row[0],
                "full_name": row[2] if row[2] else row[0],
                "role": row[3] if row[3] else "Viewer",
            }
    except Exception:
        pass
    return None

def register_user(username, password, full_name, role="Viewer"):
    """Register a new user in the SQLite database."""
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)",
            (username.strip(), password, full_name.strip(), role),
        )
        conn.commit()
        conn.close()
        
        log_audit_action(username, "Registration", "System", f"Account created with role: {role}")
        return True, "🎉 Account created successfully! You can now log in."
    except sqlite3.IntegrityError:
        return False, "⚠️ Username already exists. Please pick a different username."
    except Exception as e:
        return False, f"Registration error: {e}"


# --- 2. TIME-BASED GREETING HELPER ---
def get_time_greeting():
    hour = datetime.datetime.now().hour
    if hour < 12:
        return "Good morning"
    elif hour < 17:
        return "Good afternoon"
    else:
        return "Good evening"


# --- 3. NYERI COUNTY SEAL VECTOR FALLBACK ---
NYERI_SEAL_FALLBACK_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" width="130" height="130" style="display: block; margin: 0 auto; filter: drop-shadow(0px 6px 12px rgba(0,0,0,0.35));">
  <defs>
    <path id="textCirclePath" d="M 50,250 A 200,200 0 1,1 450,250 A 200,200 0 1,1 50,250" fill="none" />
    <path id="bottomTextCirclePath" d="M 410,250 A 160,160 0 0,1 90,250" fill="none" />
    <linearGradient id="shieldSky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#3498db" />
      <stop offset="100%" stop-color="#1abc9c" />
    </linearGradient>
    <linearGradient id="goldGradient" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFF3B0" />
      <stop offset="50%" stop-color="#D4AF37" />
      <stop offset="100%" stop-color="#AA7C11" />
    </linearGradient>
  </defs>

  <circle cx="250" cy="250" r="235" fill="#FFFFFF" stroke="url(#goldGradient)" stroke-width="6" />
  <circle cx="250" cy="250" r="218" fill="#4CAF50" stroke="#0A4D20" stroke-width="4.5" />
  <circle cx="250" cy="250" r="175" fill="#FFFFFF" stroke="url(#goldGradient)" stroke-width="3" />

  <text font-family="'Poppins', 'Inter', sans-serif" font-size="28" font-weight="900" fill="#FFFFFF" letter-spacing="4">
    <textPath href="#textCirclePath" startOffset="25%" text-anchor="middle">COUNTY GOVERNMENT OF NYERI</textPath>
  </text>

  <g transform="translate(0, -10)">
    <path d="M 180,120 Q 250,110 320,120 Q 320,240 250,300 Q 180,240 180,120 Z" fill="#FFFFFF" stroke="url(#goldGradient)" stroke-width="5" />
    <clipPath id="shieldClip">
      <path d="M 183,123 Q 250,113 317,123 Q 317,237 250,295 Q 183,237 183,123 Z" />
    </clipPath>
    <g clip-path="url(#shieldClip)">
      <rect x="150" y="90" width="200" height="100" fill="url(#shieldSky)" />
      <polygon points="250,105 185,185 315,185" fill="#2c3e50" />
      <polygon points="250,105 225,140 250,135 275,140" fill="#FFFFFF" />
      <rect x="150" y="180" width="200" height="60" fill="#8bc34a" stroke="#ffffff" stroke-width="2" />
      <circle cx="250" cy="210" r="7" fill="#e74c3c" />
      <rect x="150" y="235" width="200" height="70" fill="#f39c12" />
    </g>
  </g>

  <path d="M 90,340 Q 250,390 410,340 L 390,390 Q 250,440 110,390 Z" fill="#2980b9" stroke="url(#goldGradient)" stroke-width="3" />
  <text font-family="'Poppins', 'Inter', sans-serif" font-size="20" font-weight="bold" fill="#FFFFFF" letter-spacing="1.5">
    <textPath href="#bottomTextCirclePath" startOffset="50%" text-anchor="middle">Ndaragwa na Maitu</textPath>
  </text>
</svg>"""

def get_nyeri_seal_element():
    if os.path.exists("seal.png"):
        try:
            with open("seal.png", "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            return f'<img src="data:image/png;base64,{encoded_string}" alt="Nyeri County Seal" style="display: block; margin: 0 auto; width: 130px; height: 130px; border-radius: 50%; border: 3px solid #D4AF37;">'
        except Exception:
            pass
    return NYERI_SEAL_FALLBACK_SVG

def inject_custom_styles():
    st.markdown(
        """
    <style>
        [data-testid="stSidebar"] {
            background-color: #0A4D20 !important;
            background-image: linear-gradient(180deg, #0A4D20 0%, #041f0d 100%) !important;
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] span, 
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] h4, 
        [data-testid="stSidebar"] h5, 
        [data-testid="stSidebar"] h6,
        [data-testid="stSidebar"] label {
            color: #FFFFFF !important;
            font-family: 'Poppins', sans-serif;
        }
        [data-testid="stSidebar"] strong {
            color: #D4AF37 !important;
        }
        /* Fix sidebar button text contrast */
        [data-testid="stSidebar"] button {
            background-color: #FFFFFF !important;
            border: 2px solid #D4AF37 !important;
            border-radius: 20px !important;
            font-weight: bold !important;
            width: 100% !important;
        }
        [data-testid="stSidebar"] button p, 
        [data-testid="stSidebar"] button span, 
        [data-testid="stSidebar"] button div {
            color: #0A4D20 !important;
            font-weight: 700 !important;
        }
        [data-testid="stSidebar"] button:hover {
            background-color: #D4AF37 !important;
            border-color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] button:hover p, 
        [data-testid="stSidebar"] button:hover span, 
        [data-testid="stSidebar"] button:hover div {
            color: #041f0d !important;
        }
        div[data-testid="stMetricValue"] {
            color: #0A4D20 !important;
            font-weight: 700 !important;
            font-size: 1.5rem !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


# --- 4. APP INITIALIZATION ---
st.set_page_config(
    page_title="Ministry MIS - Executive Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_custom_styles()
init_enterprise_db()

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

# --- 5. AUTHENTICATION (LOGIN & SIGN UP SCREEN) ---
if not st.session_state["authenticated"]:
    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        st.markdown(get_nyeri_seal_element(), unsafe_allow_html=True)

    st.markdown(
        "<h1 style='text-align: center; color: #0A4D20;'>🏛️ County Government of Nyeri</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h3 style='text-align: center; color: #D4AF37; margin-top: -15px;'>Public Works & Infrastructure MIS Portal</h3>",
        unsafe_allow_html=True,
    )

    if st.session_state.get("show_goodbye", False):
        last_user = st.session_state.get("last_username", "User")
        st.success(f"👋 Goodbye, **{last_user}**! You have been logged out securely. Have a great day!")
        st.session_state["show_goodbye"] = False

    _, auth_col, _ = st.columns([1, 1.8, 1])
    with auth_col:
        tab_login, tab_signup = st.tabs(["🔒 Sign In", "📝 Create Account"])

        with tab_login:
            with st.form("login_form"):
                user_input = st.text_input("Username")
                pass_input = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Sign In Securely", use_container_width=True)

                if submitted:
                    user_data = verify_login(user_input, pass_input)
                    if user_data:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = user_data["username"]
                        st.session_state["role"] = user_data["role"]
                        st.session_state["full_name"] = user_data["full_name"]
                        st.session_state["just_logged_in"] = True
                        
                        log_audit_action(user_data["username"], "Login", "System", "User logged in successfully")
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

        with tab_signup:
            with st.form("signup_form"):
                new_fullname = st.text_input("Full Name (e.g., Jane Doe)")
                new_username = st.text_input("Choose Username")
                new_password = st.text_input("Choose Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
                new_role = st.selectbox(
                    "Access Role",
                    ["Viewer", "Engineer", "Director", "Chief Officer", "Admin"],
                )

                signup_submitted = st.form_submit_button("Register New Account", use_container_width=True)

                if signup_submitted:
                    if not new_fullname.strip() or not new_username.strip() or not new_password:
                        st.warning("Please fill in all required fields.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match. Please re-enter.")
                    elif len(new_password) < 4:
                        st.error("Password must be at least 4 characters long.")
                    else:
                        success, msg = register_user(new_username, new_password, new_fullname, new_role)
                        if success:
                            st.success(msg)
                            st.info("👈 Switch to the **Sign In** tab to log in.")
                        else:
                            st.error(msg)

    st.stop()

# --- 6. SIDEBAR BRANDING & USER PROFILE ---
seal_element = get_nyeri_seal_element()
sidebar_header_html = textwrap.dedent(f"""
<div style="text-align: center; margin-bottom: 15px;">
    {seal_element}
    <h3 style="margin-top: 10px; font-size: 18px; font-weight: 700; color: #FFFFFF;">NYERI COUNTY</h3>
    <span style="color: #D4AF37; font-size: 11px; font-weight: 600; text-transform: uppercase;">Public Works MIS</span>
</div>
<hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.2); margin-bottom: 15px;" />
""")
st.sidebar.markdown(sidebar_header_html, unsafe_allow_html=True)

st.sidebar.markdown(f"**👤 User:** {st.session_state.get('username', 'User')}")
st.sidebar.markdown(f"**🛡️ Role:** {st.session_state.get('role', 'Viewer')}")

if st.sidebar.button("Logout"):
    log_audit_action(st.session_state["username"], "Logout", "System", "User logged out")
    st.session_state["authenticated"] = False
    st.session_state["show_goodbye"] = True
    st.session_state["last_username"] = st.session_state.get("username", "User")
    st.rerun()

st.sidebar.markdown("---")

# --- 7. WELCOME TOAST NOTIFICATION ---
current_greeting = get_time_greeting()
user_display = st.session_state.get("full_name", st.session_state.get("username", "User"))

if st.session_state.get("just_logged_in", False):
    st.toast(f"👋 {current_greeting}, {user_display}! Welcome to Nyeri MIS Portal.", icon="🏛️")
    st.session_state["just_logged_in"] = False

# Dynamic Header Banner
st.markdown(
    f"""
    <div style="background-color: #f0f7f2; border-left: 5px solid #0A4D20; padding: 12px 20px; border-radius: 6px; margin-bottom: 20px;">
        <span style="color: #0A4D20; font-weight: 600; font-size: 18px;">☀️ {current_greeting}, {user_display}!</span>
        <span style="color: #555555; font-size: 14px; margin-left: 10px;">| County Government of Nyeri Executive MIS Dashboard</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- 8. FETCH DATA FUNCTIONS ---
def fetch_project_data():
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        df = pd.read_sql_query("SELECT * FROM projects", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()

def fetch_audit_logs():
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        df = pd.read_sql_query("SELECT timestamp, username, action, target_record, details FROM audit_logs ORDER BY log_id DESC LIMIT 25", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def fetch_documents(project_code=None):
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        query = "SELECT project_code, filename, file_path, uploaded_by, upload_timestamp FROM documents"
        if project_code:
            query += f" WHERE project_code = '{project_code}'"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

# Helper for budget formatting
def format_currency_short(val):
    if val >= 1e9:
        return f"KES {val/1e9:.2f}B"
    elif val >= 1e6:
        return f"KES {val/1e6:.2f}M"
    elif val >= 1e3:
        return f"KES {val/1e3:.2f}K"
    return f"KES {val:,.2f}"


# --- 9. APPLICATION NAVIGATION TABS ---
tab_dash, tab_entry, tab_docs, tab_audit = st.tabs([
    "📊 Executive Dashboard", 
    "➕ Project Management", 
    "📄 Document Repository", 
    "🔐 Audit Trail"
])

df = fetch_project_data()

# TAB 1: EXECUTIVE DASHBOARD
with tab_dash:
    if not df.empty:
        st.sidebar.header("📊 Filter Projects")

        dept_col = next((c for c in df.columns if c.lower() in ["department_assigned", "department", "dept", "dept_name"]), None)
        status_col = next((c for c in df.columns if c.lower() in ["workflow_stage", "current_status", "status", "stage"]), None)
        budget_col = next((c for c in df.columns if c.lower() in ["budget_allocated", "budget", "cost"]), None)
        name_col = next((c for c in df.columns if c.lower() in ["project_name", "name", "title"]), df.columns[0])
        subcounty_col = next((c for c in df.columns if c.lower() in ["sub_county", "subcounty", "ward"]), None)

        filtered_df = df.copy()

        if dept_col:
            departments = ["All"] + list(filtered_df[dept_col].dropna().unique())
            selected_dept = st.sidebar.selectbox("Filter by Department", departments)
            if selected_dept != "All":
                filtered_df = filtered_df[filtered_df[dept_col] == selected_dept]

        if status_col:
            statuses = ["All"] + list(filtered_df[status_col].dropna().unique())
            selected_status = st.sidebar.selectbox("Filter by Stage", statuses)
            if selected_status != "All":
                filtered_df = filtered_df[filtered_df[status_col] == selected_status]

        # KPI Metrics
        st.subheader(f"Executive Summary ({len(filtered_df)} Projects Displayed)")
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        total_proj = len(filtered_df)
        completed_proj = 0
        ongoing_proj = 0

        if status_col:
            completed_proj = len(filtered_df[filtered_df[status_col].astype(str).str.lower().str.contains("complete|done|finished", na=False)])
            ongoing_proj = total_proj - completed_proj

        total_budget = 0.0
        if budget_col:
            total_budget = pd.to_numeric(filtered_df[budget_col], errors="coerce").sum()

        kpi1.metric("Total Projects", total_proj)
        kpi2.metric("Active / Ongoing", ongoing_proj)
        kpi3.metric("Completed Projects", completed_proj)
        kpi4.metric("Total Budget Allocated", format_currency_short(total_budget), help=f"Exact Budget: KES {total_budget:,.2f}")

        # Charts Section
        col_left, col_right = st.columns(2)

        with col_left:
            if dept_col:
                dept_counts = filtered_df[dept_col].value_counts().reset_index()
                dept_counts.columns = ["Department", "Count"]

                fig_dept = px.bar(
                    dept_counts,
                    x="Department",
                    y="Count",
                    color="Department",
                    title="Projects by Department",
                    color_discrete_sequence=px.colors.qualitative.Bold,
                )
                fig_dept.update_layout(xaxis_tickangle=-30, showlegend=False, margin=dict(t=30, b=20))
                st.plotly_chart(fig_dept, use_container_width=True)

        with col_right:
            if status_col:
                status_color_map = {
                    "Completed": "#2e7d32",
                    "Approved": "#4caf50",
                    "In Progress": "#0288d1",
                    "Review": "#f57c00",
                    "Draft": "#9e9e9e",
                    "Delayed": "#d32f2f",
                }
                fig_status = px.pie(
                    filtered_df,
                    names=status_col,
                    hole=0.4,
                    title="Project Stage Breakdown",
                    color=status_col,
                    color_discrete_map=status_color_map,
                )
                fig_status.update_layout(margin=dict(t=30, b=20))
                st.plotly_chart(fig_status, use_container_width=True)

        # GIS Interactive Nyeri Map
        st.subheader("🗺️ Nyeri County Project GIS Map")

        NYERI_COORDINATES = {
            "mathira east": (-0.4812, 37.1281), "mathira west": (-0.4285, 37.0600),
            "othaya": (-0.5439, 36.9472), "mukurweini": (-0.5606, 37.0483),
            "tetu": (-0.4350, 36.8833), "nyeri town": (-0.4201, 36.9476),
            "kieni east": (-0.1500, 37.0500), "kieni west": (-0.2800, 36.8500),
        }

        def assign_coordinates(row):
            loc_str = ""
            if subcounty_col and row.get(subcounty_col): loc_str += str(row.get(subcounty_col)).lower()
            if name_col and row.get(name_col): loc_str += " " + str(row.get(name_col)).lower()

            for key, coords in NYERI_COORDINATES.items():
                if key in loc_str: return coords
            return (-0.4201, 36.9476) 

        map_df = filtered_df.copy()
        coords = map_df.apply(assign_coordinates, axis=1)
        map_df["latitude"] = [c[0] for c in coords]
        map_df["longitude"] = [c[1] for c in coords]

        np.random.seed(42)
        map_df["latitude"] += np.random.uniform(-0.008, 0.008, size=len(map_df))
        map_df["longitude"] += np.random.uniform(-0.008, 0.008, size=len(map_df))

        hover_cols = {c: True for c in [dept_col, status_col] if c}
        if budget_col: hover_cols[budget_col] = ":,.2f"
        hover_cols["latitude"] = False
        hover_cols["longitude"] = False

        fig_map = px.scatter_mapbox(
            map_df, lat="latitude", lon="longitude", hover_name=name_col,
            hover_data=hover_cols, color=status_col if status_col else None,
            zoom=9.5, center={"lat": -0.4201, "lon": 36.9476}, height=450,
        )
        fig_map.update_layout(mapbox_style="open-street-map", margin={"r": 0, "t": 10, "l": 0, "b": 10})
        st.plotly_chart(fig_map, use_container_width=True)

        # Full Table with Streamlit Progress Column
        st.subheader("📋 Project Details Table")
        st.dataframe(
            filtered_df,
            column_config={
                "percentage_complete": st.column_config.ProgressColumn(
                    "Completion %",
                    help="Project progress percentage",
                    format="%d%%",
                    min_value=0,
                    max_value=100,
                ),
                "budget_allocated": st.column_config.NumberColumn("Allocated Budget (KES)", format="KES %,.2f"),
                "actual_spend": st.column_config.NumberColumn("Actual Spend (KES)", format="KES %,.2f"),
            },
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.warning("No project data found. Navigate to the **Project Management** tab to enter your first project.")

# TAB 2: PROJECT MANAGEMENT & ENTRY
with tab_entry:
    st.subheader("🛠️ Project Data Management")
    
    sub_tab1, sub_tab2 = st.tabs(["➕ Create New Project", "✏️ Update Existing Project Progress"])

    with sub_tab1:
        with st.form("new_project_form", clear_on_submit=True):
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                p_code = st.text_input("Project Code", value=f"PRJ-2026-00{len(df)+1}")
                p_name = st.text_input("Project Name (e.g., Othaya Road Resurfacing)")
                p_subcounty = st.selectbox("Sub-County", ["Nyeri Town", "Othaya", "Tetu", "Mukurweini", "Mathira East", "Mathira West", "Kieni East", "Kieni West"])
                p_dept = st.selectbox("Department", ["Roads & Transport", "Public Works", "Water & Sanitation", "Infrastructure & Energy", "Health Services"])
                p_budget = st.number_input("Allocated Budget (KES)", min_value=0.0, step=500000.0, value=5000000.0)

            with col_p2:
                p_spend = st.number_input("Actual Spend to Date (KES)", min_value=0.0, step=100000.0, value=0.0)
                p_complete = st.slider("Completion Percentage (%)", min_value=0, max_value=100, value=0)
                p_stage = st.selectbox("Workflow Stage", ["Draft", "Review", "Approved", "In Progress", "Completed"])
                p_status = st.selectbox("Current Status", ["Active", "Delayed", "Completed", "On Hold"])

            btn_save = st.form_submit_button("💾 Save New Project Record", use_container_width=True)

            if btn_save:
                if not p_name.strip() or not p_code.strip():
                    st.error("Please provide both a Project Code and Project Name.")
                else:
                    try:
                        conn = sqlite3.connect("nyeri_public_works.db")
                        cursor = conn.cursor()
                        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute("""
                            INSERT INTO projects 
                            (project_code, project_name, sub_county, department, budget_allocated, actual_spend, percentage_complete, workflow_stage, status, created_by, last_updated)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (p_code, p_name, p_subcounty, p_dept, p_budget, p_spend, p_complete, p_stage, p_status, st.session_state["username"], now_str))
                        conn.commit()
                        conn.close()

                        log_audit_action(st.session_state["username"], "Create Project", p_code, f"Created project: {p_name}")
                        st.success(f"✅ Project '{p_name}' successfully created!")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error(f"⚠️ Project Code '{p_code}' already exists. Please use a unique code.")
                    except Exception as e:
                        st.error(f"Error saving project: {e}")

    with sub_tab2:
        if not df.empty:
            selected_edit_code = st.selectbox("Select Project to Update", df["project_code"].unique())
            current_row = df[df["project_code"] == selected_edit_code].iloc[0]

            with st.form("update_project_form"):
                st.info(f"Updating **{current_row['project_name']}** ({current_row['project_code']})")
                u_col1, u_col2 = st.columns(2)
                
                with u_col1:
                    u_spend = st.number_input("Update Spend to Date (KES)", min_value=0.0, step=100000.0, value=float(current_row['actual_spend']))
                    u_complete = st.slider("Update Completion %", min_value=0, max_value=100, value=int(current_row['percentage_complete']))

                with u_col2:
                    stages = ["Draft", "Review", "Approved", "In Progress", "Completed"]
                    u_stage = st.selectbox("Update Workflow Stage", stages, index=stages.index(current_row['workflow_stage']) if current_row['workflow_stage'] in stages else 0)
                    statuses = ["Active", "Delayed", "Completed", "On Hold"]
                    u_status = st.selectbox("Update Overall Status", statuses, index=statuses.index(current_row['status']) if current_row['status'] in statuses else 0)

                btn_update = st.form_submit_button("🔄 Update Project Record", use_container_width=True)

                if btn_update:
                    try:
                        conn = sqlite3.connect("nyeri_public_works.db")
                        cursor = conn.cursor()
                        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute("""
                            UPDATE projects 
                            SET actual_spend = ?, percentage_complete = ?, workflow_stage = ?, status = ?, last_updated = ?
                            WHERE project_code = ?
                        """, (u_spend, u_complete, u_stage, u_status, now_str, selected_edit_code))
                        conn.commit()
                        conn.close()

                        log_audit_action(st.session_state["username"], "Update Project", selected_edit_code, f"Updated progress to {u_complete}% ({u_stage})")
                        st.success(f"✅ Project '{selected_edit_code}' successfully updated!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error updating project: {e}")
        else:
            st.info("No projects available to update.")

# TAB 3: DOCUMENT REPOSITORY
with tab_docs:
    st.subheader("📄 Upload & Attach Project Documents")
    
    if not df.empty:
        col_doc1, col_doc2 = st.columns([1, 1])

        with col_doc1:
            selected_proj_code = st.selectbox("Select Target Project Code", df["project_code"].unique(), key="doc_project_select")
            uploaded_file = st.file_uploader("Upload Project Specification / Tender PDF", type=["pdf", "docx", "xlsx", "png", "jpg"])

            if st.button("Upload Document") and uploaded_file and selected_proj_code:
                try:
                    os.makedirs("uploads", exist_ok=True)
                    save_path = os.path.join("uploads", uploaded_file.name)
                    
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())

                    conn = sqlite3.connect("nyeri_public_works.db")
                    cursor = conn.cursor()
                    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cursor.execute("""
                        INSERT INTO documents (project_code, filename, file_path, uploaded_by, upload_timestamp)
                        VALUES (?, ?, ?, ?, ?)
                    """, (selected_proj_code, uploaded_file.name, save_path, st.session_state["username"], now_str))
                    conn.commit()
                    conn.close()

                    log_audit_action(st.session_state["username"], "Upload Document", selected_proj_code, f"Attached {uploaded_file.name}")
                    st.success(f"✅ File '{uploaded_file.name}' successfully uploaded for {selected_proj_code}!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error uploading document: {e}")

        with col_doc2:
            st.markdown(f"### 📂 Existing Documents for `{selected_proj_code}`")
            doc_df = fetch_documents(selected_proj_code)

            if not doc_df.empty:
                for _, row in doc_df.iterrows():
                    file_path = row["file_path"]
                    filename = row["filename"]
                    
                    st.write(f"📄 **{filename}**")
                    st.caption(f"Uploaded by {row['uploaded_by']} on {row['upload_timestamp']}")
                    
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as file_data:
                            st.download_button(
                                label=f"📥 Download {filename}",
                                data=file_data,
                                file_name=filename,
                                key=f"dl_{row['filename']}_{row['upload_timestamp']}"
                            )
                    st.markdown("---")
            else:
                st.info("No documents uploaded for this project yet.")
    else:
        st.warning("Please create a project first before attaching documents.")

# TAB 4: AUDIT TRAIL
with tab_audit:
    st.subheader("🔐 System Audit Logs")
    st.caption("Tracking user activities, project creations, status updates, and logins.")

    audit_df = fetch_audit_logs()

    if not audit_df.empty:
        st.dataframe(
            audit_df,
            column_config={
                "timestamp": "Timestamp",
                "username": "User",
                "action": "Action Taken",
                "target_record": "Target Record",
                "details": "Details / Parameters",
            },
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No audit logs available yet.")
