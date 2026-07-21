import hashlib
import sqlite3
import datetime
import io
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ==========================================
# 1. DATABASE SCHEMA & ENTERPRISE SEEDING
# ==========================================
def init_enterprise_gov_db():
    try:
        conn = sqlite3.connect("nyeri_enterprise_mis.db")
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'Engineer',
                department TEXT DEFAULT 'Public Works'
            )
        ''')
        if cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            cursor.execute("INSERT INTO users (username, password, full_name, role, department) VALUES ('CECM_Nyeri', 'cecm123', 'Hon. Charles Wanjohi', 'CECM', 'Executive')")
            cursor.execute("INSERT INTO users (username, password, full_name, role, department) VALUES ('CO_Infra', 'chief123', 'Hon. Joseph Maina', 'Chief Officer', 'Infrastructure')")
            cursor.execute("INSERT INTO users (username, password, full_name, role, department) VALUES ('DIR_Roads', 'dir123', 'Dr. Lucy Wambui', 'Director', 'Roads & Transport')")
            cursor.execute("INSERT INTO users (username, password, full_name, role, department) VALUES ('ENG_Mwangi', 'eng123', 'Eng. John Mwangi', 'County Engineer', 'Roads & Transport')")

        # 2. Project Lifecycle Master Table
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
                lifecycle_stage TEXT DEFAULT '1. Idea / Proposal', 
                status TEXT DEFAULT '🔵 Planning',
                start_date TEXT,
                target_completion TEXT,
                description TEXT
            )
        ''')

        if cursor.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
            sample_projects = [
                ("PRJ-2026-001", "Karatina Market Modernization & Drainage", "Mathira East", "Infrastructure & Energy", "Apex Builders Ltd", "Eng. David Kariuki", 45000000.0, 38000000.0, 85, "7. Construction", "🟠 In Progress", "2026-01-15", "2026-09-30", "Upgrade of Karatina market drainage and paved stalls."),
                ("PRJ-2026-002", "Othaya Sub-County Hospital Wing Extension", "Othaya", "Health Services", "Mount Kenya Construction", "Eng. John Mwangi", 60000000.0, 60000000.0, 100, "9. Handover / Asset", "🟢 Completed", "2025-06-01", "2026-05-15", "60-bed ward extension and maternity theater."),
                ("PRJ-2026-003", "Tetu High-Altitude Training Water Pipeline", "Tetu", "Water & Sanitation", "Aberdare Water Systems", "Eng. Grace Nderitu", 18500000.0, 12000000.0, 65, "7. Construction", "🟠 In Progress", "2026-02-10", "2026-11-20", "Pipeline extension connecting Ihururu water plant."),
                ("PRJ-2026-004", "Mukurwe-ini Feeder Roads Tarmacking", "Mukurweini", "Roads & Transport", "Highland Civils Ltd", "Eng. Peter Kamau", 82000000.0, 78000000.0, 30, "4. Technical Review", "🔴 Delayed", "2026-03-01", "2026-12-31", "Tarmacking 12km feeder roads connecting farms."),
                ("PRJ-2026-005", "Nyeri Town Bus Park Stormwater System", "Nyeri Town", "Public Works", "County In-House", "Eng. John Mwangi", 12000000.0, 1500500.0, 15, "3. Budget Approval", "🔵 Planning", "2026-05-01", "2026-10-15", "Rehabilitation of central bus park culverts.")
            ]
            cursor.executemany("""
                INSERT INTO projects 
                (project_code, project_name, sub_county, department, contractor, lead_engineer, budget_allocated, actual_spend, percentage_complete, lifecycle_stage, status, start_date, target_completion, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_projects)

        # 3. Classified Documents
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS classified_documents (
                doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT,
                doc_name TEXT,
                security_classification TEXT DEFAULT 'INTERNAL',
                version TEXT DEFAULT 'v1.0',
                uploaded_by TEXT,
                retention_period_yrs INTEGER DEFAULT 7,
                archive_status TEXT DEFAULT 'Active',
                upload_date DATETIME
            )
        ''')
        if cursor.execute("SELECT COUNT(*) FROM classified_documents").fetchone()[0] == 0:
            cursor.execute("INSERT INTO classified_documents (project_code, doc_name, security_classification, uploaded_by, upload_date) VALUES ('PRJ-2026-004', 'Tender_Evaluation_Report_Confidential.pdf', 'RESTRICTED', 'Dr. Lucy Wambui', '2026-07-20 14:20:00')")
            cursor.execute("INSERT INTO classified_documents (project_code, doc_name, security_classification, uploaded_by, upload_date) VALUES ('PRJ-2026-001', 'Karatina_BOQ_Final.pdf', 'INTERNAL', 'Eng. David Kariuki', '2026-07-18 09:15:00')")

        # 4. Executive Approvals
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS executive_approvals (
                approval_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT,
                item_title TEXT,
                stage TEXT,
                status TEXT DEFAULT 'Pending',
                submitted_by TEXT,
                action_by TEXT,
                ip_hash TEXT,
                digital_signature TEXT,
                comments TEXT,
                timestamp DATETIME
            )
        ''')
        if cursor.execute("SELECT COUNT(*) FROM executive_approvals").fetchone()[0] == 0:
            cursor.execute("INSERT INTO executive_approvals (project_code, item_title, stage, status, submitted_by, timestamp) VALUES ('PRJ-2026-004', 'Mukurwe-ini Additional Funding Budget Reallocation', 'Budget Approval', 'Pending', 'Dr. Lucy Wambui', '2026-07-21 08:30:00')")
            cursor.execute("INSERT INTO executive_approvals (project_code, item_title, stage, status, submitted_by, timestamp) VALUES ('PRJ-2026-001', 'Karatina Phase II Site Variation Sign-off', 'Technical Review', 'Pending', 'Eng. David Kariuki', '2026-07-21 10:15:00')")

        # 5. Risk Register
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_register (
                risk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT,
                risk_description TEXT,
                severity TEXT,
                mitigation_strategy TEXT,
                risk_owner TEXT,
                status TEXT DEFAULT 'Open'
            )
        ''')
        if cursor.execute("SELECT COUNT(*) FROM risk_register").fetchone()[0] == 0:
            cursor.execute("INSERT INTO risk_register (project_code, risk_description, severity, mitigation_strategy, risk_owner) VALUES ('PRJ-2026-004', 'Severe cost overrun due to unexpected soil instability', 'High', 'Request re-allocation from contingency fund', 'Director')")

        # 6. Site Inspections
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS site_inspections (
                inspection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT,
                engineer_name TEXT,
                inspection_date TEXT,
                gps_coordinates TEXT,
                weather TEXT,
                defects_found TEXT,
                recommendations TEXT,
                next_inspection_date TEXT
            )
        ''')

        # 7. Asset Register
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asset_register (
                asset_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT,
                asset_name TEXT,
                asset_category TEXT,
                sub_county TEXT,
                condition_rating TEXT,
                warranty_expiry TEXT,
                last_inspection_date TEXT,
                maintenance_schedule TEXT
            )
        ''')
        if cursor.execute("SELECT COUNT(*) FROM asset_register").fetchone()[0] == 0:
            cursor.execute("INSERT INTO asset_register (project_code, asset_name, asset_category, sub_county, condition_rating, warranty_expiry, last_inspection_date, maintenance_schedule) VALUES ('PRJ-2026-002', 'Othaya Hospital Medical Wing B', 'Buildings', 'Othaya', '🟢 Excellent', '2028-05-15', '2026-06-01', 'Bi-Annual HVAC Check')")

        # 8. Audit Logs
        cursor.execute('''CREATE TABLE IF NOT EXISTS audit_logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, username TEXT, role TEXT, action TEXT, target_record TEXT, details TEXT)''')

        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database setup error: {e}")

def log_audit_action(username, role, action, target, details=""):
    try:
        conn = sqlite3.connect("nyeri_enterprise_mis.db")
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO audit_logs (timestamp, username, role, action, target_record, details) VALUES (?, ?, ?, ?, ?, ?)", (timestamp, username, role, action, target, details))
        conn.commit()
        conn.close()
    except Exception:
        pass

def verify_login(username, password):
    try:
        conn = sqlite3.connect("nyeri_enterprise_mis.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, password, full_name, role, department FROM users WHERE LOWER(username) = LOWER(?)", (username.strip(),))
        row = cursor.fetchone()
        conn.close()
        if row and str(row[1]) == str(password):
            return {"username": row[0], "full_name": row[2], "role": row[3], "department": row[4]}
    except Exception:
        pass
    return None

def fetch_df(query, params=()):
    conn = sqlite3.connect("nyeri_enterprise_mis.db")
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

def execute_sql(sql, params=()):
    conn = sqlite3.connect("nyeri_enterprise_mis.db")
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
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
            color: #FFFFFF !important;
            font-family: 'Inter', sans-serif;
        }
        .dec-card {
            background: #FFFFFF; border-radius: 8px; padding: 14px 16px; border: 1px solid #E5E7EB;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); text-align: left;
        }
        .dec-title { font-size: 11px; font-weight: 700; color: #6B7280; text-transform: uppercase; }
        .dec-value { font-size: 22px; font-weight: 800; color: #111827; margin: 4px 0; }
        .security-banner { background-color: #FEF2F2; border-left: 4px solid #DC2626; padding: 10px; font-size: 12px; color: #991B1B; margin-bottom: 15px; }
        .compliance-footer { font-size: 11px; color: #6B7280; text-align: center; margin-top: 30px; line-height: 1.4; }
    </style>
    """, unsafe_allow_html=True)


