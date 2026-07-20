import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import os
import base64

# --- STREAMING_CHUNK: Defining the Nyeri County Seal vector fallback ---
# This high-definition SVG replicates the official seal.png elements:
# Two Kudus, Mount Kenya shield, red coffee berries, dairy cow, and the blue banner.
NYERI_SEAL_FALLBACK_SVG = """
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" width="140" height="140" style="display: block; margin: 0 auto; filter: drop-shadow(0px 8px 16px rgba(0,0,0,0.35));">
  <defs>
    <!-- Circular text paths -->
    <path id="textCirclePath" d="M 50,250 A 200,200 0 1,1 450,250 A 200,200 0 1,1 50,250" fill="none" />
    <path id="bottomTextCirclePath" d="M 410,250 A 160,160 0 0,1 90,250" fill="none" />
    <!-- Gradient Backgrounds -->
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

  <!-- Outer ring system -->
  <circle cx="250" cy="250" r="235" fill="#FFFFFF" stroke="url(#goldGradient)" stroke-width="6" />
  <circle cx="250" cy="250" r="218" fill="#4CAF50" stroke="#0A4D20" stroke-width="4.5" />
  <circle cx="250" cy="250" r="175" fill="#FFFFFF" stroke="url(#goldGradient)" stroke-width="3" />

  <!-- Outer circular branding text -->
  <text font-family="'Poppins', 'Inter', sans-serif" font-size="28" font-weight="900" fill="#FFFFFF" letter-spacing="4">
    <textPath href="#textCirclePath" startOffset="25%" text-anchor="middle">COUNTY GOVERNMENT OF NYERI</textPath>
  </text>

  <!-- Central Shield -->
  <g transform="translate(0, -10)">
    <!-- Shield Outer Frame -->
    <path d="M 180,120 Q 250,110 320,120 Q 320,240 250,300 Q 180,240 180,120 Z" fill="#FFFFFF" stroke="url(#goldGradient)" stroke-width="5" />
    
    <!-- Shield Sky & Mount Kenya (Top Section) -->
    <clipPath id="shieldClip">
      <path d="M 183,123 Q 250,113 317,123 Q 317,237 250,295 Q 183,237 183,123 Z" />
    </clipPath>
    
    <g clip-path="url(#shieldClip)">
      <!-- Sky Background -->
      <rect x="150" y="90" width="200" height="100" fill="url(#shieldSky)" />
      <!-- Mount Kenya Peak with Snow -->
      <polygon points="250,105 185,185 315,185" fill="#2c3e50" />
      <polygon points="250,105 225,140 250,135 275,140" fill="#FFFFFF" />
      
      <!-- Green Field (Middle Section) -->
      <rect x="150" y="180" width="200" height="60" fill="#8bc34a" stroke="#ffffff" stroke-width="2" />
      <!-- Red Coffee Berries -->
      <circle cx="250" cy="210" r="7" fill="#e74c3c" />
      <circle cx="242" cy="206" r="6" fill="#c0392b" />
      <circle cx="258" cy="208" r="6" fill="#c0392b" />
      <path d="M 245,215 Q 250,205 255,215" stroke="#27ae60" stroke-width="2" fill="none" />

      <!-- Yellow Ground & Cow (Lower Section) -->
      <rect x="150" y="235" width="200" height="70" fill="#f39c12" />
      <!-- Simple Cow Graphic -->
      <rect x="230" y="255" width="40" height="20" rx="3" fill="#FFFFFF" stroke="#000000" stroke-width="1.5" />
      <rect x="260" y="252" width="12" height="12" rx="2" fill="#FFFFFF" stroke="#000000" stroke-width="1.5" />
      <circle cx="238" cy="262" r="3.5" fill="#000000" />
      <circle cx="254" cy="268" r="4.5" fill="#000000" />
      <!-- Cow legs -->
      <line x1="235" y1="275" x2="235" y2="288" stroke="#000000" stroke-width="2.5" />
      <line x1="242" y1="275" x2="242" y2="288" stroke="#000000" stroke-width="2.5" />
      <line x1="258" y1="275" x2="258" y2="288" stroke="#000000" stroke-width="2.5" />
      <line x1="265" y1="275" x2="265" y2="288" stroke="#000000" stroke-width="2.5" />
    </g>
  </g>

  <!-- Left Kudu (Antelope) -->
  <path d="M 100,280 Q 120,180 178,160 Q 170,140 150,110 Q 165,115 174,138 Q 185,190 175,270 L 170,330 Q 150,340 100,280 Z" fill="#b87333" stroke="#4a2c11" stroke-width="2" />
  <!-- Kudu belly white stripes -->
  <path d="M 132,240 Q 142,242 145,260 M 125,250 Q 135,252 138,270" stroke="#FFFFFF" stroke-width="2.5" fill="none" />
  <!-- Left Horn -->
  <path d="M 152,112 Q 135,70 148,40 Q 155,60 156,92" fill="#111111" />

  <!-- Right Kudu (Antelope) -->
  <path d="M 400,280 Q 380,180 322,160 Q 330,140 350,110 Q 335,115 326,138 Q 315,190 325,270 L 330,330 Q 350,340 400,280 Z" fill="#b87333" stroke="#4a2c11" stroke-width="2" />
  <!-- Kudu belly stripes right -->
  <path d="M 368,240 Q 358,242 355,260 M 375,250 Q 365,252 362,270" stroke="#FFFFFF" stroke-width="2.5" fill="none" />
  <!-- Right Horn -->
  <path d="M 348,112 Q 365,70 352,40 Q 345,60 344,92" fill="#111111" />

  <!-- Blue Ribbon / Banner at the Bottom -->
  <path d="M 90,340 Q 250,390 410,340 L 390,390 Q 250,440 110,390 Z" fill="#2980b9" stroke="url(#goldGradient)" stroke-width="3" />
  <text font-family="'Poppins', 'Inter', sans-serif" font-size="20" font-weight="bold" fill="#FFFFFF" letter-spacing="1.5">
    <textPath href="#bottomTextCirclePath" startOffset="50%" text-anchor="middle">Ndaragwa na Maitu</textPath>
  </text>

  <!-- Five Blue Stars at the very bottom -->
  <g fill="#2980b9" transform="translate(0, 10)">
    <polygon points="170,415 173,425 183,425 175,431 178,441 170,435 162,441 165,431 157,425 167,425" />
    <polygon points="210,430 213,440 223,440 215,446 218,456 210,450 202,456 205,446 197,440 207,440" />
    <polygon points="250,435 253,445 263,445 255,451 258,461 250,455 242,461 245,451 237,445 247,445" />
    <polygon points="290,430 293,440 303,440 295,446 298,456 290,450 282,456 285,446 277,440 287,440" />
    <polygon points="330,415 333,425 343,425 335,431 338,441 330,435 322,441 325,431 317,425 327,425" />
  </g>
</svg>
"""

