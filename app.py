import datetime
import io
import sqlite3
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ==========================================
# 1. DATABASE SCHEMA & SEEDING WITH WORKFLOW PIPELINE
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

        # 2. Projects (Updated with Lifecycle Stage)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                project_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT UNIQUE,
                project_name TEXT NOT NULL,
                sub_county TEXT,
                department TEXT,
                contractor TEXT DEFAULT 'Unassigned',
                lead_engineer TEXT DEFAULT 'Eng. John Mwangi',
                budget_allocated REAL,
                actual_spend REAL DEFAULT 0.0,
                percentage_complete INTEGER DEFAULT 0,
                workflow_stage TEXT DEFAULT '1. Project Draft', 
                status TEXT DEFAULT '🔵 Planning',
                start_date TEXT,
                target_completion TEXT,
                description TEXT
            )
        ''')

        if cursor.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
            sample_projects = [
                ("PRJ-2026-001", "Karatina Market Modernization & Drainage", "Mathira East", "Infrastructure & Energy", "Apex Builders Ltd", "Eng. David Kariuki", 45000000.0, 38000000.0, 85, "4. Director Review", "🟠 In Progress", "2026-01-15", "2026-09-30", "Upgrade of Karatina market drainage and paved stalls."),
                ("PRJ-2026-002", "Othaya Sub-County Hospital Wing Extension", "Othaya", "Health Services", "Mount Kenya Construction", "Eng. John Mwangi", 60000000.0, 60000000.0, 100, "10. Completion", "🟢 Completed", "2025-06-01", "2026-05-15", "Construction of 60-bed ward extension and maternity theater."),
                ("PRJ-2026-003", "Tetu High-Altitude Training Water Pipeline", "Tetu", "Water & Sanitation", "Aberdare Water Systems", "Eng. Grace Nderitu", 18500000.0, 12000000.0, 65, "7. Construction", "🟠 In Progress", "2026-02-10", "2026-11-20", "Pipeline extension connecting Ihururu water plant to training center."),
                ("PRJ-2026-004", "Mukurwe-ini Feeder Roads Tarmacking", "Mukurweini", "Roads & Transport", "Highland Civils Ltd", "Eng. Peter Kamau", 82000000.0, 25000000.0, 30, "3. Engineer Review", "🔴 Delayed", "2026-03-01", "2026-12-31", "Tarmacking 12km feeder roads connecting local farms to highway."),
                ("PRJ-2026-005", "Nyeri Town Bus Park Stormwater System", "Nyeri Town", "Public Works", "County In-House", "Eng. John Mwangi", 12000000.0, 1500000.0, 15, "2. Upload BOQ", "🔵 Planning", "2026-05-01", "2026-10-15", "Rehabilitation of central bus park drainage culverts."),
                ("PRJ-2026-006", "Kieni East Earth Dam Rehabilitation", "Kieni East", "Water & Sanitation", "Rift Valley Hydraulics", "Eng. Grace Nderitu", 35000000.0, 32000000.0, 90, "8. Field Inspection", "🟠 In Progress", "2025-11-01", "2026-08-15", "Desilting dam reservoir and constructing spillway concrete wall.")
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
                action TEXT,
                comments TEXT,
                timestamp DATETIME
            )
        ''')

        # 4. Document Versions
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

        # 5. Interactive Notifications Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                notif_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT,
                type TEXT,
                title TEXT,
                message TEXT,
                status TEXT DEFAULT 'Unread',
                timestamp DATETIME
            )
        ''')

        if cursor.execute("SELECT COUNT(*) FROM notifications").fetchone()[0] == 0:
            cursor.execute("INSERT INTO notifications (project_code, type, title, message, status, timestamp) VALUES ('PRJ-2026-004', 'Warning', 'Budget & Schedule Variance Alert', 'Mukurwe-ini Feeder Roads is delayed by 35 days.', 'Unread', '2026-07-21 08:30:00')")
            cursor.execute("INSERT INTO notifications (project_code, type, title, message, status, timestamp) VALUES ('PRJ-2026-001', 'Approval Needed', 'Director Signoff Pending', 'Karatina Market Modernization requires executive signoff.', 'Unread', '2026-07-21 11:00:00')")

        # 6. Audit Trail & Real-time Activity Log
        cursor.execute('''CREATE TABLE IF NOT EXISTS audit_logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, username TEXT, action TEXT, target_record TEXT, details TEXT)''')
        
        if cursor.execute("SELECT COUNT(*) FROM audit_logs").fetchone()[0] == 0:
            cursor.execute("INSERT INTO audit_logs (timestamp, username, action, target_record, details) VALUES ('2026-07-21 09:20:00', 'eng123', 'Project Update', 'PRJ-2026-004', 'Eng. Peter Kamau updated construction progress logs.')")
            cursor.execute("INSERT INTO audit_logs (timestamp, username, action, target_record, details) VALUES ('2026-07-21 10:05:00', 'dir123', 'Workflow Approval', 'PRJ-2026-001', 'Dr. Lucy Wambui approved BOQ documentation.')")
            cursor.execute("INSERT INTO audit_logs (timestamp, username, action, target_record, details) VALUES ('2026-07-21 10:42:00', 'admin', 'Budget Reallocation', 'PRJ-2026-003', 'Approved contingency expenditure adjustment of KES 1.2M.')")

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
# 2. CUSTOM STYLES & COLOR SCHEME
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
        
        /* Decision Center Cards */
        .dec-card {
            background: #FFFFFF; border-radius: 10px; padding: 16px 18px; border: 1px solid #E5E7EB;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); text-align: left;
        }
        .dec-title { font-size: 12px; font-weight: 700; color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px; }
        .dec-value { font-size: 24px; font-weight: 800; color: #111827; margin: 4px 0; }
        .dec-sub { font-size: 11px; font-weight: 600; }
        
        .status-completed { color: #10B981; background: #ECFDF5; padding: 2px 8px; border-radius: 12px; font-weight:700; font-size:12px; }
        .status-progress { color: #F59E0B; background: #FEF3C7; padding: 2px 8px; border-radius: 12px; font-weight:700; font-size:12px; }
        .status-delayed { color: #EF4444; background: #FEF2F2; padding: 2px 8px; border-radius: 12px; font-weight:700; font-size:12px; }
        .status-planning { color: #3B82F6; background: #EFF6FF; padding: 2px 8px; border-radius: 12px; font-weight:700; font-size:12px; }

        /* Timeline feed */
        .timeline-item { padding: 10px 0; border-bottom: 1px solid #F3F4F6; }
        .timeline-time { font-size: 11px; font-weight: 700; color: #0A4D20; }
        .timeline-desc { font-size: 13px; color: #374151; margin-top: 2px; }
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

# --- UNAUTHENTICATED / CITIZEN GATE ---
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
# 4. CITIZEN PUBLIC PORTAL
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
        st.subheader(f"Public Infrastructure Projects ({len(filtered_df)})")
        display_public = filtered_df.copy()
        display_public["budget_allocated"] = display_public["budget_allocated"].apply(lambda x: f"KES {x:,.2f}")
        display_public["percentage_complete"] = display_public["percentage_complete"].apply(lambda x: f"{x}%")
        
        st.dataframe(display_public, use_container_width=True, hide_index=True)

        csv_data = filtered_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Public Transparency Report (CSV)",
            data=csv_data,
            file_name=f"Nyeri_Public_Projects_{datetime.date.today()}.csv",
            mime="text/csv"
        )
    st.stop()


# ==========================================
# 5. GLOBAL TOP HEADER (SEARCH + NOTIFICATIONS)
# ==========================================
df = fetch_df("SELECT * FROM projects")

h1, h2, h3 = st.columns([3, 1, 1])
with h1:
    search_query = st.text_input("🔍 Global Search (Project, Contractor, Engineer, Sub-County)...", key="global_search")
with h2:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    unread_cnt = len(fetch_df("SELECT * FROM notifications WHERE status = 'Unread'"))
    with st.expander(f"🔔 Notifications ({unread_cnt})"):
        notif_data = fetch_df("SELECT * FROM notifications WHERE status = 'Unread'")
        if notif_data.empty:
            st.write("No unread alerts.")
        else:
            for _, n in notif_data.iterrows():
                st.markdown(f"**{n['title']}**\n\n{n['message']}")
                st.divider()
with h3:
    st.markdown(f"<div style='margin-top: 28px; text-align:right;'><strong>{st.session_state['full_name']}</strong><br/><span style='font-size:12px; color:#6B7280;'>{st.session_state['role']}</span></div>", unsafe_allow_html=True)

st.markdown("---")


# ==========================================
# 6. ENTERPRISE SIDEBAR WITH ICONS
# ==========================================
st.sidebar.markdown(f"""
<div style="text-align: center; padding: 10px 0;">
    <h2 style="color: #FFFFFF; font-weight: 800; margin: 0;">NYERI COUNTY</h2>
    <span style="color: #D4AF37; font-size: 11px; letter-spacing: 1px;">PUBLIC WORKS MIS ENTERPRISE</span>
</div>
<hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.15); margin-bottom: 15px;" />
""", unsafe_allow_html=True)

nav_choice = st.sidebar.radio(
    "NAVIGATION MODULES",
    [
        "🏠 Executive Decision Centre",
        "📁 Projects Portfolio",
        "🔎 Project Details Inspector",
        "🔄 End-to-End Workflow Pipeline",
        "📄 Documents & Versioning",
        "📊 Deep Analytics & Forecasting",
        "🔔 Interactive Notifications",
        "🤖 Ask Nyeri AI Assistant",
        "⚙️ Settings & System Audit Trail"
    ]
)

if st.sidebar.button("Logout"):
    log_audit_action(st.session_state["username"], "Logout", "System", "User logged out")
    st.session_state["authenticated"] = False
    st.rerun()


# ==========================================
# GLOBAL SEARCH OVERRIDE
# ==========================================
if search_query:
    st.subheader(f"🔎 Global Search Results for: '{search_query}'")
    s_results = df[
        df["project_name"].str.contains(search_query, case=False) |
        df["contractor"].str.contains(search_query, case=False) |
        df["lead_engineer"].str.contains(search_query, case=False) |
        df["sub_county"].str.contains(search_query, case=False)
    ]
    st.dataframe(s_results, use_container_width=True)
    st.stop()


# ==========================================
# MODULE 1: EXECUTIVE DECISION CENTRE
# ==========================================
if nav_choice == "🏠 Executive Decision Centre":
    
    # ⚡ QUICK ACTIONS BAR
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        with st.popover("➕ New Project"):
            with st.form("quick_new_prj"):
                np_code = st.text_input("Project Code", f"PRJ-2026-00{len(df)+1}")
                np_name = st.text_input("Project Name")
                np_sc = st.selectbox("Sub-County", ["Mathira East", "Othaya", "Tetu", "Mukurweini", "Nyeri Town", "Kieni East"])
                np_dept = st.selectbox("Department", ["Infrastructure & Energy", "Health Services", "Water & Sanitation", "Roads & Transport", "Public Works"])
                np_budget = st.number_input("Allocated Budget (KES)", min_value=100000.0, value=10000000.0)
                if st.form_submit_button("Submit New Project"):
                    execute_sql("INSERT INTO projects (project_code, project_name, sub_county, department, budget_allocated, workflow_stage, status, start_date, target_completion) VALUES (?, ?, ?, ?, ?, '1. Project Draft', '🔵 Planning', ?, ?)",
                                (np_code, np_name, np_sc, np_dept, np_budget, datetime.date.today().strftime("%Y-%m-%d"), "2026-12-31"))
                    log_audit_action(st.session_state["username"], "Quick Action", np_code, f"Created new project {np_name}")
                    st.success("Project initialized!")
                    st.rerun()
    with q2:
        with st.popover("📄 Upload BOQ / Document"):
            st.write("Quick upload tender document or BOQ spreadsheet directly to repository.")
            u_p = st.selectbox("Select Target Project", df["project_code"].unique())
            u_f = st.file_uploader("Choose BOQ File")
            if st.button("Upload to Pipeline"):
                if u_f:
                    execute_sql("INSERT INTO document_repository (project_code, doc_name, version, doc_type, status, uploaded_by, upload_date) VALUES (?, ?, 'v1.0', 'BOQ PDF', 'Approved', ?, ?)",
                                (u_p, u_f.name, st.session_state["full_name"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    st.success("Document attached!")
    with q3:
        if st.button("📊 Generate Executive Report", use_container_width=True):
            st.info("Executive Report generated and queued for download.")
    with q4:
        with st.popover("👤 Assign Lead Engineer"):
            a_p = st.selectbox("Select Project Code", df["project_code"].unique(), key="assign_p")
            a_e = st.selectbox("Select Lead Engineer", ["Eng. John Mwangi", "Eng. David Kariuki", "Eng. Grace Nderitu", "Eng. Peter Kamau"])
            if st.button("Assign Engineer"):
                execute_sql("UPDATE projects SET lead_engineer = ? WHERE project_code = ?", (a_e, a_p))
                log_audit_action(st.session_state["username"], "Assign Engineer", a_p, f"Assigned to {a_e}")
                st.success("Engineer assigned successfully!")

    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

    # 🏛️ DECISION CENTER METRICS (6 KPI RISK CARDS)
    req_approvals = len(df[df["workflow_stage"].str.contains("Review|Approval")])
    delayed_cnt = len(df[df["status"] == "🔴 Delayed"])
    tot_budget_risk = df[df["status"] == "🔴 Delayed"]["budget_allocated"].sum()
    
    m1, m2, m3, m4, m5, m6 = st.columns(6)
    with m1:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Awaiting Approval</div><div class="dec-value">{req_approvals}</div><span class="dec-sub status-progress">Action Needed</span></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Budget at Risk</div><div class="dec-value">{format_currency_short(tot_budget_risk)}</div><span class="dec-sub status-delayed">Delayed Capital</span></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Delayed Projects</div><div class="dec-value">{delayed_cnt}</div><span class="dec-sub status-delayed">Schedule Variance</span></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="dec-card"><div class="dec-title">High-Risk Contractors</div><div class="dec-value">1</div><span class="dec-sub status-delayed">Highland Civils</span></div>', unsafe_allow_html=True)
    with m5:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Pending Documents</div><div class="dec-value">3</div><span class="dec-sub status-planning">BOQs Awaiting Signoff</span></div>', unsafe_allow_html=True)
    with m6:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Upcoming Deadlines</div><div class="dec-value">2</div><span class="dec-sub status-progress">Due within 30 Days</span></div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    # 🧠 AI EXECUTIVE SUMMARY BRIEFING
    st.info(f"""
    🧠 **Today's Executive Operational Briefing:**
    - **Critical Bottlenecks:** **{delayed_cnt} project(s)** are currently behind schedule with **{format_currency_short(tot_budget_risk)}** in delayed capital.
    - **Pending Authorizations:** **{req_approvals} project approval(s)** are awaiting Director/Chief Officer sign-off in the pipeline.
    - **Departmental Expenditure:** **Roads & Transport** has registered the highest monthly budget utilization rate (78%), while **Water & Sanitation** leads in overall completion percentage (77.5%).
    """)

    # DECISION VISUALS & RECENT ACTIVITY FEED
    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.subheader("📊 Capital Allocation & Progress Overview")
        fig_main = px.scatter(df, x="percentage_complete", y="budget_allocated", size="budget_allocated", color="status",
                             hover_name="project_name", text="project_code",
                             color_discrete_map={"🟢 Completed":"#10B981", "🟠 In Progress":"#F59E0B", "🔴 Delayed":"#EF4444", "🔵 Planning":"#3B82F6"})
        st.plotly_chart(fig_main, use_container_width=True)

    with c_right:
        st.subheader("🕒 Recent Activity Feed")
        activities = fetch_df("SELECT timestamp, username, action, details FROM audit_logs ORDER BY log_id DESC LIMIT 5")
        for _, act in activities.iterrows():
            st.markdown(f"""
            <div class="timeline-item">
                <div class="timeline-time">⏱️ {act['timestamp']} - {act['username']}</div>
                <div class="timeline-desc"><strong>{act['action']}:</strong> {act['details']}</div>
            </div>
            """, unsafe_allow_html=True)


# ==========================================
# MODULE 2: PROJECTS PORTFOLIO
# ==========================================
elif nav_choice == "📁 Projects Portfolio":
    st.subheader("📁 Infrastructure Projects Portfolio")
    
    # Styled Table Preview with Color Coding
    display_df = df[["project_code", "project_name", "sub_county", "department", "contractor", "budget_allocated", "percentage_complete", "workflow_stage", "status"]].copy()
    display_df["budget_allocated"] = display_df["budget_allocated"].apply(lambda x: f"KES {x:,.2f}")
    display_df["percentage_complete"] = display_df["percentage_complete"].apply(lambda x: f"{x}%")
    
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.write("👉 **Inspect a project in depth:**")
    selected_code = st.selectbox("Select Project Code", df["project_code"].unique())
    if st.button("Open Project Inspector ➔"):
        st.session_state["selected_project_code"] = selected_code
        st.rerun()


# ==========================================
# MODULE 3: PROJECT DETAILS INSPECTOR
# ==========================================
elif nav_choice == "🔎 Project Details Inspector":
    st.subheader("🔎 Project Details Inspector")

    p_code = st.session_state.get("selected_project_code") or df["project_code"].iloc[0]
    p_code_input = st.selectbox("Select Active Project", df["project_code"].unique(), index=int(df[df["project_code"]==p_code].index[0]) if p_code in df["project_code"].values else 0)
    
    p_info = df[df["project_code"] == p_code_input].iloc[0]

    st.markdown(f"### 🏗️ {p_info['project_name']} (`{p_info['project_code']}`)")
    st.markdown(f"Status: **{p_info['status']}** | Stage: **{p_info['workflow_stage']}**")
    
    d_tab1, d_tab2, d_tab3, d_tab4 = st.tabs([
        "📋 Overview & Budget",
        "🔄 Workflow History",
        "📄 BOQ Documents & Previews",
        "📷 Field Inspections"
    ])

    with d_tab1:
        o1, o2, o3 = st.columns(3)
        o1.write(f"**Sub-County:** {p_info['sub_county']}")
        o1.write(f"**Department:** {p_info['department']}")
        o2.write(f"**Contractor:** {p_info['contractor']}")
        o2.write(f"**Lead Engineer:** {p_info['lead_engineer']}")
        o3.write(f"**Start Date:** {p_info['start_date']}")
        o3.write(f"**Target Completion:** {p_info['target_completion']}")

        st.markdown("#### Progress & Expenditure Balance")
        st.progress(p_info['percentage_complete']/100)
        st.write(f"**Completion Rate:** {p_info['percentage_complete']}% | **Allocated Budget:** {format_currency_short(p_info['budget_allocated'])} | **Actual Spend:** {format_currency_short(p_info['actual_spend'])}")

    with d_tab2:
        st.markdown("#### Approval Trail Log")
        hist = fetch_df("SELECT stage, approver_name, approver_role, action, comments, timestamp FROM approval_history WHERE project_code = ? ORDER BY approval_id DESC", (p_code_input,))
        if not hist.empty:
            st.dataframe(hist, use_container_width=True)
        else:
            st.info("No formal governance actions logged yet.")

    with d_tab3:
        st.markdown("#### Contract Documents & BOQ Repository")
        docs = fetch_df("SELECT doc_name, version, doc_type, status, uploaded_by, upload_date FROM document_repository WHERE project_code = ?", (p_code_input,))
        if not docs.empty:
            st.dataframe(docs, use_container_width=True)
        else:
            st.info("No documents uploaded for this project yet.")

    with d_tab4:
        st.markdown("#### Site Photo Inspection Logs")
        st.image("https://images.unsplash.com/photo-1541888946425-d0fbb186a5b3?auto=format&fit=crop&w=800&q=80", caption=f"Field Inspection Verification - {p_info['project_name']}", width=600)


# ==========================================
# MODULE 4: CONNECTED END-TO-END WORKFLOW PIPELINE
# ==========================================
elif nav_choice == "🔄 End-to-End Workflow Pipeline":
    st.subheader("🔄 Connected Project Lifecycle Management Pipeline")
    
    pipeline_stages = [
        "1. Project Draft",
        "2. Upload BOQ",
        "3. Engineer Review",
        "4. Director Review",
        "5. Chief Officer Approval",
        "6. Tender Award",
        "7. Construction",
        "8. Field Inspection",
        "9. Completion Review",
        "10. Completion",
        "11. Published to Citizen Portal"
    ]
    
    p_code_pipe = st.selectbox("Select Project to Advance Lifecycle", df["project_code"].unique())
    p_curr = df[df["project_code"] == p_code_pipe].iloc[0]

    st.info(f"Current Pipeline Stage: **{p_curr['workflow_stage']}** | Status: **{p_curr['status']}**")

    # Stepper Pipeline Display
    curr_stage_str = str(p_curr['workflow_stage'])
    curr_idx = 0
    for idx, stg in enumerate(pipeline_stages):
        if stg.lower() in curr_stage_str.lower() or curr_stage_str.startswith(stg.split(".")[0]):
            curr_idx = idx

    st.markdown("#### Project Lifecycle Progress Tracker")
    st.progress((curr_idx + 1) / len(pipeline_stages))
    
    st.markdown("---")
    st.markdown("### ✍️ Execute Pipeline Governance Action")

    with st.form("pipeline_advance_form"):
        p_comments = st.text_area("Official Authorization Notes / Directives")
        next_stage_selected = st.selectbox("Advance Stage To", pipeline_stages, index=min(curr_idx + 1, len(pipeline_stages)-1))
        
        # Automatic Status Mapping
        if "Completion" in next_stage_selected or "Citizen Portal" in next_stage_selected:
            new_status = "🟢 Completed"
        elif "Construction" in next_stage_selected or "Inspection" in next_stage_selected:
            new_status = "🟠 In Progress"
        elif "Draft" in next_stage_selected or "BOQ" in next_stage_selected or "Review" in next_stage_selected or "Approval" in next_stage_selected:
            new_status = "🔵 Planning"
        else:
            new_status = p_curr["status"]

        if st.form_submit_button("Submit Pipeline Update"):
            execute_sql("UPDATE projects SET workflow_stage = ?, status = ? WHERE project_code = ?", (next_stage_selected, new_status, p_code_pipe))
            execute_sql("INSERT INTO approval_history (project_code, stage, approver_name, approver_role, action, comments, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (p_code_pipe, next_stage_selected, st.session_state["full_name"], st.session_state["role"], "Stage Advance", p_comments, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            log_audit_action(st.session_state["username"], "Pipeline Advance", p_code_pipe, f"Moved to {next_stage_selected}")
            st.success(f"Project updated to: {next_stage_selected}")
            st.rerun()


# ==========================================
# MODULE 5: DOCUMENTS & VERSIONING
# ==========================================
elif nav_choice == "📄 Documents & Versioning":
    st.subheader("📄 Document Repository & Versioning")

    all_docs = fetch_df("SELECT * FROM document_repository")
    st.dataframe(all_docs, use_container_width=True)

    st.markdown("### 📤 Upload New Version")
    with st.form("doc_upload_form"):
        u_pcode = st.selectbox("Select Project", df["project_code"].unique())
        u_file = st.file_uploader("Choose PDF or Spreadsheet")
        u_version = st.text_input("Version Tag", "v1.0")
        if st.form_submit_button("Attach to Project"):
            if u_file:
                execute_sql("INSERT INTO document_repository (project_code, doc_name, version, doc_type, status, uploaded_by, upload_date) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (u_pcode, u_file.name, u_version, "PDF", "Pending Review", st.session_state["full_name"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                log_audit_action(st.session_state["username"], "Document Upload", u_pcode, f"Uploaded {u_file.name} ({u_version})")
                st.success("Document attached to repository!")
                st.rerun()


# ==========================================
# MODULE 6: DEEP ANALYTICS & FORECASTING
# ==========================================
elif nav_choice == "📊 Deep Analytics & Forecasting":
    st.subheader("📊 Executive Analytics & Forecast Engine")

    a1, a2 = st.columns(2)
    with a1:
        st.markdown("#### Monthly Spend vs. Budget Target")
        dates = pd.date_range(start="2026-01-01", periods=8, freq="MS")
        spend_trend = pd.DataFrame({
            "Month": dates.strftime("%B %Y"),
            "Actual Expenditure": [12, 28, 45, 62, 89, 110, 145, 168.5],
            "Budget Forecast": [15, 30, 50, 70, 95, 120, 150, 180]
        })
        fig_line = px.line(spend_trend, x="Month", y=["Actual Expenditure", "Budget Forecast"], markers=True, color_discrete_sequence=["#0A4D20", "#D4AF37"])
        st.plotly_chart(fig_line, use_container_width=True)

    with a2:
        st.markdown("#### Contractor Execution Ranking")
        c_rank = df.groupby("contractor")["percentage_complete"].mean().reset_index()
        fig_c = px.bar(c_rank, x="percentage_complete", y="contractor", orientation="h", color="percentage_complete", color_continuous_scale="Greens")
        st.plotly_chart(fig_c, use_container_width=True)


# ==========================================
# MODULE 7: INTERACTIVE NOTIFICATIONS
# ==========================================
elif nav_choice == "🔔 Interactive Notifications":
    st.subheader("🔔 Notification & Alert Center")

    notifs = fetch_df("SELECT * FROM notifications WHERE status = 'Unread'")
    if notifs.empty:
        st.info("🎉 All notifications cleared.")
    else:
        for idx, row in notifs.iterrows():
            st.markdown(f"""
            <div style="padding:12px; border-left:4px solid {'#EF4444' if row['type']=='Warning' else '#D4AF37'}; background:white; margin-bottom:10px; border-radius:6px;">
                <strong>{row['title']} (`{row['project_code']}`)</strong><br/>
                <span style="font-size:13px; color:#374151;">{row['message']}</span>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Dismiss Alert", key=f"dism_{row['notif_id']}"):
                execute_sql("UPDATE notifications SET status = 'Dismissed' WHERE notif_id = ?", (row['notif_id'],))
                st.rerun()


# ==========================================
# MODULE 8: ASK NYERI AI ASSISTANT
# ==========================================
elif nav_choice == "🤖 Ask Nyeri AI Assistant":
    st.subheader("🤖 Ask Nyeri AI - Live Database Decision Assistant")

    if "ai_chat" not in st.session_state:
        st.session_state.ai_chat = [{"role": "assistant", "content": "Hello! I am connected to the Nyeri Public Works database. What decision metrics do you need?"}]

    for msg in st.session_state.ai_chat:
        st.chat_message(msg["role"]).write(msg["content"])

    q = st.chat_input("Ask database query...")
    if q:
        st.session_state.ai_chat.append({"role": "user", "content": q})
        st.chat_message("user").write(q)

        q_lower = q.lower()
        if "delayed" in q_lower:
            res_df = fetch_df("SELECT project_code, project_name, department, budget_allocated FROM projects WHERE status = '🔴 Delayed'")
            ans = f"Found **{len(res_df)} delayed project(s)** in the database:\n" + res_df.to_markdown(index=False)
        elif "highest budget" in q_lower or "contractor" in q_lower:
            res_df = fetch_df("SELECT contractor, SUM(budget_allocated) as total_budget FROM projects GROUP BY contractor ORDER BY total_budget DESC LIMIT 1")
            ans = f"The contractor with the highest total budget allocation is **{res_df.iloc[0]['contractor']}** with **{format_currency_short(res_df.iloc[0]['total_budget'])}**."
        elif "summary" in q_lower or "executive" in q_lower:
            tot_p = len(df)
            tot_b = df["budget_allocated"].sum()
            tot_s = df["actual_spend"].sum()
            ans = f"""
            ### 🏛️ Executive Summary
            - **Total Capital Projects:** {tot_p}
            - **Allocated Portfolio Budget:** {format_currency_short(tot_b)}
            - **Actual Expenditure:** {format_currency_short(tot_s)} ({(tot_s/tot_b*100):.1f}% utilization)
            """
        else:
            ans = f"Query processed. Current database has {len(df)} projects with total allocation of {format_currency_short(df['budget_allocated'].sum())}."

        st.session_state.ai_chat.append({"role": "assistant", "content": ans})
        st.chat_message("assistant").write(ans)


# ==========================================
# MODULE 9: SETTINGS & SYSTEM AUDIT TRAIL
# ==========================================
elif nav_choice == "⚙️ Settings & System Audit Trail":
    st.subheader("⚙️ Settings & System Audit Logs")
    logs = fetch_df("SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT 30")
    st.dataframe(logs, use_container_width=True)