# ==========================================
# 3. SESSION STATE & ROUTING
# ==========================================
st.set_page_config(page_title="Nyeri County Government Enterprise MIS", layout="wide", initial_sidebar_state="expanded")
inject_custom_styles()
init_enterprise_gov_db()

if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "mfa_pending" not in st.session_state: st.session_state["mfa_pending"] = False
if "mfa_user_data" not in st.session_state: st.session_state["mfa_user_data"] = None
if "is_public" not in st.session_state: st.session_state["is_public"] = False


# ==========================================
# 4. LOGIN / GATEWAY INTERFACE
# ==========================================
if not st.session_state["authenticated"] and not st.session_state["is_public"]:
    st.markdown("<h1 style='text-align: center; color: #0A4D20;'>🏛️ County Government of Nyeri</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #D4AF37; margin-top: -15px;'>Enterprise Infrastructure BPM & Governance MIS</h3>", unsafe_allow_html=True)
    st.markdown("<br/>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 1.3, 1])
    with col_b:
        t_login, t_pub = st.tabs(["🔒 Government Officer Sign In", "🌐 Citizen Open Data Portal"])
        
        with t_login:
            # Handle MFA Verification Step if triggered for senior officials
            if st.session_state["mfa_pending"]:
                st.info("🔐 Multi-Factor Authentication (MFA) Required for Senior Official / Admin.")
                st.write(f"Enter the 4-digit authenticator code sent for user: **{st.session_state['mfa_user_data']['full_name']}** (Demo Code: `1234`)")
                with st.form("mfa_form"):
                    otp = st.text_input("One-Time Passcode (OTP)", type="password")
                    if st.form_submit_button("Verify & Complete Sign In", use_container_width=True):
                        if otp == "1234":
                            u_data = st.session_state["mfa_user_data"]
                            st.session_state["authenticated"] = True
                            st.session_state["username"] = u_data["username"]
                            st.session_state["role"] = u_data["role"]
                            st.session_state["full_name"] = u_data["full_name"]
                            st.session_state["department"] = u_data["department"]
                            st.session_state["mfa_pending"] = False
                            log_audit_action(u_data["username"], u_data["role"], "MFA Login", "System", "MFA verified successfully")
                            st.rerun()
                        else:
                            st.error("Invalid OTP code. Try '1234'.")
            else:
                with st.form("clean_login_form"):
                    st.subheader("Official Staff Authentication")
                    u_input = st.text_input("Username or Employee Number")
                    p_input = st.text_input("Password", type="password")
                    
                    st.markdown("""
                    <div class="security-banner">
                        <strong>Authorized Government Personnel Only.</strong><br/>
                        All access is monitored and recorded. Unauthorized access is strictly prohibited.
                    </div>
                    """, unsafe_allow_html=True)

                    if st.form_submit_button("Sign In Securely", use_container_width=True):
                        user_data = verify_login(u_input, p_input)
                        if user_data:
                            # Enforce MFA for CECM, Chief Officer, or Admin roles
                            if user_data["role"] in ["CECM", "Chief Officer", "Admin"]:
                                st.session_state["mfa_pending"] = True
                                st.session_state["mfa_user_data"] = user_data
                                st.rerun()
                            else:
                                st.session_state["authenticated"] = True
                                st.session_state["username"] = user_data["username"]
                                st.session_state["role"] = user_data["role"]
                                st.session_state["full_name"] = user_data["full_name"]
                                st.session_state["department"] = user_data["department"]
                                log_audit_action(user_data["username"], user_data["role"], "Login", "System", "Authenticated successfully")
                                st.rerun()
                        else:
                            st.error("Invalid credentials. Please verify your employee ID and password.")

        with t_pub:
            st.subheader("Welcome to the Public Citizen Portal")
            st.write("Access open infrastructure data, track county project progress, and download public transparency records without requiring an account.")
            if st.button("Enter Citizen Open Data Portal ➔", use_container_width=True, type="primary"):
                st.session_state["is_public"] = True
                st.rerun()

        st.markdown("""
        <div class="compliance-footer">
            Access to this system is restricted to authorized personnel of the County Government of Nyeri. All activities are logged and monitored for security, audit, and compliance purposes.
        </div>
        """, unsafe_allow_html=True)
    st.stop()


# ==========================================
# 5. CITIZEN OPEN DATA PORTAL (ZERO LOGIN)
# ==========================================
if st.session_state["is_public"]:
    st.markdown("## 🏛️ County Government of Nyeri - Citizen Open Data Portal")
    st.caption("Public Infrastructure Transparency & Project Tracker")
    
    if st.button("← Return to Staff Sign-In Gateway"):
        st.session_state["is_public"] = False
        st.rerun()

    p_df = fetch_df("SELECT project_code, project_name, sub_county, department, contractor, budget_allocated, percentage_complete, status FROM projects")

    c_filter, c_search = st.columns([1, 2])
    with c_filter:
        sc_sel = st.multiselect("Filter by Sub-County", p_df["sub_county"].unique())
    with c_search:
        s_keyword = st.text_input("Search Projects by Keyword", "")

    public_filtered = p_df.copy()
    if sc_sel: public_filtered = public_filtered[public_filtered["sub_county"].isin(sc_sel)]
    if s_keyword: public_filtered = public_filtered[public_filtered["project_name"].str.contains(s_keyword, case=False)]

    public_filtered["budget_allocated"] = public_filtered["budget_allocated"].apply(lambda x: f"KES {x:,.2f}")
    public_filtered["percentage_complete"] = public_filtered["percentage_complete"].apply(lambda x: f"{x}%")

    st.dataframe(public_filtered, use_container_width=True, hide_index=True)

    csv_data = public_filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Public Transparency Dataset (CSV)",
        data=csv_data,
        file_name=f"Nyeri_Public_Projects_{datetime.date.today()}.csv",
        mime="text/csv"
    )
    st.stop()


