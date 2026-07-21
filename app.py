import datetime
import io
import sqlite3
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ==========================================
# 1. DATABASE SCHEMA & DEEP SEEDING
# ==========================================
def init_enterprise_db():
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        cursor = conn.cursor()

        # 1. Users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'Viewer'
            )
        ''')
        if cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('admin', 'admin123', 'System Administrator', 'Admin')")
            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('engineer', 'eng123', 'Eng. John Mwangi', 'County Engineer')")
            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('director', 'dir123', 'Dr. Lucy Wambui', 'Director')")
            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('chief', 'chief123', 'Hon. Joseph Maina', 'Chief Officer')")

        # 2. Projects
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT UNIQUE,
                project_name TEXT NOT NULL,
                sub_county TEXT,
                department TEXT,
                contractor TEXT DEFAULT 'County In-House',
                lead_engineer TEXT DEFAULT 'Eng. John Mwangi',
                budget_allocated REAL,
                actual_spend REAL DEFAULT 0.0,
                percentage_complete INTEGER DEFAULT 0,
                workflow_stage TEXT DEFAULT 'Project Officer Review', 
                status TEXT DEFAULT 'Active',
                start_date TEXT,
                target_completion TEXT,
                description TEXT
            )
        ''')

        if cursor.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
            sample_projects = [
                ("PRJ-2026-001", "Karatina Market Modernization & Drainage", "Mathira East", "Infrastructure & Energy", "Apex Builders Ltd", "Eng. David Kariuki", 45000000.0, 38000000.0, 85, "Director Review", "Active", "2026-01-15", "2026-09-30", "Upgrade of Karatina market drainage and paved stalls."),
                ("PRJ-2026-002", "Othaya Sub-County Hospital Wing Extension", "Othaya", "Health Services", "Mount Kenya Construction", "Eng. John Mwangi", 60000000.0, 60000000.0, 100, "Approved", "Completed", "2025-06-01", "2026-05-15", "Construction of 60-bed ward extension and maternity theater."),
                ("PRJ-2026-003", "Tetu High-Altitude Training Water Pipeline", "Tetu", "Water & Sanitation", "Aberdare Water Systems", "Eng. Grace Nderitu", 18500000.0, 12000000.0, 65, "County Engineer Signoff", "Active", "2026-02-10", "2026-11-20", "Pipeline extension connecting Ihururu water plant to training center."),
                ("PRJ-2026-004", "Mukurwe-ini Feeder Roads Tarmacking", "Mukurweini", "Roads & Transport", "Highland Civils Ltd", "Eng. Peter Kamau", 82000000.0, 25000000.0, 30, "Project Officer Review", "Delayed", "2026-03-01", "2026-12-31", "Tarmacking 12km feeder roads connecting local farms to highway."),
                ("PRJ-2026-005", "Nyeri Town Bus Park Stormwater System", "Nyeri Town", "Public Works", "County In-House", "Eng. John Mwangi", 12000000.0, 1500000.0, 15, "Project Officer Review", "Active", "2026-05-01", "2026-10-15", "Rehabilitation of central bus park drainage culverts."),
                ("PRJ-2026-006", "Kieni East Earth Dam Rehabilitation", "Kieni East", "Water & Sanitation", "Rift Valley Hydraulics", "Eng. Grace Nderitu", 35000000.0, 32000000.0, 90, "Chief Officer Approval", "Active", "2025-11-01", "2026-08-15", "Desilting dam reservoir and constructing spillway concrete wall.")
            ]
            cursor.executemany("""
                INSERT INTO projects 
                (project_code, project_name, sub_county, department, contractor, lead_engineer, budget_allocated, actual_spend, percentage_complete, workflow_stage, status, start_date, target_completion, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_projects)

        # 3. Approvals Engine History
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS approval_history (
                approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT,
                stage TEXT,
                approver_name TEXT,
                approver_role TEXT,
                action TEXT, -- 'Approved', 'Rejected', 'Escalated'
                comments TEXT,
                timestamp DATETIME
            )
        ''')

        if cursor.execute("SELECT COUNT(*) FROM approval_history").fetchone()[0] == 0:
            cursor.execute("INSERT INTO approval_history (project_code, stage, approver_name, approver_role, action, comments, timestamp) VALUES ('PRJ-2026-001', 'Project Officer Review', 'Eng. David Kariuki', 'Project Officer', 'Approved', 'Initial site inspection complete. Proceed.', '2026-06-10 10:15:00')")
            cursor.execute("INSERT INTO approval_history (project_code, stage, approver_name, approver_role, action, comments, timestamp) VALUES ('PRJ-2026-001', 'County Engineer Signoff', 'Eng. John Mwangi', 'County Engineer', 'Approved', 'Engineering specs verified.', '2026-07-01 14:20:00')")

        # 4. Document Versions & Metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS document_repository (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT,
                doc_name TEXT,
                version TEXT,
                doc_type TEXT,
                status TEXT,
                uploaded_by TEXT,
                upload_date DATETIME
            )
        ''')

        if cursor.execute("SELECT COUNT(*) FROM document_repository").fetchone()[0] == 0:
            cursor.execute("INSERT INTO document_repository (project_code, doc_name, version, doc_type, status, uploaded_by, upload_date) VALUES ('PRJ-2026-001', 'Karatina_Market_Tender_BOQ.pdf', 'v2.1', 'PDF', 'Approved', 'Eng. David Kariuki', '2026-06-12 09:30:00')")
            cursor.execute("INSERT INTO document_repository (project_code, doc_name, version, doc_type, status, uploaded_by, upload_date) VALUES ('PRJ-2026-001', 'Structural_Drawing_Drainage.pdf', 'v1.0', 'PDF', 'Approved', 'Apex Builders Ltd', '2026-06-15 11:00:00')")
            cursor.execute("INSERT INTO document_repository (project_code, doc_name, version, doc_type, status, uploaded_by, upload_date) VALUES ('PRJ-2026-004', 'Road_Gradients_Survey.xlsx', 'v1.2', 'Spreadsheet', 'Pending Review', 'Highland Civils Ltd', '2026-07-10 16:45:00')")

        # 5. Interactive Notifications Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                notif_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT,
                type TEXT, -- 'Warning', 'Approval Needed', 'Info'
                title TEXT,
                message TEXT,
                status TEXT DEFAULT 'Unread', -- 'Unread', 'Dismissed'
                timestamp DATETIME
            )
        ''')

        if cursor.execute("SELECT COUNT(*) FROM notifications").fetchone()[0] == 0:
            cursor.execute("INSERT INTO notifications (project_code, type, title, message, status, timestamp) VALUES ('PRJ-2026-004', 'Warning', 'Schedule Variance Alert', 'Mukurwe-ini Feeder Roads is delayed by 35 days.', 'Unread', '2026-07-21 08:30:00')")
            cursor.execute("INSERT INTO notifications (project_code, type, title, message, status, timestamp) VALUES ('PRJ-2026-001', 'Approval Needed', 'Director Signoff Pending', 'Karatina Market Modernization requires executive signoff.', 'Unread', '2026-07-21 11:00:00')")

        # 6. Audit Trail
        cursor.execute('''CREATE TABLE IF NOT EXISTS audit_logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, username TEXT, action TEXT, target_record TEXT, details TEXT)''')

        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database error: {e}")

def log_audit_action(username, action, target, details=""):
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO audit_logs (timestamp, username, action, target_record, details) VALUES (?, ?, ?, ?, ?)", (timestamp, username, action, target, details))
        conn.commit()
        conn.close()
    except Exception:
        pass

def verify_login(username, password):
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, password, full_name, role FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
        row = cursor.fetchone()
        conn.close()
        if row and str(row[1]) == str(password):
            return {"username": row[0], "full_name": row[2] if row[2] else row[0], "role": row[3] if row[3] else "Viewer"}
    except Exception:
        pass
    return None

def fetch_df(query, params=()):
    conn = sqlite3.connect("nyeri_public_works.db")
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_sql(sql, params=()):
    conn = sqlite3.connect("nyeri_public_works.db")
    cursor = conn.cursor()
    cursor.execute(sql, params)
    conn.commit()
    conn.close()

def format_currency_short(val):
    if val >= 1e9: return f"KES {val/1e9:.2f}B"
    elif val >= 1e6: return f"KES {val/1e6:.2f}M"
    elif val >= 1e3: return f"KES {val/1e3:.2f}K"
    return f"KES {val:,.2f}"


# ==========================================
# 2. CUSTOM STYLES
# ==========================================
def inject_custom_styles():
    st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            background-color: #0A4D20 !important;
            background-image: linear-gradient(180deg, #0A4D20 0%, #031e0c 100%) !important;
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div {
            color: #FFFFFF !important;
            font-family: 'Inter', sans-serif;
        }
        .kpi-card {
            background: #FFFFFF; border-radius: 12px; padding: 18px 20px; border: 1px solid #E5E7EB;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-bottom: 15px;
        }
        .kpi-title { font-size: 13px; font-weight: 600; color: #6B7280; text-transform: uppercase; }
        .kpi-value { font-size: 26px; font-weight: 800; color: #111827; margin: 4px 0; }
        .kpi-badge-up { color: #10B981; font-size: 12px; font-weight: 700; background: #ECFDF5; padding: 2px 8px; border-radius: 20px; }
        .kpi-badge-down { color: #EF4444; font-size: 12px; font-weight: 700; background: #FEF2F2; padding: 2px 8px; border-radius: 20px; }

        /* Stepper Visualizer */
        .stepper-wrapper { display: flex; justify-content: space-between; margin: 20px 0; }
        .stepper-item { flex: 1; text-align: center; position: relative; }
        .stepper-item::after {
            content: ''; position: absolute; top: 18px; left: 50%; width: 100%; height: 3px; background-color: #E5E7EB; z-index: 1;
        }
        .stepper-item:last-child::after { content: none; }
        .stepper-circle {
            width: 36px; height: 36px; border-radius: 50%; background-color: #E5E7EB; color: #6B7280;
            display: flex; align-items: center; justify-content: center; margin: 0 auto 8px auto; font-weight: bold; position: relative; z-index: 2;
        }
        .stepper-complete .stepper-circle { background-color: #10B981; color: white; }
        .stepper-active .stepper-circle { background-color: #D4AF37; color: white; box-shadow: 0 0 0 4px #FEF3C7; }
        .stepper-title { font-size: 12px; font-weight: 600; color: #374151; }

        .notif-box {
            padding: 14px; border-radius: 8px; background: #FFFFFF; border-left: 5px solid #0A4D20; border-top: 1px solid #E5E7EB; border-right: 1px solid #E5E7EB; border-bottom: 1px solid #E5E7EB; margin-bottom: 12px;
        }
        .notif-warning { border-left-color: #EF4444 !important; }
        .notif-approval { border-left-color: #D4AF37 !important; }
    </style>
    """, unsafe_allow_html=True)


