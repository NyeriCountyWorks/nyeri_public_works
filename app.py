import base64
import datetime
import os
import sqlite3
import textwrap
import pandas as pd
import plotly.express as px
import streamlit as st


# --- 1. DATABASE & USER AUTHENTICATION HELPERS ---
def init_users_db():
    """Ensure the users table exists and contains default credentials."""
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'Viewer'
            )
        """
        )

        cursor.execute("PRAGMA table_info(users)")
        cols = [col[1] for col in cursor.fetchall()]

        if "password" not in cols:
            cursor.execute(
                "ALTER TABLE users ADD COLUMN password TEXT DEFAULT 'admin123'"
            )
        if "role" not in cols:
            cursor.execute(
                "ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'Viewer'"
            )

        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES ('admin', 'admin123', 'Administrator', 'Admin')"
            )
            cursor.execute(
                "INSERT INTO users (username, password, full_name, role) VALUES ('viewer', 'viewer123', 'Executive Viewer', 'Viewer')"
            )

        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"User DB Initialization error: {e}")


def verify_login(username, password):
    """Verify user credentials against SQLite or static fallback."""
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(users)")
        cols = [col[1] for col in cursor.fetchall()]

        name_col = "full_name" if "full_name" in cols else "username"
        role_col = (
            "role"
            if "role" in cols
            else ("role_title" if "role_title" in cols else "'Viewer'")
        )

        cursor.execute(
            f"SELECT username, password, {name_col}, {role_col} FROM users WHERE LOWER(username) = LOWER(?)",
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

    fallback_users = {
        "admin": {
            "password": "admin123",
            "role": "Admin",
            "full_name": "Administrator",
        },
        "viewer": {
            "password": "viewer123",
            "role": "Viewer",
            "full_name": "Executive Viewer",
        },
    }
    if (
        username in fallback_users
        and fallback_users[username]["password"] == password
    ):
        return {
            "username": username,
            "full_name": fallback_users[username]["full_name"],
            "role": fallback_users[username]["role"],
        }

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
        return True, "🎉 Account created successfully! You can now log in."
    except sqlite3.IntegrityError:
        return (
            False,
            "⚠️ Username already exists. Please pick a different username.",
        )
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
      <circle cx="242" cy="206" r="6" fill="#c0392b" />
      <circle cx="258" cy="208" r="6" fill="#c0392b" />
      <path d="M 245,215 Q 250,205 255,215" stroke="#27ae60" stroke-width="2" fill="none" />
      <rect x="150" y="235" width="200" height="70" fill="#f39c12" />
      <rect x="230" y="255" width="40" height="20" rx="3" fill="#FFFFFF" stroke="#000000" stroke-width="1.5" />
      <rect x="260" y="252" width="12" height="12" rx="2" fill="#FFFFFF" stroke="#000000" stroke-width="1.5" />
      <circle cx="238" cy="262" r="3.5" fill="#000000" />
      <circle cx="254" cy="268" r="4.5" fill="#000000" />
      <line x1="235" y1="275" x2="235" y2="288" stroke="#000000" stroke-width="2.5" />
      <line x1="242" y1="275" x2="242" y2="288" stroke="#000000" stroke-width="2.5" />
      <line x1="258" y1="275" x2="258" y2="288" stroke="#000000" stroke-width="2.5" />
      <line x1="265" y1="275" x2="265" y2="288" stroke="#000000" stroke-width="2.5" />
    </g>
  </g>

  <path d="M 100,280 Q 120,180 178,160 Q 170,140 150,110 Q 165,115 174,138 Q 185,190 175,270 L 170,330 Q 150,340 100,280 Z" fill="#b87333" stroke="#4a2c11" stroke-width="2" />
  <path d="M 132,240 Q 142,242 145,260 M 125,250 Q 135,252 138,270" stroke="#FFFFFF" stroke-width="2.5" fill="none" />
  <path d="M 152,112 Q 135,70 148,40 Q 155,60 156,92" fill="#111111" />

  <path d="M 400,280 Q 380,180 322,160 Q 330,140 350,110 Q 335,115 326,138 Q 315,190 325,270 L 330,330 Q 350,340 400,280 Z" fill="#b87333" stroke="#4a2c11" stroke-width="2" />
  <path d="M 368,240 Q 358,242 355,260 M 375,250 Q 365,252 362,270" stroke="#FFFFFF" stroke-width="2.5" fill="none" />
  <path d="M 348,112 Q 365,70 352,40 Q 345,60 344,92" fill="#111111" />

  <path d="M 90,340 Q 250,390 410,340 L 390,390 Q 250,440 110,390 Z" fill="#2980b9" stroke="url(#goldGradient)" stroke-width="3" />
  <text font-family="'Poppins', 'Inter', sans-serif" font-size="20" font-weight="bold" fill="#FFFFFF" letter-spacing="1.5">
    <textPath href="#bottomTextCirclePath" startOffset="50%" text-anchor="middle">Ndaragwa na Maitu</textPath>
  </text>

  <g fill="#2980b9" transform="translate(0, 10)">
    <polygon points="170,415 173,425 183,425 175,431 178,441 170,435 162,441 165,431 157,425 167,425" />
    <polygon points="210,430 213,440 223,440 215,446 218,456 210,450 202,456 205,446 197,440 207,440" />
    <polygon points="250,435 253,445 263,445 255,451 258,461 250,455 242,461 245,451 237,445 247,445" />
    <polygon points="290,430 293,440 303,440 295,446 298,456 290,450 282,456 285,446 277,440 287,440" />
    <polygon points="330,415 333,425 343,425 335,431 338,441 330,435 322,441 325,431 317,425 327,425" />
  </g>
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
        [data-testid="stSidebar"] button {
            background-color: #FFFFFF !important;
            color: #0A4D20 !important;
            border: 2px solid #D4AF37 !important;
            border-radius: 20px !important;
            font-weight: bold !important;
            width: 100% !important;
        }
        [data-testid="stSidebar"] button:hover {
            background-color: #D4AF37 !important;
            color: #041f0d !important;
            border-color: #FFFFFF !important;
        }
        div[data-testid="stMetricValue"] {
            color: #0A4D20 !important;
            font-weight: 700 !important;
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
init_users_db()

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
        st.success(
            f"👋 Goodbye, **{last_user}**! You have been logged out securely. Have a great day!"
        )
        st.session_state["show_goodbye"] = False

    _, auth_col, _ = st.columns([1, 1.8, 1])
    with auth_col:
        tab_login, tab_signup = st.tabs(["🔒 Sign In", "📝 Create Account"])

        with tab_login:
            with st.form("login_form"):
                user_input = st.text_input("Username")
                pass_input = st.text_input("Password", type="password")
                submitted = st.form_submit_button(
                    "Sign In Securely", use_container_width=True
                )

                if submitted:
                    user_data = verify_login(user_input, pass_input)
                    if user_data:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = user_data["username"]
                        st.session_state["role"] = user_data["role"]
                        st.session_state["full_name"] = user_data["full_name"]
                        st.session_state["just_logged_in"] = True
                        st.rerun()
                    else:
                        st.error("Invalid username or password.")

        with tab_signup:
            with st.form("signup_form"):
                new_fullname = st.text_input("Full Name (e.g., Jane Doe)")
                new_username = st.text_input("Choose Username")
                new_password = st.text_input("Choose Password", type="password")
                confirm_password = st.text_input(
                    "Confirm Password", type="password"
                )
                new_role = st.selectbox(
                    "Access Role",
                    ["Viewer", "Project Officer", "Department Manager"],
                )

                signup_submitted = st.form_submit_button(
                    "Register New Account", use_container_width=True
                )

                if signup_submitted:
                    if (
                        not new_fullname.strip()
                        or not new_username.strip()
                        or not new_password
                    ):
                        st.warning("Please fill in all required fields.")
                    elif new_password != confirm_password:
                        st.error("Passwords do not match. Please re-enter.")
                    elif len(new_password) < 4:
                        st.error("Password must be at least 4 characters long.")
                    else:
                        success, msg = register_user(
                            new_username, new_password, new_fullname, new_role
                        )
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
    st.session_state["authenticated"] = False
    st.session_state["show_goodbye"] = True
    st.session_state["last_username"] = st.session_state.get("username", "User")
    st.rerun()

st.sidebar.markdown("---")

# --- 7. WELCOME TOAST NOTIFICATION ON LOGIN ---
current_greeting = get_time_greeting()
user_display = st.session_state.get(
    "full_name", st.session_state.get("username", "User")
)

if st.session_state.get("just_logged_in", False):
    st.toast(
        f"👋 {current_greeting}, {user_display}! Welcome to Nyeri MIS Portal.",
        icon="🏛️",
    )
    st.session_state["just_logged_in"] = False

# --- 8. DASHBOARD MAIN CONTENT ---
st.title("🏛️ Department of Public Works, Roads & Infrastructure")

# Dynamic Header Banner with Time-based Greeting
st.markdown(
    f"""
    <div style="background-color: #f0f7f2; border-left: 5px solid #0A4D20; padding: 12px 20px; border-radius: 6px; margin-bottom: 20px;">
        <span style="color: #0A4D20; font-weight: 600; font-size: 18px;">☀️ {current_greeting}, {user_display}!</span>
        <span style="color: #555555; font-size: 14px; margin-left: 10px;">| County Government of Nyeri Executive MIS Dashboard</span>
    </div>
    """,
    unsafe_allow_html=True,
)


def fetch_project_data():
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]

        if not tables:
            conn.close()
            return pd.DataFrame()

        ignored_tables = ["users", "audit_trail", "sqlite_sequence"]
        candidate_tables = [t for t in tables if t.lower() not in ignored_tables]

        target_table = None
        for t in candidate_tables:
            if "project" in t.lower() or "registry" in t.lower():
                target_table = t
                break

        if not target_table and candidate_tables:
            target_table = candidate_tables[0]

        if target_table:
            df = pd.read_sql_query(f"SELECT * FROM {target_table}", conn)
            conn.close()
            return df

        conn.close()
        return pd.DataFrame()
    except Exception as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()


df = fetch_project_data()

if not df.empty:
    st.sidebar.header("📊 Filter Projects")

    dept_col = next(
        (
            c
            for c in df.columns
            if c.lower()
            in [
                "department_assigned",
                "department",
                "dept",
                "dept_name",
                "assigned_department",
            ]
        ),
        None,
    )
    status_col = next(
        (
            c
            for c in df.columns
            if c.lower()
            in [
                "current_status",
                "status",
                "project_status",
                "stage",
                "state",
            ]
        ),
        None,
    )
    budget_col = next(
        (
            c
            for c in df.columns
            if c.lower()
            in [
                "budget_allocated",
                "budget",
                "cost",
                "allocated_budget",
                "amount",
                "budget_allocated_kes",
            ]
        ),
        None,
    )
    name_col = next(
        (
            c
            for c in df.columns
            if c.lower() in ["project_name", "name", "title", "project_title"]
        ),
        df.columns[0],
    )

    filtered_df = df.copy()

    if dept_col:
        departments = ["All"] + list(filtered_df[dept_col].dropna().unique())
        selected_dept = st.sidebar.selectbox("Filter by Department", departments)
        if selected_dept != "All":
            filtered_df = filtered_df[filtered_df[dept_col] == selected_dept]

    if status_col:
        statuses = ["All"] + list(filtered_df[status_col].dropna().unique())
        selected_status = st.sidebar.selectbox("Filter by Status", statuses)
        if selected_status != "All":
            filtered_df = filtered_df[filtered_df[status_col] == selected_status]

    # --- KPI METRICS ---
    st.subheader(f"Executive Summary ({len(filtered_df)} Projects Displayed)")
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)

    total_proj = len(filtered_df)
    completed_proj = 0
    pending_proj = 0

    if status_col:
        completed_proj = len(
            filtered_df[
                filtered_df[status_col]
                .astype(str)
                .str.lower()
                .str.contains("complete|done|finished|active", na=False)
            ]
        )
        pending_proj = total_proj - completed_proj

    total_budget = 0.0
    if budget_col:
        total_budget = pd.to_numeric(
            filtered_df[budget_col], errors="coerce"
        ).sum()

    kpi1.metric("Total Projects", total_proj)
    kpi2.metric("Completed / Active Projects", completed_proj)
    kpi3.metric("Pending Projects", pending_proj)
    kpi4.metric("Total Budget Allocated", f"KES {total_budget:,.2f}")

    # --- MULTI-COLOR CHARTS ---
    col_left, col_right = st.columns(2)

    with col_left:
        if dept_col:
            dept_counts = filtered_df[dept_col].value_counts().reset_index()
            dept_counts.columns = ["Department", "Count"]

            # Multi-color qualitative palette for distinct bar colors per department
            fig_dept = px.bar(
                dept_counts,
                x="Department",
                y="Count",
                color="Department",
                color_discrete_sequence=px.colors.qualitative.Bold,
                labels={
                    "Department": "Department",
                    "Count": "Project Count",
                },
            )
            fig_dept.update_layout(
                xaxis_tickangle=-45,
                showlegend=False,
                margin=dict(t=20, b=20),
            )
            st.plotly_chart(fig_dept, use_container_width=True)
        else:
            st.info("No department data column found.")

    with col_right:
        if status_col:
            # Semantic color mapping for project status clarity
            status_color_map = {
                "Completed": "#2e7d32",  # Dark Green
                "Approved": "#4caf50",   # Light Green
                "Active": "#0288d1",     # Royal Blue
                "Pending": "#f57c00",    # Orange
                "Rejected": "#d32f2f",   # Red
            }

            fig_status = px.pie(
                filtered_df,
                names=status_col,
                hole=0.4,
                color=status_col,
                color_discrete_map=status_color_map,
            )
            fig_status.update_layout(margin=dict(t=20, b=20))
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("No status data column found.")

    # --- BUDGET OVERSIGHT ---
    st.subheader("⚠️ High-Value Budget Oversight")
    if budget_col:
        temp_df = filtered_df.copy()
        temp_df[budget_col] = pd.to_numeric(
            temp_df[budget_col], errors="coerce"
        ).fillna(0)
        top_budget = temp_df.sort_values(by=budget_col, ascending=False).head(5)
        cols_to_show = [
            c
            for c in [name_col, dept_col, status_col, budget_col]
            if c and c in top_budget.columns
        ]
        st.dataframe(top_budget[cols_to_show], use_container_width=True)
    else:
        st.info("No budget data column found.")

    # --- FULL TABLE ---
    st.subheader("Project Details Table")
    st.dataframe(filtered_df, use_container_width=True)

else:
    st.warning("No project data found. Please add projects via the Registry page.")