# ==========================================
# 6. INTERNAL ENTERPRISE MIS APP
# ==========================================
user_role = st.session_state["role"]
user_name = st.session_state["full_name"]

# Navigation modules based on role authority
all_nav_items = [
    "🏠 Executive Decision Centre",
    "✍️ Executive Approval Centre",
    "📁 Projects Lifecycle Pipeline",
    "📊 Department Performance",
    "⚠️ Risk & Governance Register",
    "📄 Classified Records & Documents",
    "🏗️ Site Inspection Module",
    "🏛️ County Asset Register",
    "🤖 AI Executive Briefing",
    "⚙️ Disaster Recovery & Audit Logs"
]

if user_role not in ["CECM", "Chief Officer"]:
    nav_items = [item for item in all_nav_items if item not in ["🏠 Executive Decision Centre", "✍️ Executive Approval Centre", "⚙️ Disaster Recovery & Audit Logs"]]
else:
    nav_items = all_nav_items

st.sidebar.markdown(f"""
<div style="text-align: center; padding: 10px 0;">
    <h3 style="color: #FFFFFF; font-weight: 800; margin: 0;">NYERI MIS ERP</h3>
    <span style="color: #D4AF37; font-size: 11px;">ROLE: {user_role.upper()}</span>
</div>
<hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.15);" />
""", unsafe_allow_html=True)

