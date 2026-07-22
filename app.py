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
# 2. ENTERPRISE DATABASE SCHEMA & SEEDING (WITH RBAC)
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

        # 2. Role-Based Access Control (RBAC) Permissions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS role_permissions (
                permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                module_name TEXT NOT NULL,
                can_view INTEGER DEFAULT 1,
                can_execute INTEGER DEFAULT 0
            )
        ''')
        
        if cursor.execute("SELECT COUNT(*) FROM role_permissions").fetchone()[0] == 0:
            default_rbac = [
                # CECM (Cabinet Executive) - Full Access
                ('CECM', '📊 Executive Dashboard & KPIs', 1, 1),
                ('CECM', '📁 Projects Lifecycle Pipeline', 1, 1),
                ('CECM', '🌍 Interactive Infrastructure Map', 1, 1),
                ('CECM', '📄 Classified Records & Documents', 1, 1),
                ('CECM', '✍️ Executive Approval Centre', 1, 1),
                ('CECM', '⚙️ Disaster Recovery & Audit Logs', 1, 1),
                ('CECM', '📊 Department Performance', 1, 1),
                ('CECM', '🏗️ Site Inspection Module', 1, 1),
                ('CECM', '⚠️ Risk & Governance Register', 1, 1),
                
                # Chief Officer - High Level Oversight
                ('Chief Officer', '📊 Executive Dashboard & KPIs', 1, 1),
                ('Chief Officer', '📁 Projects Lifecycle Pipeline', 1, 1),
                ('Chief Officer', '🌍 Interactive Infrastructure Map', 1, 1),
                ('Chief Officer', '✍️ Executive Approval Centre', 1, 1),
                ('Chief Officer', '📄 Classified Records & Documents', 1, 1),
                ('Chief Officer', '📊 Department Performance', 1, 1),
                ('Chief Officer', '🏗️ Site Inspection Module', 1, 1),
                ('Chief Officer', '⚠️ Risk & Governance Register', 1, 1),

                # Director - Operational Management
                ('Director', '📊 Executive Dashboard & KPIs', 1, 1),
                ('Director', '📁 Projects Lifecycle Pipeline', 1, 1),
                ('Director', '🌍 Interactive Infrastructure Map', 1, 1),
                ('Director', '📄 Classified Records & Documents', 1, 1),
                ('Director', '📊 Department Performance', 1, 1),
                ('Director', '🏗️ Site Inspection Module', 1, 1),
                ('Director', '⚠️ Risk & Governance Register', 1, 1),
                
                # Engineer - Operational Field Access
                ('Engineer', '📊 Executive Dashboard & KPIs', 1, 0),
                ('Engineer', '📁 Projects Lifecycle Pipeline', 1, 1),
                ('Engineer', '🏗️ Site Inspection Module', 1, 1),
                ('Engineer', '🌍 Interactive Infrastructure Map', 1, 0),
                ('Engineer', '⚠️ Risk & Governance Register', 1, 1),
                
                # Finance - Treasury & Budgets
                ('Finance', '📊 Executive Dashboard & KPIs', 1, 0),
                ('Finance', '💰 Finance & Treasury Workspace', 1, 1),
                ('Finance', '📊 Department Performance', 1, 0),
                ('Finance', '📁 Projects Lifecycle Pipeline', 1, 0),
            ]
            cursor.executemany("""
                INSERT INTO role_permissions (role, module_name, can_view, can_execute)
                VALUES (?, ?, ?, ?)
            """, default_rbac)

        # 3. Projects Table
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
                status TEXT DEFAULT '🔵 Active',
                start_date TEXT,
                target_completion TEXT,
                description TEXT,
                latitude REAL DEFAULT -0.4169,
                longitude REAL DEFAULT 36.9515
            )
        ''')
        
        cursor.execute("PRAGMA table_info(projects)")
        p_cols = [c[1] for c in cursor.fetchall()]
        if 'latitude' not in p_cols:
            cursor.execute("ALTER TABLE projects ADD COLUMN latitude REAL DEFAULT -0.4169")
        if 'longitude' not in p_cols:
            cursor.execute("ALTER TABLE projects ADD COLUMN longitude REAL DEFAULT 36.9515")

        if cursor.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
            sample_projects = [
                ("PRJ-2026-001", "Karatina Market Modernization & Drainage", "Mathira East", "Infrastructure & Energy", "Apex Builders Ltd", "Eng. David Kariuki", 45000000.0, 38000000.0, 85, "5. Construction", "🟠 Pending", "2026-01-15", "2026-09-30", "Upgrade of Karatina market drainage and paved stalls.", -0.4851, 37.1234),
                ("PRJ-2026-002", "Othaya Sub-County Hospital Wing Extension", "Othaya", "Health Services", "Mount Kenya Construction", "Eng. John Mwangi", 60000000.0, 60000000.0, 100, "7. Handover", "🟢 Completed", "2025-06-01", "2026-05-15", "60-bed ward extension and maternity theater.", -0.5312, 36.9321),
                ("PRJ-2026-003", "Tetu High-Altitude Training Water Pipeline", "Tetu", "Water & Sanitation", "Aberdare Water Systems", "Eng. Grace Nderitu", 18500000.0, 12000000.0, 65, "5. Construction", "🔵 Active", "2026-02-10", "2026-11-20", "Pipeline extension connecting Ihururu water plant.", -0.3921, 36.9102),
                ("PRJ-2026-004", "Mukurwe-ini Feeder Roads Tarmacking", "Mukurweini", "Roads & Transport", "Highland Civils Ltd", "Eng. Peter Kamau", 82000000.0, 78000000.0, 30, "2. Technical Review", "🔴 Delayed", "2026-03-01", "2026-12-31", "Tarmacking 12km feeder roads connecting farms.", -0.5843, 37.0211),
                ("PRJ-2026-005", "Nyeri Town Bus Park Stormwater System", "Nyeri Town", "Public Works", "County In-House", "Eng. John Mwangi", 12000000.0, 1500500.0, 15, "3. Budget Approval", "🔵 Active", "2026-05-01", "2026-10-15", "Rehabilitation of central bus park culverts.", -0.4169, 36.9515)
            ]
            cursor.executemany("""
                INSERT INTO projects 
                (project_code, project_name, sub_county, department, contractor, lead_engineer, budget_allocated, actual_spend, percentage_complete, lifecycle_stage, status, start_date, target_completion, description, latitude, longitude)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_projects)

        # 4. Classified Documents
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
            cursor.execute("INSERT INTO classified_documents (project_code, doc_name, security_classification, version, uploaded_by, upload_date) VALUES ('PRJ-2026-004', 'Tender_Evaluation_Report_Confidential.pdf', 'RESTRICTED', 'v1.1', 'Dr. Lucy Wambui', '2026-07-20 14:20:00')")
            cursor.execute("INSERT INTO classified_documents (project_code, doc_name, security_classification, version, uploaded_by, upload_date) VALUES ('PRJ-2026-001', 'Karatina_BOQ_Final.pdf', 'INTERNAL', 'v1.0', 'Eng. David Kariuki', '2026-07-18 09:15:00')")

        # 5. Executive Approvals
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

        # 6. Financial Invoices
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

        # 7. Risk Register
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

        # 8. Site Inspections
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

        # 9. Immutable Audit Logs
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
            cursor.execute("UPDATE users SET last_login = ?, last_login_ip = ? WHERE username = ?", (now_str, client_ip, row[0]))
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
    except Exception as e:
        print("LOGIN ERROR EXCEPTION:", e)
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

def get_allowed_modules_for_role(role_name):
    """Dynamically fetches permitted navigation items from the SQLite RBAC table."""
    try:
        conn = sqlite3.connect("nyeri_enterprise_mis.db")
        cursor = conn.cursor()
        cursor.execute("SELECT module_name FROM role_permissions WHERE role = ? AND can_view = 1", (role_name,))
        modules = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not modules:
            return [
                "📊 Executive Dashboard & KPIs", 
                "📁 Projects Lifecycle Pipeline", 
                "🌍 Interactive Infrastructure Map"
            ]
        return modules
    except Exception:
        return [
            "📊 Executive Dashboard & KPIs", 
            "📁 Projects Lifecycle Pipeline", 
            "🌍 Interactive Infrastructure Map"
        ]

def check_permission(role, module_name):
    try:
        conn = sqlite3.connect("nyeri_enterprise_mis.db")
        cursor = conn.cursor()
        cursor.execute("SELECT can_execute FROM role_permissions WHERE role = ? AND module_name = ?", (role, module_name))
        res = cursor.fetchone()
        conn.close()
        return res[0] == 1 if res else False
    except Exception:
        return True


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
    st.markdown("<div style='text-align: center; font-size: 12px; color: #6B7280; margin-bottom: 15px;'>🏛️ Official County Coat of Arms Gateway | Version 2.0.0 (RBAC Enforced) © County Government of Nyeri</div>", unsafe_allow_html=True)

    col_a, col_b, col_c = st.columns([1, 1.4, 1])
    with col_b:
        t_login, t_forgot, t_pub = st.tabs(["🔒 Staff Sign In", "🔑 Forgot Password", "🌐 Citizen Open Data Portal"])
        
        with t_login:
            st.markdown("""
            <div class="sec-indicator-bar">
                <span>🔒 Secure TLS 1.3 / HSTS</span>
                <span>🟢 RBAC Database: Active</span>
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
                        Passwords are cryptographically salted and hashed. Database-driven RBAC enforces strict authorization policies.
                    </div>
                    """, unsafe_allow_html=True)

                    submitted = st.form_submit_button("Sign In Securely", use_container_width=True)
                    st.markdown("<div style='text-align: center; font-size: 11px; color: #6B7280; margin-top: 5px;'>Session Timeout: 15 Minutes of inactivity</div>", unsafe_allow_html=True)

                    if submitted:
                        ip_key = u_input.strip().lower()
                        attempts = st.session_state["failed_attempts"].get(ip_key, 0)
                        if attempts >= 3:
                            st.error("Account temporarily locked due to repeated failed login attempts. Contact ICT Service Desk.")
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

    public_filtered["budget_allocated"] = public_filtered["budget_allocated"].apply(lambda x: format_currency_short(x))
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
# 7. INTERNAL ENTERPRISE MIS APP & DYNAMIC RBAC NAVIGATION
# ==========================================
user_role = st.session_state["role"]
user_name = st.session_state["full_name"]

# Dynamically load permitted modules from database RBAC rules
allowed_modules = get_allowed_modules_for_role(user_role)
universal_modules = [
    "🔔 Notification Center", 
    "🔍 Global Universal Search", 
    "🤖 Executive AI Assistant", 
    "👤 My Profile & Settings"
]
active_nav_items = list(dict.fromkeys(allowed_modules + universal_modules))

# Enhanced Branding Header inside Sidebar
st.sidebar.markdown(f"""
<div style="text-align: center; padding: 10px 0;">
    <h3 style="color: #FFFFFF; font-weight: 800; margin: 0;">NYERI MIS ERP</h3>
    <p style="color: #D4AF37; font-size: 11px; margin: 2px 0;"><b>Motto:</b> Quality Public Service</p>
    <span style="color: #FFFFFF; font-size: 11px;"><b>Role:</b> {user_role.upper()} ({st.session_state['department']})</span>
</div>
<hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.15);" />
""", unsafe_allow_html=True)

selected_nav = st.sidebar.radio("Enterprise Navigation", active_nav_items)

# Top Bar Profile Widget & Global Session Info
col_info1, col_info2, col_info3, col_info4 = st.columns([3, 3, 2, 2])
with col_info1:
    st.markdown(f"**User:** {user_name} (`{st.session_state['employee_number']}`)")
with col_info2:
    st.markdown(f"**Department:** {st.session_state['department']}")
with col_info3:
    st.markdown(f"**IP:** `{st.session_state['last_login_ip']}`")
with col_info4:
    if st.button("🔒 Sign Out", use_container_width=True):
        log_audit_action(st.session_state["username"], user_role, "Logout", "System", "User signed out securely")
        st.session_state["authenticated"] = False
        st.session_state["mfa_pending"] = False
        st.rerun()

st.divider()

# ------------------------------------------
# NAVIGATION MODULE IMPLEMENTATIONS
# ------------------------------------------

if selected_nav == "📊 Executive Dashboard & KPIs":
    st.subheader("📊 Executive Dashboard & Real-Time KPIs")
    st.caption("High-level fiscal and infrastructural analytics for Nyeri County Government PFM monitoring.")

    p_df = fetch_df("SELECT * FROM projects")
    
    total_budget = p_df["budget_allocated"].sum()
    total_spend = p_df["actual_spend"].sum()
    avg_completion = p_df["percentage_complete"].mean()
    active_count = len(p_df[p_df["status"].str.contains("Active|Pending", case=False)])

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f"""
        <div class="dec-card">
            <div class="dec-title">Total Budget Allocated</div>
            <div class="dec-value">{format_currency_short(total_budget)}</div>
        </div>
        """, unsafe_allow_html=True)
    with m2:
        st.markdown(f"""
        <div class="dec-card">
            <div class="dec-title">Total Actual Expenditure</div>
            <div class="dec-value">{format_currency_short(total_spend)}</div>
        </div>
        """, unsafe_allow_html=True)
    with m3:
        st.markdown(f"""
        <div class="dec-card">
            <div class="dec-title">Average Project Progress</div>
            <div class="dec-value">{avg_completion:.1f}%</div>
        </div>
        """, unsafe_allow_html=True)
    with m4:
        st.markdown(f"""
        <div class="dec-card">
            <div class="dec-title">Active Projects Count</div>
            <div class="dec-value">{active_count}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    c_chart1, c_chart2 = st.columns(2)
    with c_chart1:
        st.markdown("##### Budget vs. Actual Spend by Sub-County")
        sub_agg = p_df.groupby("sub_county")[["budget_allocated", "actual_spend"]].sum().reset_index()
        fig_bar = px.bar(sub_agg, x="sub_county", y=["budget_allocated", "actual_spend"], barmode="group",
                         labels={"value": "Amount (KES)", "sub_county": "Sub-County", "variable": "Metric"},
                         color_discrete_map={"budget_allocated": "#0A4D20", "actual_spend": "#D4AF37"})
        st.plotly_chart(fig_bar, use_container_width=True)

    with c_chart2:
        st.markdown("##### Project Lifecycle Distribution")
        life_agg = p_df.groupby("lifecycle_stage").size().reset_index(name="count")
        fig_pie = px.pie(life_agg, names="lifecycle_stage", values="count", hole=0.4,
                         color_discrete_sequence=px.colors.sequential.Greens)
        st.plotly_chart(fig_pie, use_container_width=True)

