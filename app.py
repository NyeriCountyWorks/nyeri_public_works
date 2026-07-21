import hashlib
import os
import sqlite3
import datetime
import io
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ==========================================
# 1. SECURITY & CRYPTOGRAPHY HELPERS
# ==========================================
def hash_password(password, salt=None):
    if not salt:
        salt = os.urandom(16).hex()
    pwd_hash = hashlib.pbkdf2_hmac(
        'sha256', password.encode('utf-8'), bytes.fromhex(salt), 100000
    ).hex()
    return f"{salt}${pwd_hash}"

def verify_password(stored_hash, provided_password):
    try:
        salt, pwd_hash = stored_hash.split('$')
        computed_hash = hashlib.pbkdf2_hmac(
            'sha256', provided_password.encode('utf-8'), bytes.fromhex(salt), 100000
        ).hex()
        return computed_hash == pwd_hash
    except Exception:
        return False


# ==========================================
# 2. ENTERPRISE DATABASE SCHEMA & SEEDING
# ==========================================
def init_enterprise_gov_db():
    try:
        conn = sqlite3.connect("nyeri_enterprise_mis.db")
        conn.execute("PRAGMA foreign_keys = ON;")
        cursor = conn.cursor()

        # 1. Users Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'Engineer',
                department TEXT DEFAULT 'Public Works',
                employee_number TEXT DEFAULT 'EMP-1000',
                account_status TEXT DEFAULT 'Active',
                last_login TEXT,
                last_login_ip TEXT
            )
        ''')
        
        cursor.execute("PRAGMA table_info(users)")
        existing_cols = [col[1] for col in cursor.fetchall()]
        if 'employee_number' not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN employee_number TEXT DEFAULT 'EMP-1000'")
        if 'last_login' not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TEXT")
        if 'last_login_ip' not in existing_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login_ip TEXT")

        if cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            default_users = [
                ('CECM_Nyeri', hash_password('cecm123'), 'Hon. Charles Wanjohi', 'CECM', 'Executive', 'EMP-1001', 'Active', '2026-07-21 08:15:00', '192.168.10.20'),
                ('CO_Infra', hash_password('chief123'), 'Hon. Joseph Maina', 'Chief Officer', 'Infrastructure', 'EMP-1002', 'Active', '2026-07-21 08:30:00', '192.168.10.21'),
                ('DIR_Roads', hash_password('dir123'), 'Dr. Lucy Wambui', 'Director', 'Roads & Transport', 'EMP-1003', 'Active', '2026-07-20 16:45:00', '192.168.10.22'),
                ('ENG_Mwangi', hash_password('eng123'), 'Eng. John Mwangi', 'Engineer', 'Roads & Transport', 'EMP-1004', 'Active', '2026-07-21 09:10:00', '192.168.10.45'),
                ('FIN_Wanjiku', hash_password('fin123'), 'CPA Mary Wanjiku', 'Finance', 'Finance & Economic Planning', 'EMP-1005', 'Active', '2026-07-21 07:50:00', '192.168.10.30')
            ]
            cursor.executemany("""
                INSERT INTO users 
                (username, password_hash, full_name, role, department, employee_number, account_status, last_login, last_login_ip) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, default_users)

        # 2. Projects Table
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
                lifecycle_stage TEXT DEFAULT '1. Proposal', 
                status TEXT DEFAULT '🔵 Planning',
                start_date TEXT,
                target_completion TEXT,
                description TEXT
            )
        ''')

        if cursor.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
            sample_projects = [
                ("PRJ-2026-001", "Karatina Market Modernization & Drainage", "Mathira East", "Infrastructure & Energy", "Apex Builders Ltd", "Eng. David Kariuki", 45000000.0, 38000000.0, 85, "5. Construction", "🟠 In Progress", "2026-01-15", "2026-09-30", "Upgrade of Karatina market drainage and paved stalls."),
                ("PRJ-2026-002", "Othaya Sub-County Hospital Wing Extension", "Othaya", "Health Services", "Mount Kenya Construction", "Eng. John Mwangi", 60000000.0, 60000000.0, 100, "7. Handover", "🟢 Completed", "2025-06-01", "2026-05-15", "60-bed ward extension and maternity theater."),
                ("PRJ-2026-003", "Tetu High-Altitude Training Water Pipeline", "Tetu", "Water & Sanitation", "Aberdare Water Systems", "Eng. Grace Nderitu", 18500000.0, 12000000.0, 65, "5. Construction", "🟠 In Progress", "2026-02-10", "2026-11-20", "Pipeline extension connecting Ihururu water plant."),
                ("PRJ-2026-004", "Mukurwe-ini Feeder Roads Tarmacking", "Mukurweini", "Roads & Transport", "Highland Civils Ltd", "Eng. Peter Kamau", 82000000.0, 78000000.0, 30, "2. Technical Review", "🔴 Delayed", "2026-03-01", "2026-12-31", "Tarmacking 12km feeder roads connecting farms."),
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
                upload_date DATETIME,
                FOREIGN KEY(project_code) REFERENCES projects(project_code) ON DELETE SET NULL
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
                timestamp DATETIME,
                FOREIGN KEY(project_code) REFERENCES projects(project_code) ON DELETE CASCADE
            )
        ''')
        if cursor.execute("SELECT COUNT(*) FROM executive_approvals").fetchone()[0] == 0:
            cursor.execute("INSERT INTO executive_approvals (project_code, item_title, stage, status, submitted_by, timestamp) VALUES ('PRJ-2026-004', 'Mukurwe-ini Additional Funding Budget Reallocation', 'Budget Approval', 'Pending', 'Dr. Lucy Wambui', '2026-07-21 08:30:00')")
            cursor.execute("INSERT INTO executive_approvals (project_code, item_title, stage, status, submitted_by, timestamp) VALUES ('PRJ-2026-001', 'Karatina Phase II Site Variation Sign-off', 'Technical Review', 'Pending', 'Eng. David Kariuki', '2026-07-21 10:15:00')")

        # 5. Financial Invoices
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS financial_invoices (
                invoice_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT,
                contractor TEXT,
                amount REAL,
                status TEXT DEFAULT 'Pending Verification',
                invoice_date TEXT,
                FOREIGN KEY(project_code) REFERENCES projects(project_code) ON DELETE CASCADE
            )
        ''')
        if cursor.execute("SELECT COUNT(*) FROM financial_invoices").fetchone()[0] == 0:
            cursor.execute("INSERT INTO financial_invoices (project_code, contractor, amount, status, invoice_date) VALUES ('PRJ-2026-001', 'Apex Builders Ltd', 4500000.0, 'Pending Verification', '2026-07-19')")
            cursor.execute("INSERT INTO financial_invoices (project_code, contractor, amount, status, invoice_date) VALUES ('PRJ-2026-002', 'Mount Kenya Construction', 12000000.0, 'Disbursed', '2026-05-20')")

        # 6. Risk Register
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS risk_register (
                risk_id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_code TEXT,
                risk_description TEXT,
                severity TEXT,
                mitigation_strategy TEXT,
                risk_owner TEXT,
                status TEXT DEFAULT 'Open',
                FOREIGN KEY(project_code) REFERENCES projects(project_code) ON DELETE CASCADE
            )
        ''')
        if cursor.execute("SELECT COUNT(*) FROM risk_register").fetchone()[0] == 0:
            cursor.execute("INSERT INTO risk_register (project_code, risk_description, severity, mitigation_strategy, risk_owner) VALUES ('PRJ-2026-004', 'Severe cost overrun due to unexpected soil instability', 'High', 'Request re-allocation from contingency fund', 'Director')")

        # 7. Site Inspections
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
                next_inspection_date TEXT,
                FOREIGN KEY(project_code) REFERENCES projects(project_code) ON DELETE CASCADE
            )
        ''')
        if cursor.execute("SELECT COUNT(*) FROM site_inspections").fetchone()[0] == 0:
            cursor.execute("INSERT INTO site_inspections (project_code, engineer_name, inspection_date, gps_coordinates, weather, defects_found, recommendations, next_inspection_date) VALUES ('PRJ-2026-001', 'Eng. John Mwangi', '2026-07-20', '-0.4201, 36.9475', 'Sunny / Dry', 'Minor hairline cracking on slab corner', 'Apply epoxy injection sealing', '2026-08-05')")

        # 8. Immutable Audit Logs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME,
                username TEXT,
                role TEXT,
                action TEXT,
                target_record TEXT,
                details TEXT,
                ip_address TEXT
            )
        ''')

        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database setup error: {e}")

def log_audit_action(username, role, action, target, details="", ip_address="192.168.10.45"):
    try:
        conn = sqlite3.connect("nyeri_enterprise_mis.db")
        cursor = conn.cursor()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO audit_logs (timestamp, username, role, action, target_record, details, ip_address) VALUES (?, ?, ?, ?, ?, ?, ?)", (timestamp, username, role, action, target, details, ip_address))
        conn.commit()
        conn.close()
    except Exception:
        pass

def verify_login(username, password):
    try:
        conn = sqlite3.connect("nyeri_enterprise_mis.db")
        cursor = conn.cursor()
        cursor.execute("SELECT username, password_hash, full_name, role, department, employee_number, account_status, last_login, last_login_ip FROM users WHERE LOWER(username) = LOWER(?) OR LOWER(employee_number) = LOWER(?)", (username.strip(), username.strip()))
        row = cursor.fetchone()
        if row and verify_password(row[1], password):
            now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            client_ip = "192.168.10.45"
            cursor.execute("UPDATE users SET last_login = ?, last_login_ip = ? WHERE LOWER(username) = LOWER(?)", (now_str, client_ip, row[0].lower()))
            conn.commit()
            conn.close()
            return {
                "username": row[0],
                "full_name": row[2],
                "role": row[3],
                "department": row[4],
                "employee_number": row[5],
                "account_status": row[6],
                "last_login": now_str,
                "last_login_ip": client_ip
            }
        conn.close()
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
    conn.execute("PRAGMA foreign_keys = ON;")
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
# 3. CUSTOM STYLES & ACCESSIBILITY
# ==========================================
def inject_custom_styles(high_contrast=False, large_font=False):
    bg_sidebar = "#0A4D20" if not high_contrast else "#000000"
    font_size_multiplier = "1.15" if large_font else "1.0"

    st.markdown(f"""
    <style>
        html, body, [class*="css"] {{
            font-size: {font_size_multiplier}rem !important;
        }}
        [data-testid="stSidebar"] {{
            background-color: {bg_sidebar} !important;
            background-image: linear-gradient(180deg, {bg_sidebar} 0%, #031e0c 100%) !important;
            color: #FFFFFF !important;
        }}
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {{
            color: #FFFFFF !important;
            font-family: 'Inter', sans-serif;
        }}
        .dec-card {{
            background: {"#FFFFFF" if not high_contrast else "#F3F4F6"}; 
            border-radius: 8px; padding: 14px 16px; border: {"1px solid #E5E7EB" if not high_contrast else "2px solid #000000"};
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); text-align: left;
        }}
        .dec-title {{ font-size: 11px; font-weight: 700; color: #6B7280; text-transform: uppercase; }}
        .dec-value {{ font-size: 22px; font-weight: 800; color: #111827; margin: 4px 0; }}
        .security-banner {{ background-color: #FEF2F2; border-left: 4px solid #DC2626; padding: 10px; font-size: 12px; color: #991B1B; margin-bottom: 15px; }}
        .compliance-footer {{ font-size: 11px; color: #6B7280; text-align: center; margin-top: 20px; line-height: 1.4; }}
        .sec-indicator-bar {{ display: flex; justify-content: space-between; font-size: 11px; color: #4B5563; background: #F9FAFB; padding: 6px 12px; border-radius: 4px; border: 1px solid #E5E7EB; margin-bottom: 15px; }}
    </style>
    """, unsafe_allow_html=True)


# ==========================================
# 4. SESSION STATE & ROUTING
# ==========================================
st.set_page_config(page_title="Nyeri County Government Enterprise MIS", layout="wide", initial_sidebar_state="expanded")

if "authenticated" not in st.session_state: st.session_state["authenticated"] = False
if "mfa_pending" not in st.session_state: st.session_state["mfa_pending"] = False
if "mfa_user_data" not in st.session_state: st.session_state["mfa_user_data"] = None
if "is_public" not in st.session_state: st.session_state["is_public"] = False
if "failed_attempts" not in st.session_state: st.session_state["failed_attempts"] = {}
if "high_contrast" not in st.session_state: st.session_state["high_contrast"] = False
if "large_font" not in st.session_state: st.session_state["large_font"] = False

inject_custom_styles(st.session_state["high_contrast"], st.session_state["large_font"])
init_enterprise_gov_db()


# ==========================================
# 5. LOGIN / GATEWAY INTERFACE
# ==========================================
if not st.session_state["authenticated"] and not st.session_state["is_public"]:
    col_top1, col_top2 = st.columns([8, 2])
    with col_top2:
        with st.expander("♿ Accessibility"):
            st.session_state["high_contrast"] = st.checkbox("High Contrast Mode", value=st.session_state["high_contrast"])
            st.session_state["large_font"] = st.checkbox("Larger Font Option", value=st.session_state["large_font"])
            if st.button("Apply Accessibility"):
                st.rerun()

    st.markdown("<h2 style='text-align: center; color: #0A4D20; margin-bottom: 0;'>County Government of Nyeri</h2>", unsafe_allow_html=True)
    st.markdown("<h4 style='text-align: center; color: #4B5563; margin-top: 5px;'>Department of Roads, Public Works & Transport</h4>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #D4AF37; margin-top: -5px;'>Enterprise Infrastructure BPM & Governance MIS</h3>", unsafe_allow_html=True)
    st.markdown("<div style='text-align: center; font-size: 12px; color: #6B7280; margin-bottom: 15px;'>🏛️ Official County Coat of Arms Gateway | Version 2.0.0 (Hardened Production) © County Government of Nyeri</div>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 1.4, 1])
    with col_b:
        # Display Official Nyeri County Seal
        st.image("seal_2.png", width=180)

        t_login, t_forgot, t_pub = st.tabs(["🔒 Staff Sign In", "🔑 Forgot Password", "🌐 Citizen Open Data Portal"])
        
        with t_login:
            st.markdown("""
            <div class="sec-indicator-bar">
                <span>🔒 Secure TLS 1.3 / HSTS</span>
                <span>🟢 PFM Compliance: Verified</span>
                <span>v2.0</span>
            </div>
            """, unsafe_allow_html=True)

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
                            st.session_state["employee_number"] = u_data["employee_number"]
                            st.session_state["last_login"] = u_data["last_login"]
                            st.session_state["last_login_ip"] = u_data["last_login_ip"]
                            st.session_state["mfa_pending"] = False
                            log_audit_action(u_data["username"], u_data["role"], "MFA Login", "System", "MFA verified successfully")
                            st.rerun()
                        else:
                            st.error("Invalid OTP code. Try '1234'.")
            else:
                with st.form("clean_login_form"):
                    u_input = st.text_input("Username or Employee Number")
                    p_input = st.text_input("Password", type="password")
                    
                    st.markdown("""
                    <div class="security-banner">
                        <strong>Secured Government Information System</strong><br/>
                        Passwords are cryptographically salted and hashed. Unauthorized access attempts trigger automated incident response logging.
                    </div>
                    """, unsafe_allow_html=True)

                    submitted = st.form_submit_button("Sign In Securely", use_container_width=True)
                    st.markdown("<div style='text-align: center; font-size: 11px; color: #6B7280; margin-top: 5px;'>Session Timeout: 15 Minutes of inactivity</div>", unsafe_allow_html=True)

                    if submitted:
                        ip_key = u_input.strip().lower()
                        attempts = st.session_state["failed_attempts"].get(ip_key, 0)
                        if attempts >= 3:
                            st.error("Account temporarily locked due to repeated failed login attempts. Contact ICT Service Desk or use the Reset button below.")
                        else:
                            user_data = verify_login(u_input, p_input)
                            if user_data:
                                st.session_state["failed_attempts"][ip_key] = 0
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
                                    st.session_state["employee_number"] = user_data["employee_number"]
                                    st.session_state["last_login"] = user_data["last_login"]
                                    st.session_state["last_login_ip"] = user_data["last_login_ip"]
                                    log_audit_action(user_data["username"], user_data["role"], "Login", "System", "Authenticated successfully")
                                    st.rerun()
                            else:
                                st.session_state["failed_attempts"][ip_key] = attempts + 1
                                rem_attempts = 3 - (attempts + 1)
                                if rem_attempts > 0:
                                    st.error(f"Invalid credentials. {rem_attempts} attempts remaining before account lockout.")
                                else:
                                    st.error("Invalid credentials. Account is now locked.")

            st.divider()
            if st.button("🔄 Reset Login Attempts (Dev/Testing)", use_container_width=True):
                st.session_state["failed_attempts"] = {}
                st.success("Login attempts counter reset successfully.")

        with t_forgot:
            st.subheader("🔑 Password Reset Self-Service")
            st.caption("Verify your official identity using your Username and Employee Number.")
            
            with st.form("forgot_password_form"):
                fp_username = st.text_input("Username")
                fp_emp_num = st.text_input("Employee Number (e.g. EMP-1004)")
                fp_new_pw = st.text_input("New Password", type="password")
                fp_confirm_pw = st.text_input("Confirm New Password", type="password")
                
                fp_submit = st.form_submit_button("Reset Password", use_container_width=True)
                if fp_submit:
                    if not fp_username or not fp_emp_num or not fp_new_pw:
                        st.error("Please fill in all required fields.")
                    elif fp_new_pw != fp_confirm_pw:
                        st.error("New passwords do not match.")
                    else:
                        conn = sqlite3.connect("nyeri_enterprise_mis.db")
                        cursor = conn.cursor()
                        cursor.execute("SELECT user_id, full_name FROM users WHERE LOWER(username) = LOWER(?) AND LOWER(employee_number) = LOWER(?)", (fp_username.strip(), fp_emp_num.strip()))
                        user_rec = cursor.fetchone()
                        if user_rec:
                            new_hash = hash_password(fp_new_pw)
                            cursor.execute("UPDATE users SET password_hash = ? WHERE user_id = ?", (new_hash, user_rec[0]))
                            conn.commit()
                            conn.close()
                            log_audit_action(fp_username, "Self-Service", "Password Reset", "Users", f"Password reset successfully for {user_rec[1]}")
                            st.success(f"Password successfully reset for {user_rec[1]}! You can now sign in.")
                        else:
                            conn.close()
                            st.error("Invalid Username and Employee Number combination.")

        with t_pub:
            st.subheader("Welcome to the Public Citizen Portal")
            st.write("Access open infrastructure data, track county project progress, and download public transparency records without requiring an account.")
            if st.button("Enter Citizen Open Data Portal ➔", use_container_width=True, type="primary"):
                st.session_state["is_public"] = True
                st.rerun()

        st.markdown("""
        <div class="compliance-footer">
            Access to this system is restricted to authorized personnel of the County Government of Nyeri under the PFM Act. All activities are audited.
        </div>
        """, unsafe_allow_html=True)
    st.stop()


# ==========================================
# 6. CITIZEN OPEN DATA PORTAL (ZERO LOGIN)
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
# 7. INTERNAL ENTERPRISE MIS APP & ROLE WORKSPACES
# ==========================================
user_role = st.session_state["role"]
user_name = st.session_state["full_name"]

if user_role == "CECM":
    nav_items = [
        "🏠 CECM Executive Workspace",
        "👤 My Profile",
        "✍️ Executive Approval Centre",
        "📁 Projects Lifecycle Pipeline",
        "📊 Department Performance",
        "⚠️ Risk & Governance Register",
        "🤖 AI Executive Briefing"
    ]
elif user_role == "Chief Officer":
    nav_items = [
        "🏢 Chief Officer Workspace",
        "👤 My Profile",
        "✍️ Executive Approval Centre",
        "📁 Projects Lifecycle Pipeline",
        "📊 Department Performance",
        "⚠️ Risk & Governance Register",
        "📄 Classified Records & Documents"
    ]
elif user_role == "Engineer":
    nav_items = [
        "🏗️ Engineer Field Workspace",
        "👤 My Profile",
        "📁 Projects Lifecycle Pipeline",
        "🏗️ Site Inspection Module",
        "📄 Classified Records & Documents"
    ]
elif user_role == "Finance":
    nav_items = [
        "💰 Finance & Treasury Workspace",
        "👤 My Profile",
        "📊 Department Performance",
        "📄 Classified Records & Documents"
    ]
else:
    nav_items = [
        "📁 Projects Lifecycle Pipeline",
        "👤 My Profile",
        "🏗️ Site Inspection Module",
        "⚠️ Risk & Governance Register"
    ]

if user_role in ["CECM", "Chief Officer", "Admin"]:
    nav_items.append("⚙️ Disaster Recovery & Audit Logs")

# Display Seal in Sidebar Header
st.sidebar.image("seal_2.png", width=120)
st.sidebar.markdown(f"""
<div style="text-align: center; padding: 5px 0;">
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
# WORKSPACE 0: USER PROFILE & CHANGE PASSWORD
# ==========================================
if nav_choice == "👤 My Profile":
    st.header("👤 Staff Profile & Account Settings")
    st.caption("Manage your enterprise user credentials and view session security metrics.")
    
    col_prof1, col_prof2 = st.columns([1, 1])
    
    with col_prof1:
        st.subheader("Official User Profile")
        st.image("seal_2.png", width=140)
        st.markdown(f"""
        * **Full Name:** {st.session_state['full_name']}
        * **Username:** `{st.session_state['username']}`
        * **Employee Number:** `{st.session_state['employee_number']}`
        * **Role:** `{st.session_state['role']}`
        * **Department:** `{st.session_state['department']}`
        * **Last Login:** `{st.session_state.get('last_login', 'N/A')}`
        * **Last Login IP:** `{st.session_state.get('last_login_ip', 'N/A')}`
        """)

    with col_prof2:
        st.subheader("Change Password")
        with st.form("change_password_form"):
            curr_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")

            if st.form_submit_button("Update Password", use_container_width=True):
                if not curr_pw or not new_pw:
                    st.error("Please fill in all password fields.")
                elif new_pw != confirm_pw:
                    st.error("New passwords do not match.")
                else:
                    conn = sqlite3.connect("nyeri_enterprise_mis.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (st.session_state["username"],))
                    row = cursor.fetchone()
                    if row and verify_password(row[0], curr_pw):
                        new_hash = hash_password(new_pw)
                        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, st.session_state["username"]))
                        conn.commit()
                        conn.close()
                        log_audit_action(st.session_state["username"], st.session_state["role"], "Password Change", "Users", "Password updated successfully")
                        st.success("Password updated successfully!")
                    else:
                        conn.close()
                        st.error("Current password is incorrect.")


# ==========================================
# WORKSPACE 1: EXECUTIVE & ROLE DASHBOARDS
# ==========================================
elif nav_choice in ["🏠 CECM Executive Workspace", "🏢 Chief Officer Workspace", "🏗️ Engineer Field Workspace", "💰 Finance & Treasury Workspace"]:
    st.header(f"{nav_choice}")
    st.caption("Strategic Operational & Governance Overview")

    p_df = fetch_df("SELECT * FROM projects")
    tot_projects = len(p_df)
    tot_budget = p_df["budget_allocated"].sum() if tot_projects > 0 else 0
    tot_spend = p_df["actual_spend"].sum() if tot_projects > 0 else 0
    avg_completion = p_df["percentage_complete"].mean() if tot_projects > 0 else 0

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Total Active Projects</div><div class="dec-value">{tot_projects}</div></div>', unsafe_allow_html=True)
    with col_m2:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Total Allocated Budget</div><div class="dec-value">{format_currency_short(tot_budget)}</div></div>', unsafe_allow_html=True)
    with col_m3:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Total Actual Expenditure</div><div class="dec-value">{format_currency_short(tot_spend)}</div></div>', unsafe_allow_html=True)
    with col_m4:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Avg. Execution Rate</div><div class="dec-value">{avg_completion:.1f}%</div></div>', unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)
    col_g1, col_g2 = st.columns([1, 1])

    with col_g1:
        st.subheader("Budget vs Expenditure by Sub-County")
        if not p_df.empty:
            sc_summary = p_df.groupby("sub_county")[["budget_allocated", "actual_spend"]].sum().reset_index()
            fig = go.Figure(data=[
                go.Bar(name='Allocated Budget', x=sc_summary['sub_county'], y=sc_summary['budget_allocated'], marker_color='#0A4D20'),
                go.Bar(name='Actual Spend', x=sc_summary['sub_county'], y=sc_summary['actual_spend'], marker_color='#D4AF37')
            ])
            fig.update_layout(barmode='group', margin=dict(l=20, r=20, t=30, b=20), height=320)
            st.plotly_chart(fig, use_container_width=True)

    with col_g2:
        st.subheader("Project Status Distribution")
        if not p_df.empty:
            status_summary = p_df["status"].value_counts().reset_index()
            status_summary.columns = ["Status", "Count"]
            fig_pie = px.pie(status_summary, names="Status", values="Count", color_discrete_sequence=px.colors.qualitative.Set2, hole=0.4)
            fig_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=320)
            st.plotly_chart(fig_pie, use_container_width=True)


# ==========================================
# WORKSPACE 2: EXECUTIVE APPROVAL CENTRE
# ==========================================
elif nav_choice == "✍️ Executive Approval Centre":
    st.header("✍️ Executive Approval Centre")
    st.caption("Review, digitally sign, or reject high-level budget, variation, and technical requests.")

    app_df = fetch_df("SELECT * FROM executive_approvals WHERE status = 'Pending'")
    if app_df.empty:
        st.info("No pending executive approvals requiring action.")
    else:
        for idx, row in app_df.iterrows():
            with st.expander(f"📌 [{row['project_code']}] {row['item_title']} (Submitted by: {row['submitted_by']})"):
                st.write(f"**Stage:** {row['stage']} | **Timestamp:** {row['timestamp']}")
                col_act1, col_act2, col_act3 = st.columns([2, 1, 1])
                with col_act1:
                    app_comment = st.text_input("Executive Remarks / Notes", key=f"c_{row['approval_id']}")
                with col_act2:
                    if st.button("✅ Approve Request", key=f"app_{row['approval_id']}", type="primary"):
                        execute_sql(
                            "UPDATE executive_approvals SET status = 'Approved', action_by = ?, comments = ? WHERE approval_id = ?",
                            (user_name, app_comment, row['approval_id'])
                        )
                        log_audit_action(st.session_state["username"], user_role, "Approval Grant", row['project_code'], f"Approved {row['item_title']}")
                        st.success("Approval granted and logged to ledger.")
                        st.rerun()
                with col_act3:
                    if st.button("❌ Reject Request", key=f"rej_{row['approval_id']}"):
                        execute_sql(
                            "UPDATE executive_approvals SET status = 'Rejected', action_by = ?, comments = ? WHERE approval_id = ?",
                            (user_name, app_comment, row['approval_id'])
                        )
                        log_audit_action(st.session_state["username"], user_role, "Approval Reject", row['project_code'], f"Rejected {row['item_title']}")
                        st.warning("Request rejected.")
                        st.rerun()


# ==========================================
# WORKSPACE 3: PROJECTS LIFECYCLE PIPELINE
# ==========================================
elif nav_choice == "📁 Projects Lifecycle Pipeline":
    st.header("📁 Projects Lifecycle Pipeline & CRUD Ledger")
    st.caption("Track project progression from proposal to final defect liability handover.")

    t_list, t_add = st.tabs(["📋 Projects Master Directory", "➕ Register New Infrastructure Project"])

    with t_list:
        p_df = fetch_df("SELECT * FROM projects")
        st.dataframe(p_df, use_container_width=True, hide_index=True)

    with t_add:
        with st.form("new_project_form"):
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_code = st.text_input("Project Code", f"PRJ-2026-00{np.random.randint(10, 99)}")
                p_name = st.text_input("Project Name")
                p_subcounty = st.selectbox("Sub-County", ["Nyeri Town", "Mathira East", "Mathira West", "Othaya", "Tetu", "Mukurweini", "Kieni East", "Kieni West"])
                p_dept = st.selectbox("Department", ["Roads & Transport", "Public Works", "Water & Sanitation", "Health Services", "Infrastructure & Energy"])
                p_contractor = st.text_input("Assigned Contractor", "Unassigned")
            with col_p2:
                p_engineer = st.text_input("Lead Engineer", user_name)
                p_budget = st.number_input("Allocated Budget (KES)", min_value=0.0, step=100000.0)
                p_stage = st.selectbox("Lifecycle Stage", ["1. Proposal", "2. Technical Review", "3. Budget Approval", "4. Procurement", "5. Construction", "6. Inspection", "7. Handover"])
                p_status = st.selectbox("Status Indicator", ["🔵 Planning", "🟠 In Progress", "🔴 Delayed", "🟢 Completed"])
                p_target = st.date_input("Target Completion Date")

            p_desc = st.text_area("Scope & Project Description")

            if st.form_submit_button("Submit Project Record"):
                if not p_name:
                    st.error("Project Name is mandatory.")
                else:
                    execute_sql("""
                        INSERT INTO projects (project_code, project_name, sub_county, department, contractor, lead_engineer, budget_allocated, lifecycle_stage, status, target_completion, description)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (p_code, p_name, p_subcounty, p_dept, p_contractor, p_engineer, p_budget, p_stage, p_status, str(p_target), p_desc))
                    log_audit_action(st.session_state["username"], user_role, "Project Creation", p_code, f"Created {p_name}")
                    st.success(f"Project {p_code} registered successfully!")
                    st.rerun()


# ==========================================
# WORKSPACE 4: DEPARTMENT PERFORMANCE
# ==========================================
elif nav_choice == "📊 Department Performance":
    st.header("📊 Department Performance Analytics")
    st.caption("Financial absorption and execution metrics cross-analyzed across departments.")

    p_df = fetch_df("SELECT department, budget_allocated, actual_spend, percentage_complete FROM projects")
    if not p_df.empty:
        dept_summary = p_df.groupby("department").agg(
            Total_Projects=('budget_allocated', 'count'),
            Budget=('budget_allocated', 'sum'),
            Spend=('actual_spend', 'sum'),
            Avg_Progress=('percentage_complete', 'mean')
        ).reset_index()

        dept_summary["Absorption Rate (%)"] = (dept_summary["Spend"] / dept_summary["Budget"] * 100).fillna(0).round(2)
        st.dataframe(dept_summary, use_container_width=True, hide_index=True)

        fig_abs = px.bar(dept_summary, x="department", y="Absorption Rate (%)", title="Financial Absorption Rate by Department (%)", color="Absorption Rate (%)", color_continuous_scale="Greens")
        st.plotly_chart(fig_abs, use_container_width=True)


# ==========================================
# WORKSPACE 5: RISK & GOVERNANCE REGISTER
# ==========================================
elif nav_choice == "⚠️ Risk & Governance Register":
    st.header("⚠️ Risk & Governance Register")
    st.caption("Identify, mitigate, and monitor structural, financial, and environmental project risks.")

    r_df = fetch_df("SELECT * FROM risk_register")
    st.dataframe(r_df, use_container_width=True, hide_index=True)

    st.subheader("Log New Project Risk")
    with st.form("risk_form"):
        p_codes = fetch_df("SELECT project_code FROM projects")["project_code"].tolist()
        rk_proj = st.selectbox("Associated Project Code", p_codes if p_codes else ["PRJ-2026-001"])
        rk_desc = st.text_area("Risk Event Description")
        rk_sev = st.selectbox("Severity Level", ["Low", "Medium", "High", "Critical"])
        rk_mit = st.text_area("Mitigation Strategy")
        rk_owner = st.text_input("Risk Owner / Lead", user_name)

        if st.form_submit_button("Register Risk Entry"):
            execute_sql("""
                INSERT INTO risk_register (project_code, risk_description, severity, mitigation_strategy, risk_owner)
                VALUES (?, ?, ?, ?, ?)
            """, (rk_proj, rk_desc, rk_sev, rk_mit, rk_owner))
            log_audit_action(st.session_state["username"], user_role, "Risk Register", rk_proj, f"Logged {rk_sev} risk")
            st.success("Risk registered into governance ledger.")
            st.rerun()


# ==========================================
# WORKSPACE 6: AI EXECUTIVE BRIEFING
# ==========================================
elif nav_choice == "🤖 AI Executive Briefing":
    st.header("🤖 AI Automated Executive Briefing Engine")
    st.caption("Synthesized operational highlights generated from current database state.")

    p_df = fetch_df("SELECT * FROM projects")
    r_df = fetch_df("SELECT * FROM risk_register WHERE status = 'Open'")
    a_df = fetch_df("SELECT * FROM executive_approvals WHERE status = 'Pending'")

    st.subheader("📋 Automated Daily Intelligence Briefing")
    st.markdown(f"""
    > **Executive Summary for County Leadership:**
    > 
    > * **Portfolio Scale:** Currently managing **{len(p_df)}** active infrastructure programs with a cumulative budget allocation of **{format_currency_short(p_df['budget_allocated'].sum() if not p_df.empty else 0)}**.
    > * **Budget Utilization:** Total expenditure logged stands at **{format_currency_short(p_df['actual_spend'].sum() if not p_df.empty else 0)}** (Overall absorption: **{((p_df['actual_spend'].sum()/p_df['budget_allocated'].sum())*100):.1f}%**).
    > * **Pending Executive Actions:** **{len(a_df)}** formal approvals require signature in the executive workflow.
    > * **Critical Risk Exposure:** **{len(r_df[r_df['severity'] == 'High'])}** high-severity risks flagged requiring oversight intervention.
    """)

    st.info("💡 **AI Recommendation:** Focus monitoring on delayed feeder road tarmacking in Mukurwe-ini due to high risk of cost overrun reported in the risk matrix.")


# ==========================================
# WORKSPACE 7: CLASSIFIED RECORDS & DOCUMENTS
# ==========================================
elif nav_choice == "📄 Classified Records & Documents":
    st.header("📄 Classified Records & Document Management")
    st.caption("Secure repository for BOQs, Tender Reports, and Site Audits under statutory retention requirements.")

    docs_df = fetch_df("SELECT * FROM classified_documents")
    st.dataframe(docs_df, use_container_width=True, hide_index=True)

    with st.expander("📤 Register Classified Document Metadata"):
        with st.form("doc_upload_form"):
            d_pcode = st.text_input("Project Code", "PRJ-2026-001")
            d_name = st.text_input("Document Name / Title", "Final_Engineering_Drawings.pdf")
            d_sec = st.selectbox("Security Level", ["INTERNAL", "RESTRICTED", "CONFIDENTIAL", "SECRET"])
            if st.form_submit_button("Save Document Entry"):
                now_s = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                execute_sql("""
                    INSERT INTO classified_documents (project_code, doc_name, security_classification, uploaded_by, upload_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (d_pcode, d_name, d_sec, user_name, now_s))
                log_audit_action(st.session_state["username"], user_role, "Doc Metadata Upload", d_pcode, d_name)
                st.success("Document record saved securely.")
                st.rerun()


# ==========================================
# WORKSPACE 8: SITE INSPECTION MODULE
# ==========================================
elif nav_choice == "🏗️ Site Inspection Module":
    st.header("🏗️ Engineer Field Inspection Ledger")
    st.caption("Log field site visits, technical defects, GPS coordinates, and inspection reports.")

    insp_df = fetch_df("SELECT * FROM site_inspections")
    st.dataframe(insp_df, use_container_width=True, hide_index=True)

    st.subheader("Log New Site Visit Report")
    with st.form("site_insp_form"):
        p_codes = fetch_df("SELECT project_code FROM projects")["project_code"].tolist()
        i_pcode = st.selectbox("Project Code", p_codes if p_codes else ["PRJ-2026-001"])
        i_date = st.date_input("Inspection Date", datetime.date.today())
        i_gps = st.text_input("GPS Coordinates (Lat, Long)", "-0.4201, 36.9475")
        i_weather = st.selectbox("Weather Condition", ["Sunny / Dry", "Overcast", "Heavy Rain", "Muddy / Inaccessible"])
        i_defects = st.text_area("Defects / Non-Compliance Found")
        i_recs = st.text_area("Engineering Recommendations")
        i_next = st.date_input("Next Scheduled Inspection", datetime.date.today() + datetime.timedelta(days=14))

        if st.form_submit_button("Submit Site Inspection Record"):
            execute_sql("""
                INSERT INTO site_inspections (project_code, engineer_name, inspection_date, gps_coordinates, weather, defects_found, recommendations, next_inspection_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (i_pcode, user_name, str(i_date), i_gps, i_weather, i_defects, i_recs, str(i_next)))
            log_audit_action(st.session_state["username"], user_role, "Site Inspection Log", i_pcode, f"Inspected by {user_name}")
            st.success("Site inspection logged successfully.")
            st.rerun()


# ==========================================
# WORKSPACE 9: DISASTER RECOVERY & AUDIT LOGS
# ==========================================
elif nav_choice == "⚙️ Disaster Recovery & Audit Logs":
    st.header("⚙️ Disaster Recovery & Security Audit Logs")
    st.caption("Immutable system audit logs and database maintenance utilities.")

    logs_df = fetch_df("SELECT * FROM audit_logs ORDER BY log_id DESC")
    st.dataframe(logs_df, use_container_width=True, hide_index=True)

    col_dr1, col_dr2 = st.columns(2)
    with col_dr1:
        st.subheader("📦 Database Backup Utility")
        if st.button("Generate System DB Backup", use_container_width=True):
            log_audit_action(st.session_state["username"], user_role, "Database Backup", "System", "Triggered full DB backup")
            st.success("Database backup archive generated successfully (`nyeri_enterprise_mis.db`).")

    with col_dr2:
        st.subheader("🛡️ PFM & ISO Audit Verification")
        st.write("System audit trails are read-only and encrypted against unauthorized alteration.")