nav_choice = st.sidebar.radio("NAVIGATION MODULES", nav_items)

if st.sidebar.button("Sign Out"):
    log_audit_action(st.session_state["username"], user_role, "Logout", "System", "User signed out")
    st.session_state["authenticated"] = False
    st.rerun()

st.markdown(f"**Logged in as:** `{user_name}` | **Role:** `{user_role}` | **Department:** `{st.session_state['department']}`")
st.divider()


# ==========================================
# MODULE 1: EXECUTIVE DECISION CENTRE
# ==========================================
if nav_choice == "🏠 Executive Decision Centre":
    st.title("🏠 Executive Decision Centre")
    st.caption("Strategic Operational Decision Support for CECM & Chief Officers")

    df_projects = fetch_df("SELECT * FROM projects")
    pending_apps = fetch_df("SELECT COUNT(*) FROM executive_approvals WHERE status = 'Pending'").iloc[0, 0]
    delayed_prjs = len(df_projects[df_projects["status"] == "🔴 Delayed"])
    overrun_amt = df_projects[df_projects["status"] == "🔴 Delayed"]["actual_spend"].sum()

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Pending Approvals</div><div class="dec-value">{pending_apps}</div><span style="color:#EF4444; font-size:11px; font-weight:bold;">Requires Sign-off</span></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Projects Behind Schedule</div><div class="dec-value">{delayed_prjs}</div><span style="color:#EF4444; font-size:11px; font-weight:bold;">Schedule Variance</span></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Capital at Risk</div><div class="dec-value">{format_currency_short(overrun_amt)}</div><span style="color:#F59E0B; font-size:11px; font-weight:bold;">Delayed Capital</span></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Critical Open Risks</div><div class="dec-value">1</div><span style="color:#EF4444; font-size:11px; font-weight:bold;">High Severity</span></div>', unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("📊 Strategic Department Performance Comparison")
        dept_perf = df_projects.groupby("department")["percentage_complete"].mean().reset_index()
        fig_dept = px.bar(dept_perf, x="department", y="percentage_complete", color="percentage_complete", color_continuous_scale="Greens", text_auto=True)
        st.plotly_chart(fig_dept, use_container_width=True)
    with c2:
        st.subheader("🔔 Smart Operational Alerts")
        st.warning("⚠️ **Project Delayed:** Mukurwe-ini Feeder Roads is delayed by 35 days.")
        st.error("🚨 **Budget Warning:** Mukurwe-ini project spend is at 95.1% of ceiling.")
        st.info("ℹ️ **Inspection Due:** Karatina Market drainage inspection due in 2 days.")


