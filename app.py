import sqlite3
import pandas as pd
import plotly.express as px
import os
import base64
import streamlit as st

# --- Nyeri County Seal Vector Fallback ---
# High-definition SVG replicating official seal elements:
# Kudus, Mount Kenya shield, coffee berries, dairy cow, and blue banner.
NYERI_SEAL_FALLBACK_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" width="140" height="140" style="display: block; margin: 0 auto; filter: drop-shadow(0px 8px 16px rgba(0,0,0,0.35));">
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
</svg>
"""


def get_nyeri_seal_element():
    """
    Renders seal.png if committed to the root directory,
    otherwise renders the fallback vector SVG of the seal.
    """
    if os.path.exists("seal.png"):
        try:
            with open("seal.png", "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            return f"""
            <img src="data:image/png;base64,{encoded_string}" 
                 alt="Nyeri County Government Seal" 
                 style="display: block; margin: 0 auto; width: 140px; height: 140px; border-radius: 50%; filter: drop-shadow(0px 8px 16px rgba(0,0,0,0.45)); border: 3px solid #D4AF37;">
            """
        except Exception:
            pass
    return NYERI_SEAL_FALLBACK_SVG


def inject_custom_styles():
    """
    Injects custom CSS to style the sidebar background in Nyeri Forest Green,
    sets gold headers/borders, and formats form elements, lists, and tables.
    """
    st.markdown(
        """
    <style>
        /* Sidebar background gradient (Nyeri Deep Green) */
        [data-testid="stSidebar"] {
            background-color: #0A4D20 !important;
            background-image: linear-gradient(180deg, #0A4D20 0%, #041f0d 100%) !important;
            color: #FFFFFF !important;
        }
        
        /* Set standard sidebar text to high-contrast white */
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
        
        /* Accent elements in sidebar to gold */
        [data-testid="stSidebar"] strong {
            color: #D4AF37 !important;
        }
        
        /* Highlight active menu item (Registry page) */
        [data-testid="stSidebarNav"] ul li a[href*="Registry"] span,
        [data-testid="stSidebarNav"] ul li a[href*="registry"] span {
            color: #0A4D20 !important;
            font-weight: 700 !important;
        }
        [data-testid="stSidebarNav"] ul li a[href*="Registry"],
        [data-testid="stSidebarNav"] ul li a[href*="registry"] {
            background-color: #FFFFFF !important;
            border-left: 5px solid #D4AF37 !important;
            border-radius: 8px !important;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.2) !important;
        }
        
        /* Custom styling for inputs and selects inside sidebar */
        [data-testid="stSidebar"] div[data-baseweb="select"] {
            background-color: #041f0d !important;
            border: 1px solid #D4AF37 !important;
            border-radius: 8px !important;
        }
        
        /* Styled Logout Button in Sidebar */
        [data-testid="stSidebar"] button {
            background-color: #FFFFFF !important;
            color: #0A4D20 !important;
            border: 2px solid #D4AF37 !important;
            border-radius: 20px !important;
            font-weight: bold !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
        }
        [data-testid="stSidebar"] button:hover {
            background-color: #D4AF37 !important;
            color: #041f0d !important;
            border-color: #FFFFFF !important;
            box-shadow: 0px 4px 12px rgba(212, 175, 55, 0.4) !important;
        }
        
        /* Core metric values green */
        div[data-testid="stMetricValue"] {
            color: #0A4D20 !important;
            font-weight: 700 !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


# 1. PAGE CONFIGURATION
st.set_page_config(
    page_title="Ministry MIS - Executive Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Nyeri custom styling
inject_custom_styles()

# 2. SESSION STATE SETUP
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

USERS = {
    "admin": {"password": "admin123", "role": "Admin"},
    "viewer": {"password": "viewer123", "role": "Viewer"},
}

# 3. LOGIN LOGIC
if not st.session_state["authenticated"]:
    col_logo_l, col_logo_c, col_logo_r = st.columns([1, 1, 1])
    with col_logo_c:
        st.markdown(get_nyeri_seal_element(), unsafe_allow_html=True)

    st.markdown(
        "<h1 style='text-align: center; color: #0A4D20;'>🏛️ County Government of Nyeri</h1>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<h3 style='text-align: center; color: #D4AF37; margin-top: -15px;'>Public Works & Infrastructure MIS Portal</h3>",
        unsafe_allow_html=True,
    )

    login_col1, login_col2, login_col3 = st.columns([1, 1.5, 1])
    with login_col2:
        with st.form("login_form"):
            user_input = st.text_input("Username")
            pass_input = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In Securely")

            if submitted:
                if (
                    user_input in USERS
                    and USERS[user_input]["password"] == pass_input
                ):
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user_input
                    st.session_state["role"] = USERS[user_input]["role"]
                    st.rerun()
                else:
                    st.error("Invalid username or password")

    st.stop()

# --- SIDEBAR USER INFO & LOGOUT ---
seal_html = get_nyeri_seal_element()
st.sidebar.markdown(
    f"""
<div style="text-align: center; margin-bottom: 20px;">
    {seal_html}
    <h3 style="margin-top: 15px; font-size: 18px; font-weight: 700; letter-spacing: 1px;">NYERI COUNTY</h3>
    <span style="color: #D4AF37; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px;">Public Works MIS</span>
</div>
<hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.15); margin-bottom: 20px;" />
""",
    unsafe_allow_html=True,
)

st.sidebar.markdown(f"**👤 User:** {st.session_state.get('username', 'User')}")
st.sidebar.markdown(f"**🛡️ Role:** {st.session_state.get('role', 'Viewer')}")

if st.sidebar.button("Logout"):
    st.session_state["authenticated"] = False
    st.rerun()

st.sidebar.markdown("---")

# 4. DASHBOARD CONTENT (Authenticated)
st.title("🏛️ Department of Public Works, Roads & Infrastructure")
st.subheader("County Government of Nyeri — Executive MIS Dashboard")

try:
    conn = sqlite3.connect("nyeri_public_works.db")

    # Determine available tables
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]

    table_name = (
        "projects" if "projects" in tables else (tables[0] if tables else None)
    )

    if table_name:
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    else:
        df = pd.DataFrame()

    conn.close()

    if not df.empty:
        # Sidebar Filters
        st.sidebar.header("📊 Filter Projects")

        # Case-insensitive column resolution
        dept_col = next(
            (
                col
                for col in df.columns
                if col.lower() in ["department", "dept"]
            ),
            None,
        )
        status_col = next(
            (
                col
                for col in df.columns
                if col.lower() in ["status", "project_status"]
            ),
            None,
        )
        budget_col = next(
            (
                col
                for col in df.columns
                if col.lower() in ["budget", "cost", "allocated_budget"]
            ),
            None,
        )
        name_col = next(
            (
                col
                for col in df.columns
                if col.lower() in ["project_name", "name", "title"]
            ),
            df.columns[0],
        )

        filtered_df = df.copy()

        if dept_col:
            departments = ["All"] + list(filtered_df[dept_col].dropna().unique())
            selected_dept = st.sidebar.selectbox(
                "Filter by Department", departments
            )
            if selected_dept != "All":
                filtered_df = filtered_df[
                    filtered_df[dept_col] == selected_dept
                ]

        if status_col:
            statuses = ["All"] + list(filtered_df[status_col].dropna().unique())
            selected_status = st.sidebar.selectbox(
                "Filter by Status", statuses
            )
            if selected_status != "All":
                filtered_df = filtered_df[
                    filtered_df[status_col] == selected_status
                ]

        # --- KPI METRICS ---
        st.subheader(
            f"Executive Summary ({len(filtered_df)} Projects Displayed)"
        )
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)

        total_proj = len(filtered_df)

        completed_proj = 0
        pending_proj = 0
        if status_col:
            completed_proj = len(
                filtered_df[
                    filtered_df[status_col]
                    .str.lower()
                    .str.contains("complete", na=False)
                ]
            )
            pending_proj = total_proj - completed_proj

        total_budget = 0.0
        if budget_col:
            total_budget = pd.to_numeric(
                filtered_df[budget_col], errors="coerce"
            ).sum()

        kpi1.metric("Total Projects", total_proj)
        kpi2.metric("Completed Projects", completed_proj)
        kpi3.metric("Pending Projects", pending_proj)
        kpi4.metric("Total Budget Allocated", f"KES {total_budget:,.2f}")

        # --- INTERACTIVE PLOTLY CHARTS ---
        col_left, col_right = st.columns(2)

        with col_left:
            if dept_col:
                dept_counts = (
                    filtered_df[dept_col].value_counts().reset_index()
                )
                dept_counts.columns = ["Department", "Count"]
                fig_dept = px.bar(
                    dept_counts,
                    x="Department",
                    y="Count",
                    labels={
                        "Department": "Department",
                        "Count": "Project Count",
                    },
                    color="Count",
                    color_continuous_scale="Greens",
                )
                fig_dept.update_layout(
                    xaxis_tickangle=-45,
                    showlegend=False,
                    margin=dict(t=20, b=20),
                )
                st.plotly_chart(fig_dept, use_container_width=True)
            else:
                st.info("No department data available.")

        with col_right:
            if status_col:
                fig_status = px.pie(
                    filtered_df,
                    names=status_col,
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Greens[::-1],
                )
                fig_status.update_layout(margin=dict(t=20, b=20))
                st.plotly_chart(fig_status, use_container_width=True)
            else:
                st.info("No status data available.")

        # --- BUDGET COMPLIANCE & HIGH-VALUE PROJECTS ---
        st.subheader("⚠️ High-Value Budget Oversight")
        if budget_col:
            temp_df = filtered_df.copy()
            temp_df[budget_col] = pd.to_numeric(
                temp_df[budget_col], errors="coerce"
            ).fillna(0)
            top_budget = temp_df.sort_values(
                by=budget_col, ascending=False
            ).head(5)
            cols_to_show = [
                c
                for c in [name_col, dept_col, status_col, budget_col]
                if c and c in top_budget.columns
            ]
            st.dataframe(top_budget[cols_to_show], use_container_width=True)
        else:
            st.info("No budget data column found.")

        # --- FULL FILTERED TABLE ---
        st.subheader("Project Details Table")
        st.dataframe(filtered_df, use_container_width=True)

    else:
        st.info(
            "The database is currently empty or no projects table was found. Please add projects using the Registry page."
        )

except Exception as e:
    st.error(f"Could not load data: {e}")