# --- STREAMING_CHUNK: Image Loader for seal.png ---
def get_nyeri_seal_element():
    """
    Renders seal.png if committed to the root directory,
    otherwise renders the beautiful fallback vector SVG of the seal.
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

# --- STREAMING_CHUNK: Injecting Custom CSS styling ---
def inject_custom_styles():
    """
    Injects custom CSS to style the sidebar background in Nyeri Forest Green,
    sets gold headers/borders, and formats form elements, lists, and tables.
    """
    st.markdown(f"""
    <style>
        /* Sidebar background gradient (Nyeri Deep Green) */
        [data-testid="stSidebar"] {{
            background-color: #0A4D20 !important;
            background-image: linear-gradient(180deg, #0A4D20 0%, #041f0d 100%) !important;
            color: #FFFFFF !important;
        }}
        
        /* Set standard sidebar text to high-contrast white */
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] span, 
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] h4, 
        [data-testid="stSidebar"] h5, 
        [data-testid="stSidebar"] h6,
        [data-testid="stSidebar"] label {{
            color: #FFFFFF !important;
            font-family: 'Poppins', sans-serif;
        }}
        
        /* Accent elements in sidebar to gold */
        [data-testid="stSidebar"] strong {{
            color: #D4AF37 !important;
        }}
        
        /* Format navigation components if present in multipage */
        [data-testid="stSidebarNav"] ul li a span {{
            color: #FFFFFF !important;
            font-weight: 600 !important;
        }}
        [data-testid="stSidebarNav"] ul li a svg {{
            fill: #FFFFFF !important;
        }}
        
        /* Highlight active menu item (Registry page) */
        [data-testid="stSidebarNav"] ul li a[href*="Registry"] span,
        [data-testid="stSidebarNav"] ul li a[href*="registry"] span {{
            color: #0A4D20 !important;
            font-weight: 700 !important;
        }}
        [data-testid="stSidebarNav"] ul li a[href*="Registry"],
        [data-testid="stSidebarNav"] ul li a[href*="registry"] {{
            background-color: #FFFFFF !important;
            border-left: 5px solid #D4AF37 !important;
            border-radius: 8px !important;
            box-shadow: 0px 4px 10px rgba(0,0,0,0.2) !important;
        }}
        
        /* Custom styling for inputs and selects inside sidebar */
        [data-testid="stSidebar"] div[data-baseweb="select"] {{
            background-color: #041f0d !important;
            border: 1px solid #D4AF37 !important;
            border-radius: 8px !important;
        }}
        
        /* Styled Logout Button in Sidebar */
        [data-testid="stSidebar"] button {{
            background-color: #FFFFFF !important;
            color: #0A4D20 !important;
            border: 2px solid #D4AF37 !important;
            border-radius: 20px !important;
            font-weight: bold !important;
            transition: all 0.3s ease !important;
            width: 100% !important;
        }}
        [data-testid="stSidebar"] button:hover {{
            background-color: #D4AF37 !important;
            color: #041f0d !important;
            border-color: #FFFFFF !important;
            box-shadow: 0px 4px 12px rgba(212, 175, 55, 0.4) !important;
        }}
        
        /* Core metric values green */
        div[data-testid="stMetricValue"] {{
            color: #0A4D20 !important;
            font-weight: 700 !important;
        }}
    </style>
    """, unsafe_allow_html=True)

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Ministry MIS - Executive Dashboard", layout="wide", initial_sidebar_state="expanded")

# Inject Nyeri styling
inject_custom_styles()

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

# --- STREAMING_CHUNK: Processing Login Authentication Layout ---
if not st.session_state['authenticated']:
    # Center seal on login page
    col_logo_l, col_logo_c, col_logo_r = st.columns([1, 1, 1])
    with col_logo_c:
        st.markdown(get_nyeri_seal_element(), unsafe_allow_html=True)
        
    st.markdown("<h1 style='text-align: center; color: #0A4D20;'>🏛️ County Government of Nyeri</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #D4AF37; margin-top: -15px;'>Public Works & Infrastructure MIS Portal</h3>", unsafe_allow_html=True)
    
    st.write("---")
    
    # Login Panel Form
    login_col1, login_col2, login_col3 = st.columns([1, 1.5, 1])
    with login_col2:
        with st.form("login_form"):
            user_input = st.text_input("Username")
            pass_input = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign In Securely")
            
            if submitted:
                if user_input in USERS and USERS[user_input]["password"] == pass_input:
                    st.session_state['authenticated'] = True
                    st.session_state['username'] = user_input
                    st.session_state['role'] = USERS[user_input]["role"]
                    st.rerun()
                else:
                    st.error("Invalid username or password")
            
    st.stop()

# --- STREAMING_CHUNK: Building Sidebar Branding & Profile Information ---
# Render Nyeri Seal at the absolute top of the sidebar
seal_html = get_nyeri_seal_element()
st.sidebar.markdown(f"""
<div style="text-align: center; margin-bottom: 20px;">
    {seal_html}
    <h3 style="margin-top: 15px; font-size: 18px; font-weight: 700; letter-spacing: 1px;">NYERI COUNTY</h3>
    <span style="color: #D4AF37; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 1.5px;">Public Works MIS</span>