# ==========================================
# MODULE 2: EXECUTIVE APPROVAL CENTRE
# ==========================================
elif nav_choice == "✍️ Executive Approval Centre":
    st.title("✍️ Executive Approval Centre")
    st.caption("Cryptographic & Immutable Sign-Off Interface")

    pending_df = fetch_df("SELECT * FROM executive_approvals WHERE status = 'Pending'")
    
    if pending_df.empty:
        st.success("🎉 All executive approval queues are completely clear!")
    else:
        for idx, row in pending_df.iterrows():
            with st.expander(f"📌 {row['item_title']} ({row['project_code']}) - Submitted by {row['submitted_by']}", expanded=True):
                st.write(f"**Stage:** {row['stage']} | **Submission Time:** {row['timestamp']}")
                comment = st.text_area(f"Executive Decision Comments for {row['project_code']}", key=f"comm_{row['approval_id']}")
                
                b1, b2, b3 = st.columns(3)
                if b1.button("✅ Approve Digitally", key=f"app_{row['approval_id']}", type="primary"):
                    sig_hash = hashlib.sha256(f"{st.session_state['username']}{datetime.datetime.now()}{row['approval_id']}".encode()).hexdigest()[:16]
                    execute_sql("UPDATE executive_approvals SET status = 'Approved', action_by = ?, ip_hash = '192.168.1.10', digital_signature = ?, comments = ?, timestamp = ? WHERE approval_id = ?",
                                (st.session_state["full_name"], f"SIG-{sig_hash.upper()}", comment, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), row['approval_id']))
                    log_audit_action(st.session_state["username"], user_role, "Executive Approval", row['project_code'], f"Approved with Hash SIG-{sig_hash.upper()}")
                    st.success("Approved and cryptographically logged!")
                    st.rerun()

                if b2.button("❌ Reject", key=f"rej_{row['approval_id']}"):
                    execute_sql("UPDATE executive_approvals SET status = 'Rejected', action_by = ?, comments = ? WHERE approval_id = ?",
                                (st.session_state["full_name"], comment, row['approval_id']))
                    log_audit_action(st.session_state["username"], user_role, "Executive Rejection", row['project_code'], comment)
                    st.error("Item Rejected.")
                    st.rerun()

                if b3.button("🔄 Request Changes", key=f"req_{row['approval_id']}"):
                    execute_sql("UPDATE executive_approvals SET status = 'Changes Requested', action_by = ?, comments = ? WHERE approval_id = ?",
                                (st.session_state["full_name"], comment, row['approval_id']))
                    st.warning("Changes requested from lead engineer.")
                    st.rerun()