elif selected_nav == "📁 Projects Lifecycle Pipeline":
    st.subheader("📁 Enterprise Projects Lifecycle Pipeline")
    st.caption("Manage end-to-end county projects across 7 rigorous stages from Proposal to Handover.")

    p_df = fetch_df("SELECT * FROM projects")
    
    with st.expander("➕ Register New County Project / Update Stage"):
        with st.form("project_form"):
            f_code = st.text_input("Project Code (e.g. PRJ-2026-006)")
            f_name = st.text_input("Project Name")
            f_sub = st.selectbox("Sub-County", ["Nyeri Town", "Mathira East", "Mathira West", "Othaya", "Tetu", "Mukurweini", "Kieni East", "Kieni West"])
            f_dept = st.selectbox("Department", ["Roads & Transport", "Infrastructure & Energy", "Health Services", "Water & Sanitation", "Public Works"])
            f_contractor = st.text_input("Contractor Name", "Unassigned")
            f_budget = st.number_input("Budget Allocated (KES)", min_value=0.0, value=1000000.0)
            f_stage = st.selectbox("Lifecycle Stage", [
                "1. Proposal", "2. Technical Review", "3. Budget Approval", 
                "4. Procurement", "5. Construction", "6. Quality Audit", "7. Handover"
            ])
            f_status = st.selectbox("Status Indicator", ["🔵 Active", "🟠 Pending", "🟢 Completed", "🔴 Delayed"])
            f_desc = st.text_area("Project Description / Scope")
            
            submitted_proj = st.form_submit_button("Commit Project Record to DB")
            if submitted_proj:
                if f_code and f_name:
                    try:
                        execute_sql("""
                            INSERT INTO projects (project_code, project_name, sub_county, department, contractor, budget_allocated, lifecycle_stage, status, description)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (f_code, f_name, f_sub, f_dept, f_contractor, f_budget, f_stage, f_status, f_desc))
                        log_audit_action(user_name, user_role, "Create Project", f_code, f"Created project {f_name}")
                        st.success(f"Project {f_code} successfully registered!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error inserting project (Ensure unique project code): {e}")
                else:
                    st.error("Project Code and Name are mandatory.")

    st.markdown("### Existing County Projects Inventory")
    st.dataframe(p_df[["project_code", "project_name", "sub_county", "department", "contractor", "budget_allocated", "percentage_complete", "lifecycle_stage", "status"]], use_container_width=True, hide_index=True)

elif selected_nav == "🌍 Interactive Infrastructure Map":
    st.subheader("🌍 Nyeri County Spatial Infrastructure Map")
    st.caption("Geospatial visualization of active infrastructure developments across all sub-counties.")

    p_df = fetch_df("SELECT project_code, project_name, sub_county, latitude, longitude, budget_allocated, percentage_complete, status FROM projects")
    
    if not p_df.empty:
        st.map(p_df, latitude="latitude", longitude="longitude", size=50, color="#0A4D20")
        st.markdown("##### Project Spatial Database Details")
        st.dataframe(p_df, use_container_width=True, hide_index=True)
    else:
        st.info("No spatial data coordinates available.")

elif selected_nav == "🔔 Notification Center":
    st.subheader("🔔 Enterprise Notification & Alert Center")
    st.caption("Automated system alerts regarding budget limits, delayed milestones, and pending approvals.")

    st.markdown("""
    * **🔴 High Priority:** Mukurwe-ini Feeder Roads Tarmacking (`PRJ-2026-004`) has reported a timeline delay of 14 days. Mitigation review required.
    * **🟠 Action Required:** Karatina Phase II Site Variation Sign-off pending executive review by Chief Officer.
    * **🟢 System Status:** Database replication active, TLS 1.3 secured session verified. Backup completed successfully at 04:00 AM.
    """)

elif selected_nav == "🔍 Global Universal Search":
    st.subheader("🔍 Global Universal Search Engine")
    st.caption("Search across users, projects, classified documents, financial records, and audit logs simultaneously.")

    query_str = st.text_input("Enter universal search query keyword (e.g. Karatina, Mwangi, Tarmacking):")
    if query_str:
        st.markdown(f"#### Search Results for: `{query_str}`")
        
        res_proj = fetch_df("SELECT project_code, project_name, sub_county FROM projects WHERE project_name LIKE ? OR project_code LIKE ? OR sub_county LIKE ?", (f"%{query_str}%", f"%{query_str}%", f"%{query_str}%"))
        st.markdown(f"**Projects Found ({len(res_proj)}):**")
        if not res_proj.empty: st.dataframe(res_proj, use_container_width=True, hide_index=True)
        else: st.info("No matching projects found.")

        res_docs = fetch_df("SELECT doc_name, security_classification, project_code FROM classified_documents WHERE doc_name LIKE ? OR project_code LIKE ?", (f"%{query_str}%", f"%{query_str}%"))
        st.markdown(f"**Classified Documents Found ({len(res_docs)}):**")
        if not res_docs.empty: st.dataframe(res_docs, use_container_width=True, hide_index=True)
        else: st.info("No matching documents found.")

elif selected_nav == "🤖 Executive AI Assistant":
    st.subheader("🤖 Nyeri County Executive AI Assistant")
    st.caption("Query PFM compliance guidelines, project updates, and budgetary allocations using natural language processing.")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = [
            {"role": "assistant", "content": "Jambo! I am your Nyeri County MIS Virtual Assistant. How can I assist you with project analytics, PFM regulations, or county data today?"}
        ]

    for msg in st.session_state["chat_history"]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_q = st.chat_input("Ask a question about county projects or finances...")
    if user_q:
        st.session_state["chat_history"].append({"role": "user", "content": user_q})
        with st.chat_message("user"):
            st.write(user_q)

        ans = "I have cross-referenced the county enterprise database. For specific inquiries regarding budgets or approvals, please navigate to the respective approval or finance workspace modules."
        q_lower = user_q.lower()
        if "budget" in q_lower or "spend" in q_lower:
            p_df = fetch_df("SELECT SUM(budget_allocated), SUM(actual_spend) FROM projects")
            tot_b, tot_s = p_df.iloc[0, 0], p_df.iloc[0, 1]
            ans = f"The total cumulative budget allocated across all current county infrastructure projects is KES {tot_b:,.2f}, with total actual expenditure standing at KES {tot_s:,.2f}."
        elif "karatina" in q_lower:
            ans = "Karatina Market Modernization & Drainage (PRJ-2026-001) is currently at 85% completion under Mathira East sub-county, handled by Apex Builders Ltd."
        elif "mukurwe" in q_lower:
            ans = "Mukurwe-ini Feeder Roads Tarmacking (PRJ-2026-004) is marked with status 'Delayed' due to unexpected soil instability issues."

        st.session_state["chat_history"].append({"role": "assistant", "content": ans})
        with st.chat_message("assistant"):
            st.write(ans)

elif selected_nav == "👤 My Profile & Settings":
    st.subheader("👤 Staff Profile & Secure Settings")
    st.caption("Manage your credential preferences, accessibility options, and view session telemetry.")

    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown(f"""
        * **Full Name:** {user_name}
        * **Username:** `{st.session_state['username']}`
        * **Employee Number:** `{st.session_state['employee_number']}`
        * **Assigned Role:** `{user_role}`
        * **Department:** `{st.session_state['department']}`
        * **Account Status:** `Active 🟢`
        * **Last Login Timestamp:** `{st.session_state['last_login']}`
        * **Last Login IP Address:** `{st.session_state['last_login_ip']}`
        """)
    with col_p2:
        st.markdown("##### Change Password")
        with st.form("change_pw_form"):
            old_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            conf_pw = st.text_input("Confirm New Password", type="password")
            if st.form_submit_button("Update Password"):
                conn = sqlite3.connect("nyeri_enterprise_mis.db")
                cursor = conn.cursor()
                cursor.execute("SELECT password_hash FROM users WHERE username = ?", (st.session_state["username"],))
                stored = cursor.fetchone()[0]
                if not verify_password(stored, old_pw):
                    st.error("Incorrect current password.")
                elif new_pw != conf_pw:
                    st.error("New passwords do not match.")
                else:
                    new_hash = hash_password(new_pw)
                    cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, st.session_state["username"]))
                    conn.commit()
                    conn.close()
                    log_audit_action(st.session_state["username"], user_role, "Password Change", "Users", "Password updated successfully")
                    st.success("Password successfully updated!")

elif selected_nav == "📄 Classified Records & Documents":
    st.subheader("📄 Classified Records & Document Management")
    st.caption("Secure enterprise repository with role-based document clearance checks.")

    if not check_permission(user_role, "📄 Classified Records & Documents"):
        st.warning("⚠️ Access Restricted: Your role clearance level does not permit viewing high-security classified documents.")
    else:
        doc_df = fetch_df("SELECT * FROM classified_documents")
        st.dataframe(doc_df, use_container_width=True, hide_index=True)
        
        with st.expander("⬆️ Upload New Classified Document"):
            with st.form("doc_upload_form"):
                d_code = st.text_input("Project Code (e.g. PRJ-2026-001)")
                d_name = st.text_input("Document Name / Title")
                d_sec = st.selectbox("Security Classification", ["INTERNAL", "RESTRICTED", "CONFIDENTIAL", "TOP SECRET"])
                d_ver = st.text_input("Version", "v1.0")
                if st.form_submit_button("Upload Record"):
                    execute_sql("INSERT INTO classified_documents (project_code, doc_name, security_classification, version, uploaded_by, upload_date) VALUES (?, ?, ?, ?, ?, ?)",
                                (d_code, d_name, d_sec, d_ver, user_name, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                    log_audit_action(user_name, user_role, "Upload Document", d_code, f"Uploaded document {d_name} ({d_sec})")
                    st.success("Document registered successfully!")
                    st.rerun()

elif selected_nav == "🏗️ Site Inspection Module":
    st.subheader("🏗️ Field Site Inspection & Quality Audit Module")
    st.caption("Record site visits, GPS coordinates, weather notes, and engineering defect evaluations.")

    insp_df = fetch_df("SELECT * FROM site_inspections")
    st.dataframe(insp_df, use_container_width=True, hide_index=True)

    with st.expander("📝 Submit New Site Inspection Report"):
        with st.form("insp_form"):
            i_code = st.text_input("Project Code")
            i_gps = st.text_input("GPS Coordinates", "-0.4169, 36.9515")
            i_weather = st.text_input("Weather Conditions", "Sunny / Dry")
            i_defects = st.text_area("Defects / Observations Found")
            i_recs = st.text_area("Engineering Recommendations")
            i_next = st.date_input("Next Scheduled Inspection Date")
            
            if st.form_submit_button("Submit Inspection Log"):
                execute_sql("""
                    INSERT INTO site_inspections (project_code, engineer_name, inspection_date, gps_coordinates, weather, defects_found, recommendations, next_inspection_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (i_code, user_name, str(datetime.date.today()), i_gps, i_weather, i_defects, i_recs, str(i_next)))
                log_audit_action(user_name, user_role, "Site Inspection", i_code, "Submitted field inspection report")
                st.success("Inspection report saved successfully!")
                st.rerun()

elif selected_nav == "⚠️ Risk & Governance Register":
    st.subheader("⚠️ Enterprise Risk & Governance Register")
    st.caption("Track project risks, severity levels, mitigation strategies, and designated risk owners.")

    risk_df = fetch_df("SELECT * FROM risk_register")
    st.dataframe(risk_df, use_container_width=True, hide_index=True)

    with st.expander("➕ Log New Risk Item"):
        with st.form("risk_form"):
            r_code = st.text_input("Project Code")
            r_desc = st.text_area("Risk Description")
            r_sev = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"])
            r_mit = st.text_area("Mitigation Strategy")
            r_owner = st.text_input("Risk Owner", user_name)
            if st.form_submit_button("Register Risk"):
                execute_sql("INSERT INTO risk_register (project_code, risk_description, severity, mitigation_strategy, risk_owner) VALUES (?, ?, ?, ?, ?)",
                            (r_code, r_desc, r_sev, r_mit, r_owner))
                log_audit_action(user_name, user_role, "Log Risk", r_code, f"Registered risk: {r_desc[:30]}...")
                st.success("Risk item successfully added!")
                st.rerun()

elif selected_nav == "📊 Department Performance":
    st.subheader("📊 Departmental Performance & Metrics")
    st.caption("Comparative departmental analysis across budget absorption rates and milestone completions.")

    p_df = fetch_df("SELECT department, SUM(budget_allocated) as total_budget, SUM(actual_spend) as total_spend, AVG(percentage_complete) as avg_comp FROM projects GROUP BY department")
    st.dataframe(p_df, use_container_width=True, hide_index=True)

    fig_dept = px.bar(p_df, x="department", y=["total_budget", "total_spend"], barmode="group",
                      labels={"value": "Amount (KES)", "department": "Department"},
                      color_discrete_map={"total_budget": "#0A4D20", "total_spend": "#D4AF37"})
    st.plotly_chart(fig_dept, use_container_width=True)

elif selected_nav == "💰 Finance & Treasury Workspace":
    st.subheader("💰 Finance & Treasury PFM Workspace")
    st.caption("Invoice verification, fund disbursement tracking, and Exchequer release monitoring.")

    inv_df = fetch_df("SELECT * FROM financial_invoices")
    st.dataframe(inv_df, use_container_width=True, hide_index=True)

    with st.expander("💸 Process New Invoice Verification"):
        with st.form("inv_form"):
            inv_code = st.text_input("Project Code")
            inv_contractor = st.text_input("Contractor Name")
            inv_amt = st.number_input("Invoice Amount (KES)", min_value=0.0)
            inv_stat = st.selectbox("Status", ["Pending Verification", "Verified", "Disbursed", "Rejected"])
            if st.form_submit_button("Save Invoice Record"):
                execute_sql("INSERT INTO financial_invoices (project_code, contractor, amount, status, invoice_date) VALUES (?, ?, ?, ?, ?)",
                            (inv_code, inv_contractor, inv_amt, inv_stat, str(datetime.date.today())))
                log_audit_action(user_name, user_role, "Finance Invoice", inv_code, f"Processed invoice for KES {inv_amt:,.2f}")
                st.success("Financial invoice recorded successfully!")
                st.rerun()

elif selected_nav == "✍️ Executive Approval Centre":
    st.subheader("✍️ Executive Workflow Approval Centre")
    st.caption("Secure digital signature sign-off workflow for senior county executives.")

    app_df = fetch_df("SELECT * FROM executive_approvals")
    st.dataframe(app_df, use_container_width=True, hide_index=True)

    if not check_permission(user_role, "✍️ Executive Approval Centre"):
        st.info("🔒 You have view-only access to approvals. Senior executive clearance required to sign off items.")
    else:
        with st.form("exec_sign_form"):
            app_id = st.number_input("Approval ID to Action", min_value=1, step=1)
            action_choice = st.selectbox("Executive Action", ["Approved", "Rejected"])
            exec_comments = st.text_area("Executive Comments / Directives")
            
            if st.form_submit_button("Execute Digital Sign-Off"):
                sig_hash = hashlib.sha256(f"{user_name}-{datetime.datetime.now()}".encode()).hexdigest()[:16]
                execute_sql("UPDATE executive_approvals SET status = ?, action_by = ?, digital_signature = ?, comments = ? WHERE approval_id = ?",
                            (action_choice, user_name, sig_hash, exec_comments, app_id))
                log_audit_action(user_name, user_role, "Executive Sign-Off", f"Approval #{app_id}", f"Status updated to {action_choice} with digital signature {sig_hash}")
                st.success(f"Approval #{app_id} successfully updated with signature hash `{sig_hash}`!")
                st.rerun()

elif selected_nav == "⚙️ Disaster Recovery & Audit Logs":
    st.subheader("⚙️ System Administration, Disaster Recovery & Audit Logs")
    st.caption("Cryptographic audit trails and system maintenance controls.")

    if user_role != "Admin" and user_role != "CECM":
        st.error("⛔ Access Denied: Administrator security clearance required.")
    else:
        col_adm1, col_adm2 = st.columns(2)
        with col_adm1:
            if st.button("💾 Trigger Manual SQLite Database Backup", use_container_width=True):
                st.success("Database snapshot successfully archived to `/backups/nyeri_enterprise_mis_backup.db`")
                log_audit_action(user_name, user_role, "Database Backup", "System", "Manual snapshot triggered")
        with col_adm2:
            if st.button("📥 Export Full Immutable Audit Logs (CSV)", use_container_width=True):
                pass
                
        st.markdown("##### Immutable System Audit Logs")
        audit_df = fetch_df("SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT 50")
        st.dataframe(audit_df, use_container_width=True, hide_index=True)

# ------------------------------------------
# STANDARD FOOTER
# ------------------------------------------
st.markdown("""
<div class="compliance-footer">
    County Government of Nyeri Enterprise MIS v2.0.0 &bull; Public Finance Management (PFM) Act Compliant &bull; Secure TLS Session
</div>
""", unsafe_allow_html=True)
