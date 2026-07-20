import base64
import os
import textwrap
import streamlit as st

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Project Registry - Ministry MIS",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- 2. NYERI SEAL & BRANDING HELPERS ---
NYERI_SEAL_FALLBACK_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 500 500" width="120" height="120" style="display: block; margin: 0 auto; filter: drop-shadow(0px 6px 12px rgba(0,0,0,0.35));">
  <defs>
    <path id="textCirclePath" d="M 50,250 A 200,200 0 1,1 450,250 A 200,200 0 1,1 50,250" fill="none" />
    <linearGradient id="goldGradient" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#FFF3B0" />
      <stop offset="50%" stop-color="#D4AF37" />
      <stop offset="100%" stop-color="#AA7C11" />
    </linearGradient>
  </defs>
  <circle cx="250" cy="250" r="235" fill="#FFFFFF" stroke="url(#goldGradient)" stroke-width="6" />
  <circle cx="250" cy="250" r="218" fill="#4CAF50" stroke="#0A4D20" stroke-width="4.5" />
  <circle cx="250" cy="250" r="175" fill="#FFFFFF" stroke="url(#goldGradient)" stroke-width="3" />
  <text font-family="sans-serif" font-size="28" font-weight="900" fill="#FFFFFF" letter-spacing="4">
    <textPath href="#textCirclePath" startOffset="25%" text-anchor="middle">COUNTY GOVERNMENT OF NYERI</textPath>
  </text>
  <circle cx="250" cy="250" r="100" fill="#0A4D20" />
</svg>"""


def get_nyeri_seal_element():
    if os.path.exists("seal.png"):
        try:
            with open("seal.png", "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            return f'<img src="data:image/png;base64,{encoded_string}" alt="Nyeri County Seal" style="display: block; margin: 0 auto; width: 120px; height: 120px; border-radius: 50%; border: 3px solid #D4AF37;">'
        except Exception:
            pass
    return NYERI_SEAL_FALLBACK_SVG


def inject_custom_styles():
    st.markdown(
        """
    <style>
        /* Sidebar background gradient */
        [data-testid="stSidebar"] {
            background-color: #0A4D20 !important;
            background-image: linear-gradient(180deg, #0A4D20 0%, #041f0d 100%) !important;
        }

        /* Standard sidebar text (without breaking icons) */
        [data-testid="stSidebar"] p, 
        [data-testid="stSidebar"] h1, 
        [data-testid="stSidebar"] h2, 
        [data-testid="stSidebar"] h3, 
        [data-testid="stSidebar"] h4, 
        [data-testid="stSidebar"] label {
            color: #FFFFFF !important;
            font-family: 'Poppins', sans-serif;
        }

        /* Sidebar Navigation Items */
        [data-testid="stSidebarNav"] a span {
            color: #FFFFFF !important;
        }

        [data-testid="stSidebarNav"] a[aria-current="page"] {
            background-color: rgba(212, 175, 55, 0.25) !important;
            border-left: 4px solid #D4AF37 !important;
            border-radius: 4px !important;
        }

        /* Sidebar user labels */
        [data-testid="stSidebar"] strong {
            color: #D4AF37 !important;
        }

        /* FIX: High-contrast Gold Logout Button with visible dark text */
        div[data-testid="stSidebar"] button {
            background-color: #D4AF37 !important;
            border: 1px solid #AA7C11 !important;
            border-radius: 20px !important;
            width: 100% !important;
            margin-top: 10px !important;
        }

        div[data-testid="stSidebar"] button p,
        div[data-testid="stSidebar"] button span {
            color: #0A4D20 !important;
            font-weight: 700 !important;
        }

        div[data-testid="stSidebar"] button:hover {
            background-color: #FFFFFF !important;
            border-color: #FFFFFF !important;
        }

        div[data-testid="stSidebar"] button:hover p,
        div[data-testid="stSidebar"] button:hover span {
            color: #0A4D20 !important;
        }

        /* Custom Green Badges for Filenames */
        .filename-badge {
            background-color: #e8f5e9;
            color: #0A4D20;
            padding: 4px 10px;
            border-radius: 6px;
            font-family: monospace;
            font-weight: 600;
            border: 1px solid #a5d6a7;
            display: inline-block;
            margin-bottom: 10px;
        }

        /* Main Page Headings */
        h1, h2, h3 {
            color: #0A4D20 !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


# --- 3. APPLY STYLES & RENDER SIDEBAR BRANDING ---
inject_custom_styles()

seal_element = get_nyeri_seal_element()
sidebar_header_html = textwrap.dedent(f"""
<div style="text-align: center; margin-bottom: 15px;">
    {seal_element}
    <h3 style="margin-top: 10px; font-size: 18px; font-weight: 700; color: #FFFFFF !important;">NYERI COUNTY</h3>
    <span style="color: #D4AF37; font-size: 11px; font-weight: 600; text-transform: uppercase;">Public Works MIS</span>
</div>
<hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.2); margin-bottom: 15px;" />
""")
st.sidebar.markdown(sidebar_header_html, unsafe_allow_html=True)

# User session info
if "username" in st.session_state:
    st.sidebar.markdown(f"**👤 User:** {st.session_state.get('username')}")
    st.sidebar.markdown(f"**🛡️ Role:** {st.session_state.get('role', 'Viewer')}")

    if st.sidebar.button("Logout"):
        st.session_state["authenticated"] = False
        st.session_state["show_goodbye"] = True
        st.session_state["last_username"] = st.session_state.get(
            "username", "User"
        )
        st.switch_page("app.py")

st.sidebar.markdown("---")


# --- 4. MAIN REGISTRY PAGE CONTENT ---
st.title("📋 Project Registry & Documents")

# Header Banner
st.markdown(
    """
    <div style="background-color: #f0f7f2; border-left: 5px solid #0A4D20; padding: 12px 20px; border-radius: 6px; margin-bottom: 25px;">
        <span style="color: #0A4D20; font-weight: 600; font-size: 18px;">📂 Document & Attachment Hub</span>
        <span style="color: #555555; font-size: 14px; margin-left: 10px;">| Public Works Technical Reports & File Attachments</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Project Registry Master List")
# ... (Your SQLite database query & table rendering code goes here) ...

st.markdown("---")

# --- 5. STYLED ATTACHMENT VIEWER ---
st.subheader("📎 Project Attachment Viewer")

projects = [
    "kahuti-ini Pry Sch",
    "Nyeri General Hospital Wing",
    "Mukurwe-ini Water Works",
]
selected_project = st.selectbox(
    "Select Project to Inspect Attachment", projects
)

sample_filename = "Nyeri_Public_Works_Report.xlsx"
st.markdown(
    f"**Filename:** <span class='filename-badge'>{sample_filename}</span>",
    unsafe_allow_html=True,
)

dummy_data = b"Nyeri County Government Public Works Sample Excel Attachment"
st.download_button(
    label=f"📥 Download {sample_filename}",
    data=dummy_data,
    file_name=sample_filename,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=False,
)