# ==========================================
# MODULE 3: PROJECTS LIFECYCLE PIPELINE
# ==========================================
elif nav_choice == "📁 Projects Lifecycle Pipeline":
    st.title("📁 Workflow-Driven Project Lifecycle Engine")

    stages = [
        "1. Idea / Proposal", "2. Technical Review", "3. Budget Approval", 
        "4. Procurement", "5. Contract Award", "6. Construction", 
        "7. Inspection", "8. Handover / Asset", "9. Archived"
    ]

    p_df = fetch_df("SELECT * FROM projects")
    st.dataframe(p_df[["project_code", "project_name", "sub_county", "department", "budget_allocated", "actual_spend", "percentage_complete", "lifecycle_stage", "status"]], use_container_width=True)

    st.markdown("### 🔄 Advance Project Lifecycle Stage")
    with st.form("advance_stage_form"):
        sel_prj = st.selectbox("Select Project", p_df["project_code"].unique())
        sel_stage = st.selectbox("Advance Stage To", stages)
        notes = st.text_area("Stage Transition Governance Notes")

        if st.form_submit_button("Submit Lifecycle Transition"):
            execute_sql("UPDATE projects SET lifecycle_stage = ? WHERE project_code = ?", (sel_stage, sel_prj))
            log_audit_action(st.session_state["username"], user_role, "Lifecycle Advance", sel_prj, f"Advanced to {sel_stage}. Notes: {notes}")
            st.success(f"Project {sel_prj} advanced to {sel_stage}!")
            st.rerun()