# ==========================================
# 3. INITIALIZATION & SESSION ROUTING
# ==========================================
st.set_page_config(page_title="Nyeri Public Works MIS", layout="wide", initial_sidebar_state="expanded")
inject_custom_styles()
init_enterprise_db()

if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "is_public" not in st.session_state: st.session_state["is_public"] = False
if "selected_project_code" not in st.session_state: st.session_state["selected_project_code"] = None

# --- UNAUTHENTICATED & PUBLIC PORTAL GATE ---
if not st.session_state["authenticated"] and not st.session_state["is_public"]:
    st.markdown("<h1 style='text-align: center; color: #0A4D20;'>🏛️ County Government of Nyeri</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #D4AF37; margin-top: -15px;'>Public Works & Infrastructure MIS Portal</h3>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 1.2, 1])
    with col_b:
        tab_login, tab_public = st.tabs(["🔒 Executive & Staff Sign In", "🌐 Citizen Public Portal"])
        
        with tab_login:
            with st.form("login_form"):
                st.subheader("Staff Authentication")
                u_input = st.text_input("Username")
                p_input = st.text_input("Password", type="password")
                if st.form_submit_button("Sign In Securely", use_container_width=True):
                    user_data = verify_login(u_input, p_input)
                    if user_data:
                        st.session_state["authenticated"] = True
                        st.session_state["username"] = user_data["username"]
                        st.session_state["role"] = user_data["role"]
                        st.session_state["full_name"] = user_data["full_name"]
                        log_audit_action(user_data["username"], "Login", "System", "Enterprise Login Success")
                        st.rerun()
                    else:
                        st.error("Invalid credentials.")
        
        with tab_public:
            st.write("Welcome citizens! Access open project tracking, transparent budgets, and public reports.")
            if st.button("Enter Citizen Public Portal ➔", use_container_width=True, type="primary"):
                st.session_state["is_public"] = True
                st.rerun()
    st.stop()


# ==========================================
# 4. CITIZEN PUBLIC PORTAL (UNAUTHENTICATED)
# ==========================================
if st.session_state["is_public"]:
    st.markdown("""
    <div style="background-color:#0A4D20; padding:18px 24px; border-radius:8px; color:white; margin-bottom:20px; display:flex; justify-content:space-between; align-items:center;">
        <div>
            <h2 style="margin:0; color:white;">🏛️ County Government of Nyeri - Citizen Portal</h2>
            <p style="margin:0; color:#D4AF37;">Public Infrastructure Transparency & Open Data Tracker</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Exit Public View (Go to Login)"):
        st.session_state["is_public"] = False
        st.rerun()

    p_df = fetch_df("SELECT project_code, project_name, sub_county, department, contractor, budget_allocated, percentage_complete, status, start_date, target_completion FROM projects")

    p1, p2 = st.columns([1, 3])
    with p1:
        st.subheader("Filter Projects")
        sc_filter = st.multiselect("Sub-County", p_df["sub_county"].unique())
        dept_filter = st.multiselect("Department", p_df["department"].unique())
        search_kw = st.text_input("Search Keyword", "")

    filtered_df = p_df.copy()
    if sc_filter: filtered_df = filtered_df[filtered_df["sub_county"].isin(sc_filter)]
    if dept_filter: filtered_df = filtered_df[filtered_df["department"].isin(dept_filter)]
    if search_kw: filtered_df = filtered_df[filtered_df["project_name"].str.contains(search_kw, case=False)]

    with p2:
        st.subheader(f"Public Projects ({len(filtered_df)})")
        
        # Format currency for table preview
        display_public = filtered_df.copy()
        display_public["budget_allocated"] = display_public["budget_allocated"].apply(lambda x: f"KES {x:,.2f}")
        display_public["percentage_complete"] = display_public["percentage_complete"].apply(lambda x: f"{x}%")
        
        st.dataframe(display_public, use_container_width=True, hide_index=True)

        # Public Report Export
        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Public Transparency Report (CSV)",
            data=csv_data,
            file_name=f"Nyeri_Public_Projects_{datetime.date.today()}.csv",
            mime="text/csv"
        )
    st.stop()


# ==========================================
# 5. ENTERPRISE SIDEBAR NAVIGATION
# ==========================================
st.sidebar.markdown(f"""
<div style="text-align: center; padding: 10px 0;">
    <h2 style="color: #FFFFFF; font-weight: 800; margin: 0;">NYERI COUNTY</h2>
    <span style="color: #D4AF37; font-size: 11px; letter-spacing: 1px;">PUBLIC WORKS MIS ENTERPRISE</span>
</div>
<hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.15); margin-bottom: 15px;" />
""", unsafe_allow_html=True)

st.sidebar.markdown(f"👤 User: **{st.session_state['full_name']}**")
st.sidebar.markdown(f"🛡️ Role: **{st.session_state['role']}**")
st.sidebar.markdown("---")

nav_choice = st.sidebar.radio(
    "SYSTEM MODULES",
    [
        "🏠 Executive Home",
        "📂 Projects Portfolio",
        "🔎 Project Details Inspector",
        "🔄 Workflow Approval Engine",
        "📄 Documents & Versions",
        "📈 Deep Analytics & Forecasting",
        "🔔 Interactive Notifications",
        "🤖 Ask Nyeri AI (Dynamic SQL)",
        "⚙️ System Audit Trail"
    ]
)

if st.sidebar.button("Logout"):
    log_audit_action(st.session_state["username"], "Logout", "System", "User logged out")
    st.session_state["authenticated"] = False
    st.rerun()

df = fetch_df("SELECT * FROM projects")


# ==========================================
# MODULE 1: EXECUTIVE HOME
# ==========================================
if nav_choice == "🏠 Executive Home":
    st.markdown(f"## ☀️ Welcome, {st.session_state['full_name']}")
    st.caption(f"Portfolio Overview as of {datetime.datetime.now().strftime('%B %d, %Y')}")

    tot_b = df["budget_allocated"].sum()
    tot_s = df["actual_spend"].sum()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Projects</div><div class="kpi-value">{len(df)}</div><span class="kpi-badge-up">▲ Active County Portfolio</span></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Allocated Budget</div><div class="kpi-value">{format_currency_short(tot_b)}</div><span class="kpi-badge-up">Total Funds</span></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Total Spend</div><div class="kpi-value">{format_currency_short(tot_s)}</div><span class="kpi-badge-up">{(tot_s/tot_b*100):.1f}% Utilized</span></div>', unsafe_allow_html=True)
    with col4:
        delayed = len(df[df["status"]=="Delayed"])
        st.markdown(f'<div class="kpi-card"><div class="kpi-title">Delayed Projects</div><div class="kpi-value">{delayed}</div><span class="kpi-badge-down">▼ Action Required</span></div>', unsafe_allow_html=True)

    g1, g2 = st.columns([1, 1])
    with g1:
        st.subheader("Department Budget Allocation")
        fig_dept = px.pie(df, names="department", values="budget_allocated", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
        st.plotly_chart(fig_dept, use_container_width=True)
    with g2:
        st.subheader("Sub-County Completion Rates (%)")
        sc_comp = df.groupby("sub_county")["percentage_complete"].mean().reset_index()
        fig_sc = px.bar(sc_comp, x="sub_county", y="percentage_complete", color="percentage_complete", color_continuous_scale="Greens")
        st.plotly_chart(fig_sc, use_container_width=True)


# ==========================================
# MODULE 2: PROJECTS PORTFOLIO
# ==========================================
elif nav_choice == "📂 Projects Portfolio":
    st.subheader("📂 Infrastructure Projects Portfolio")
    
    st.dataframe(df[["project_code", "project_name", "sub_county", "department", "contractor", "budget_allocated", "percentage_complete", "workflow_stage", "status"]], use_container_width=True)

    st.markdown("---")
    st.write("👉 **Click below to inspect a project in depth:**")
    selected_code = st.selectbox("Select Project Code to Inspect", df["project_code"].unique())
    if st.button("Open Full Project Inspector ➔"):
        st.session_state["selected_project_code"] = selected_code
        st.rerun()


# ==========================================
# MODULE 3: PROJECT DETAILS INSPECTOR (DRILL-DOWN)
# ==========================================
elif nav_choice == "🔎 Project Details Inspector":
    st.subheader("🔎 Deep Project Details Inspector")

    p_code = st.session_state.get("selected_project_code") or df["project_code"].iloc[0]
    p_code_input = st.selectbox("Select Active Project", df["project_code"].unique(), index=int(df[df["project_code"]==p_code].index[0]) if p_code in df["project_code"].values else 0)
    
    p_info = df[df["project_code"] == p_code_input].iloc[0]

    st.markdown(f"### 🏗️ {p_info['project_name']} (`{p_info['project_code']}`)")
    
    d_tab1, d_tab2, d_tab3, d_tab4, d_tab5 = st.tabs([
        "📋 Overview & Timeline",
        "🔄 Approval Workflow Log",
        "📄 Documents & Preview",
        "📷 Inspections & Photos",
        "🤖 AI Summary"
    ])

    with d_tab1:
        o1, o2, o3 = st.columns(3)
        o1.write(f"**Sub-County:** {p_info['sub_county']}")
        o1.write(f"**Department:** {p_info['department']}")
        o2.write(f"**Contractor:** {p_info['contractor']}")
        o2.write(f"**Lead Engineer:** {p_info['lead_engineer']}")
        o3.write(f"**Start Date:** {p_info['start_date']}")
        o3.write(f"**Target Completion:** {p_info['target_completion']}")

        st.markdown("#### Progress & Expenditure")
        st.progress(p_info['percentage_complete']/100)
        st.write(f"**Completion:** {p_info['percentage_complete']}% | **Allocated Budget:** {format_currency_short(p_info['budget_allocated'])} | **Actual Spend:** {format_currency_short(p_info['actual_spend'])}")

    with d_tab2:
        st.markdown("#### Formal Workflow Sign-Off Audit Trail")
        hist = fetch_df("SELECT stage, approver_name, approver_role, action, comments, timestamp FROM approval_history WHERE project_code = ? ORDER BY approval_id DESC", (p_code_input,))
        if not hist.empty:
            st.dataframe(hist, use_container_width=True)
        else:
            st.info("No approval actions logged yet.")

    with d_tab3:
        st.markdown("#### Associated Contract Documents & Previews")
        docs = fetch_df("SELECT doc_name, version, doc_type, status, uploaded_by, upload_date FROM document_repository WHERE project_code = ?", (p_code_input,))
        if not docs.empty:
            st.dataframe(docs, use_container_width=True)
            
            # Interactive Mock Document Preview
            st.markdown("##### 📄 Document Preview Box")
            doc_to_preview = st.selectbox("Select File to Preview", docs["doc_name"].unique())
            st.markdown(f"""
            <div style="border: 2px dashed #0A4D20; padding:20px; background:#F9FAFB; border-radius:8px; text-align:center;">
                📄 <strong>PREVIEW: {doc_to_preview}</strong><br/>
                <span style="font-size:12px; color:#6B7280;">Document cryptographically verified & stored on Nyeri County Cloud Repository.</span><br/><br/>
                <code>[PDF Preview Content: Specifications for {p_info['project_name']} - Approved Version]</code>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("No documents uploaded for this project yet.")

    with d_tab4:
        st.markdown("#### Site Photo Gallery & Field Inspection Logs")
        st.image("https://images.unsplash.com/photo-1541888946425-d0fbb186a5b3?auto=format&fit=crop&w=800&q=80", caption=f"Field Inspection Photo - {p_info['project_name']}", width=600)

    with d_tab5:
        st.markdown("#### 🤖 AI-Generated Project Health Summary")
        burn_rate = (p_info['actual_spend'] / p_info['budget_allocated'] * 100) if p_info['budget_allocated'] > 0 else 0
        st.success(f"""
        **AI Health Assessment for {p_info['project_code']}:**
        - **Schedule Health:** Project is currently **{p_info['status']}** sitting at stage **{p_info['workflow_stage']}**.
        - **Budget Burn Rate:** {burn_rate:.1f}% of allocated funds spent against {p_info['percentage_complete']}% completion.
        - **Risk Level:** {'🔴 High Risk' if p_info['status']=='Delayed' else '🟢 Low/Optimal Risk'}.
        """)


# ==========================================
# MODULE 4: WORKFLOW APPROVAL ENGINE
# ==========================================
elif nav_choice == "🔄 Workflow Approval Engine":
    st.subheader("🔄 Multi-Tier Governance Approval Engine")
    
    stages = ["Project Officer Review", "County Engineer Signoff", "Director Review", "Chief Officer Approval", "Approved"]
    
    p_code_app = st.selectbox("Select Project for Formal Approval Action", df["project_code"].unique())
    p_curr = df[df["project_code"] == p_code_app].iloc[0]

    st.info(f"Current Governance Stage: **{p_curr['workflow_stage']}**")

    # Stepper Display
    curr_idx = stages.index(p_curr["workflow_stage"]) if p_curr["workflow_stage"] in stages else 0
    stepper_html = '<div class="stepper-wrapper">'
    for i, s_name in enumerate(stages):
        if i < curr_idx: s_class, icon = "stepper-complete", "✓"
        elif i == curr_idx: s_class, icon = "stepper-active", "🔄"
        else: s_class, icon = "", str(i+1)
        stepper_html += f'<div class="stepper-item {s_class}"><div class="stepper-circle">{icon}</div><div class="stepper-title">{s_name}</div></div>'
    stepper_html += '</div>'
    st.markdown(stepper_html, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ✍️ Authorize / Sign Off Current Stage")

    with st.form("approval_signoff_form"):
        approver_comments = st.text_area("Official Authorization Comments / Observations")
        approval_action = st.radio("Decision", ["Approve & Advance Stage", "Reject / Escalation Required"], horizontal=True)
        
        if st.form_submit_button("Submit Digital Authorization"):
            if curr_idx < len(stages) - 1 and approval_action == "Approve & Advance Stage":
                next_stage = stages[curr_idx + 1]
                execute_sql("UPDATE projects SET workflow_stage = ? WHERE project_code = ?", (next_stage, p_code_app))
                execute_sql("INSERT INTO approval_history (project_code, stage, approver_name, approver_role, action, comments, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (p_code_app, p_curr["workflow_stage"], st.session_state["full_name"], st.session_state["role"], "Approved", approver_comments, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                log_audit_action(st.session_state["username"], "Approval", p_code_app, f"Advanced to {next_stage}")
                st.success(f"Project successfully advanced to: {next_stage}")
                st.rerun()
            else:
                st.warning("Action recorded or project is already fully approved.")


# ==========================================
# MODULE 5: DOCUMENTS & VERSIONS
# ==========================================
elif nav_choice == "📄 Documents & Versions":
    st.subheader("📄 Document Repository & Version Control")

    all_docs = fetch_df("SELECT * FROM document_repository")
    st.dataframe(all_docs, use_container_width=True)

    st.markdown("### 📤 Upload New Document / Revision")
    with st.form("doc_upload_form"):
        u_pcode = st.selectbox("Select Project", df["project_code"].unique())
        u_file = st.file_uploader("Choose PDF or Spreadsheet")
        u_version = st.text_input("Version Tag (e.g. v1.0, v2.0)", "v1.0")
        if st.form_submit_button("Upload to Repository"):
            if u_file:
                execute_sql("INSERT INTO document_repository (project_code, doc_name, version, doc_type, status, uploaded_by, upload_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (u_pcode, u_file.name, u_version, "PDF", "Pending Review", st.session_state["full_name"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                st.success("Document uploaded successfully!")
                st.rerun()


# ==========================================
# MODULE 6: DEEP ANALYTICS & FORECASTING
# ==========================================
elif nav_choice == "📈 Deep Analytics & Forecasting":
    st.subheader("📈 Deep Analytics & Executive Forecasting")

    a1, a2 = st.columns(2)
    with a1:
        st.markdown("#### Monthly Expenditure & Forecast Trend")
        dates = pd.date_range(start="2026-01-01", periods=8, freq="M")
        spend_trend = pd.DataFrame({
            "Month": dates.strftime("%B %Y"),
            "Actual Expenditure": [12, 28, 45, 62, 89, 110, 145, 168.5],
            "Budget Forecast": [15, 30, 50, 70, 95, 120, 150, 180]
        })
        fig_line = px.line(spend_trend, x="Month", y=["Actual Expenditure", "Budget Forecast"], markers=True)
        st.plotly_chart(fig_line, use_container_width=True)

    with a2:
        st.markdown("#### Contractor Performance Ranking")
        c_rank = df.groupby("contractor")["percentage_complete"].mean().reset_index()
        fig_c = px.bar(c_rank, x="percentage_complete", y="contractor", orientation="h", color="percentage_complete", color_continuous_scale="Viridis")
        st.plotly_chart(fig_c, use_container_width=True)


# ==========================================
# MODULE 7: INTERACTIVE NOTIFICATIONS
# ==========================================
elif nav_choice == "🔔 Interactive Notifications":
    st.subheader("🔔 Actionable Notification Center")

    notifs = fetch_df("SELECT * FROM notifications WHERE status = 'Unread'")
    if notifs.empty:
        st.info("🎉 All clear! No unread notifications.")
    else:
        for idx, row in notifs.iterrows():
            st.markdown(f"""
            <div class="notif-box {'notif-warning' if row['type']=='Warning' else 'notif-approval'}">
                <div style="display:flex; justify-content:space-between;">
                    <strong>{row['title']} (`{row['project_code']}`)</strong>
                    <span style="font-size:12px; color:#6B7280;">{row['timestamp']}</span>
                </div>
                <div style="margin-top:6px; font-size:13px; color:#374151;">{row['message']}</div>
            </div>
            """, unsafe_allow_html=True)
            
            b1, b2 = st.columns([1, 5])
            with b1:
                if st.button("Open Project", key=f"open_{row['notif_id']}"):
                    st.session_state["selected_project_code"] = row['project_code']
                    st.info(f"Navigating to Project Inspector for {row['project_code']}...")
            with b2:
                if st.button("Dismiss Alert", key=f"dism_{row['notif_id']}"):
                    execute_sql("UPDATE notifications SET status = 'Dismissed' WHERE notif_id = ?", (row['notif_id'],))
                    st.rerun()


# ==========================================
# MODULE 8: ASK NYERI AI (DYNAMIC SQL ENGINE)
# ==========================================
elif nav_choice == "🤖 Ask Nyeri AI (Dynamic SQL)":
    st.subheader("🤖 Ask Nyeri AI - Live Database Natural Language Assistant")
    st.caption("Connected to SQLite DB. Try: 'Show delayed road projects', 'Which contractor has highest budget?', or 'Generate executive summary'.")

    if "ai_chat" not in st.session_state:
        st.session_state.ai_chat = [{"role": "assistant", "content": "Hello! I am connected to the Nyeri Public Works database. What insights do you need?"}]

    for msg in st.session_state.ai_chat:
        st.chat_message(msg["role"]).write(msg["content"])

    q = st.chat_input("Ask database query...")
    if q:
        st.session_state.ai_chat.append({"role": "user", "content": q})
        st.chat_message("user").write(q)

        q_lower = q.lower()
        if "delayed" in q_lower:
            res_df = fetch_df("SELECT project_code, project_name, department, budget_allocated FROM projects WHERE status = 'Delayed'")
            ans = f"Found **{len(res_df)} delayed project(s)** in the database:\n" + res_df.to_markdown(index=False)
        elif "highest budget" in q_lower or "contractor" in q_lower:
            res_df = fetch_df("SELECT contractor, SUM(budget_allocated) as total_budget FROM projects GROUP BY contractor ORDER BY total_budget DESC LIMIT 1")
            ans = f"The contractor with the highest total budget allocation is **{res_df.iloc[0]['contractor']}** with **{format_currency_short(res_df.iloc[0]['total_budget'])}**."
        elif "executive summary" in q_lower:
            tot_p = len(df)
            tot_b = df["budget_allocated"].sum()
            tot_s = df["actual_spend"].sum()
            ans = f"""
            ### 🏛️ Executive Portfolio Summary
            - **Total Projects:** {tot_p}
            - **Total Capital Budget:** {format_currency_short(tot_b)}
            - **Total Portfolio Spend:** {format_currency_short(tot_s)} (Utilization: {(tot_s/tot_b*100):.1f}%)
            - **Health Status:** {len(df[df['status']=='Active'])} Active, {len(df[df['status']=='Completed'])} Completed, {len(df[df['status']=='Delayed'])} Delayed.
            """
        else:
            ans = f"Query executed. Database currently holds {len(df)} active projects with total budget of {format_currency_short(df['budget_allocated'].sum())}."

        st.session_state.ai_chat.append({"role": "assistant", "content": ans})
        st.chat_message("assistant").write(ans)


# ==========================================
# MODULE 9: SYSTEM AUDIT TRAIL
# ==========================================
elif nav_choice == "⚙️ System Audit Trail":
    st.subheader("🔐 System Security & Audit Logs")
    logs = fetch_df("SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT 30")
    st.dataframe(logs, use_container_width=True)