</div>
<hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.15); margin-bottom: 20px;" />
""", unsafe_allow_html=True)

st.sidebar.markdown(f"**👤 User:** {st.session_state['username']}")
st.sidebar.markdown(f"**🛡️ Role:** {st.session_state['role']}")
if st.sidebar.button("Logout"):
    st.session_state['authenticated'] = False
    st.session_state['role'] = None
    st.session_state['username'] = None
    st.rerun()

st.sidebar.markdown("---")

# --- STREAMING_CHUNK: Fetching Project Registry from SQLite database ---
st.title("🏛️ Department of Public Works, Roads & Infrastructure")
st.subheader("County Government of Nyeri — Executive MIS Dashboard")

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
            
        # --- STREAMING_CHUNK: Computing KPI metrics grid ---
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
        
        # --- STREAMING_CHUNK: Creating Plotly Interactive Charts ---
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
                    color_continuous_scale='Greens'  # Brand Green theme color scale
                )
                fig_dept.update_layout(xaxis_tickangle=-45, showlegend=False, margin=dict(t=20, b=20))
                # Fixed: use width="stretch" to resolve recent Streamlit deprecation warnings
                st.plotly_chart(fig_dept, width="stretch")
            else:
                st.info("No department data available.")
                
        with col_right:
            st.subheader("🍩 Status Distribution")
            if status_col and not filtered_df.empty:
                fig_status = px.pie(
                    filtered_df, names=status_col, 
                    hole=0.4,
                    color_discrete_sequence=px.colors.sequential.Greens[::-1]  # Inverted Greens for contrast
                )
                fig_status.update_layout(margin=dict(t=20, b=20))
                # Fixed: use width="stretch" to resolve deprecation warnings
                st.plotly_chart(fig_status, width="stretch")
            else:
                st.info("No status data available.")
                
        # --- STREAMING_CHUNK: High-Value Project Compliance Oversight ---
        st.subheader("⚠️ High-Value Budget Oversight")
        if budget_col and not filtered_df.empty:
            temp_df = filtered_df.copy()
            temp_df[budget_col] = pd.to_numeric(temp_df[budget_col], errors='coerce').fillna(0)
            top_budget = temp_df.sort_values(by=budget_col, ascending=False).head(5)
            cols_to_show = [c for c in [name_col, dept_col, status_col, budget_col] if c in top_budget.columns]
            # Fixed: use width="stretch" to resolve deprecation warnings
            st.dataframe(top_budget[cols_to_show], width="stretch")
        else:
            st.info("No budget data column found.")
                
        # --- STREAMING_CHUNK: Comprehensive Filtered Project Registry Details ---
        st.subheader("Project Details Table")
        # Fixed: use width="stretch" to resolve deprecation warnings
        st.dataframe(filtered_df, width="stretch")
        
    else:
        st.info("The database is currently empty. Please add projects using the Registry page.")

except Exception as e:
    st.error(f"Could not load data: {e}")
```