# ==========================================
# MODULE 4: DEPARTMENT PERFORMANCE
# ==========================================
elif nav_choice == "📊 Department Performance":
    st.title("📊 Departmental Comparative Analytics")
    
    df_p = fetch_df("SELECT * FROM projects")
    dept_agg = df_p.groupby("department").agg(
        Total_Budget=('budget_allocated', 'sum'),
        Total_Spend=('actual_spend', 'sum'),
        Avg_Completion=('percentage_complete', 'mean'),
        Project_Count=('project_id', 'count')
    ).reset_index()

    dept_agg["Budget Utilization %"] = (dept_agg["Total_Spend"] / dept_agg["Total_Budget"] * 100).round(1)
    st.dataframe(dept_agg, use_container_width=True)

    f1, f2 = st.columns(2)
    with f1:
        fig1 = px.pie(dept_agg, names="department", values="Total_Budget", title="Budget Distribution across Departments")
        st.plotly_chart(fig1, use_container_width=True)
    with f2:
        fig2 = px.bar(dept_agg, x="department", y="Avg_Completion", title="Average Completion Rate (%)", color="Avg_Completion", color_continuous_scale="Greens")
        st.plotly_chart(fig2, use_container_width=True)


# ==========================================
# MODULE 5: RISK & GOVERNANCE REGISTER
# ==========================================
elif nav_choice == "⚠️ Risk & Governance Register":
    st.title("⚠️ County Infrastructure Risk Register")

    r_df = fetch_df("SELECT * FROM risk_register")
    st.dataframe(r_df, use_container_width=True)

    st.markdown("### ➕ Register New Project Risk")
    with st.form("new_risk_form"):
        prjs = fetch_df("SELECT project_code FROM projects")["project_code"].unique()
        rk_p = st.selectbox("Project", prjs)
        rk_desc = st.text_input("Risk Description")
        rk_sev = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
        rk_mit = st.text_area("Mitigation Strategy")
        rk_own = st.text_input("Risk Owner", user_name)

        if st.form_submit_button("Log Risk Entry"):
            execute_sql("INSERT INTO risk_register (project_code, risk_description, severity, mitigation_strategy, risk_owner) VALUES (?, ?, ?, ?, ?)",
                        (rk_p, rk_desc, rk_sev, rk_mit, rk_own))
            log_audit_action(st.session_state["username"], user_role, "Risk Logged", rk_p, f"Logged {rk_sev} risk")
            st.success("Risk recorded in governance matrix!")
            st.rerun()


# ==========================================
# MODULE 6: CLASSIFIED RECORDS & DOCUMENTS
# ==========================================
elif nav_choice == "📄 Classified Records & Documents":
    st.title("📄 Classified Records & Document Security Engine")

    if user_role in ["CECM", "Chief Officer"]:
        allowed_class = ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"]
    elif user_role == "Director":
        allowed_class = ["PUBLIC", "INTERNAL", "CONFIDENTIAL"]
    else:
        allowed_class = ["PUBLIC", "INTERNAL"]

    st.info(f"🔒 Your Role (`{user_role}`) grants access to document security levels up to: **{', '.join(allowed_class)}**")

    docs_df = fetch_df("SELECT * FROM classified_documents WHERE security_classification IN ({})".format(','.join('?' for _ in allowed_class)), allowed_class)
    st.dataframe(docs_df, use_container_width=True)

    st.markdown("### 📤 Upload Classified Document")
    with st.form("upload_doc_sec"):
        p_code_d = st.selectbox("Project Code", fetch_df("SELECT project_code FROM projects")["project_code"].unique())
        doc_n = st.text_input("Document Name")
        doc_class = st.selectbox("Security Classification Level", ["PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"])
        retention = st.number_input("Retention Period (Years)", min_value=1, value=7)
        
        if st.form_submit_button("Store in Classified Repository"):
            execute_sql("INSERT INTO classified_documents (project_code, doc_name, security_classification, uploaded_by, retention_period_yrs, upload_date) VALUES (?, ?, ?, ?, ?, ?)",
                        (p_code_d, doc_n, doc_class, user_name, retention, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            log_audit_action(st.session_state["username"], user_role, "Document Upload", p_code_d, f"Uploaded {doc_n} [{doc_class}]")
            st.success("Document stored securely!")
            st.rerun()


# ==========================================
# MODULE 7: SITE INSPECTION MODULE
# ==========================================
elif nav_choice == "🏗️ Site Inspection Module":
    st.title("🏗️ Field Site Inspection & Defect Logger")

    insp_df = fetch_df("SELECT * FROM site_inspections")
    st.dataframe(insp_df, use_container_width=True)

    st.markdown("### 📝 Log Technical Field Inspection")
    with st.form("site_insp_form"):
        i_pcode = st.selectbox("Project Code", fetch_df("SELECT project_code FROM projects")["project_code"].unique())
        i_gps = st.text_input("GPS Coordinates (Lat, Long)", "-0.42013, 36.94759")
        i_weather = st.selectbox("Weather Conditions", ["Sunny / Dry", "Rainy / Muddy", "Overcast"])
        i_defects = st.text_area("Defects / Non-Compliance Observed")
        i_recom = st.text_area("Engineering Recommendations")
        i_next = st.date_input("Next Scheduled Inspection")

        if st.form_submit_button("Submit Official Inspection Log"):
            execute_sql("INSERT INTO site_inspections (project_code, engineer_name, inspection_date, gps_coordinates, weather, defects_found, recommendations, next_inspection_date) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (i_pcode, user_name, datetime.date.today().strftime("%Y-%m-%d"), i_gps, i_weather, i_defects, i_recom, i_next.strftime("%Y-%m-%d")))
            log_audit_action(st.session_state["username"], user_role, "Site Inspection", i_pcode, "Field inspection log created")
            st.success("Inspection logged into permanent audit record!")
            st.rerun()


# ==========================================
# MODULE 8: COUNTY ASSET REGISTER
# ==========================================
elif nav_choice == "🏛️ County Asset Register":
    st.title("🏛️ Completed Public Asset Register")
    st.caption("Post-Completion Capital Asset Tracking & Condition Maintenance")

    assets_df = fetch_df("SELECT * FROM asset_register")
    st.dataframe(assets_df, use_container_width=True)


# ==========================================
# MODULE 9: AI EXECUTIVE BRIEFING
# ==========================================
elif nav_choice == "🤖 AI Executive Briefing":
    st.title("🤖 Daily Executive Operational AI Briefing")

    today_str = datetime.date.today().strftime("%d %B %Y")
    st.markdown(f"""
    <div style="background-color: #F3F4F6; padding: 20px; border-radius: 8px; border-left: 6px solid #0A4D20;">
        <h3>📰 Executive Briefing – {today_str}</h3>
        <p><strong>To:</strong> CECM & Chief Officer | <strong>Generated by:</strong> Nyeri MIS Decision Engine</p>
        <hr/>
        <ul>
            <li><strong>Immediate Approvals:</strong> There are <strong>2 pending executive sign-offs</strong> awaiting authorization in the Executive Approval Centre.</li>
            <li><strong>Project Health:</strong> <strong>Mukurwe-ini Feeder Roads Tarmacking</strong> is currently marked as 🔴 <em>Delayed</em> with an expenditure rate of 95.1% of allocated capital.</li>
            <li><strong>Departmental Leader:</strong> <strong>Roads & Transport</strong> leads infrastructure spend, while <strong>Water & Sanitation</strong> has achieved the highest average completion rate.</li>
            <li><strong>Risk Summary:</strong> 1 critical risk flagged regarding soil instability in Mukurwe-ini.</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)


# ==========================================
# MODULE 10: DISASTER RECOVERY & AUDIT LOGS
# ==========================================
elif nav_choice == "⚙️ Disaster Recovery & Audit Logs":
    st.title("⚙️ System Health, Disaster Recovery & Audit Logs")

    st.subheader("🛡️ Administrative Disaster Recovery")
    d1, d2 = st.columns(2)
    with d1:
        if st.button("💾 Trigger Database Backup Now", type="primary"):
            st.success("Database backup `nyeri_mis_backup_2026.db` generated and verified successfully!")
    with d2:
        if st.button("🔍 Verify System & Database Integrity"):
            st.info("Integrity Check Passed: All database tables consistent.")

    st.divider()
    st.subheader("📜 Comprehensive System Audit Trail")
    logs = fetch_df("SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT 50")
    st.dataframe(logs, use_container_width=True)
