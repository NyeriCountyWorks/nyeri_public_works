import base64
import datetime
import os
import sqlite3
import textwrap
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# --- 1. DATABASE INITIALIZATION & SEEDING ---
def init_enterprise_db():
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        cursor = conn.cursor()

        # Users Table
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
            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('engineer', 'eng123', 'Eng. John Mwangi', 'Lead Engineer')")
            cursor.execute("INSERT INTO users (username, password, full_name, role) VALUES ('director', 'dir123', 'Dr. Lucy Wambui', 'Director Public Works')")

        # Projects Table
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
                workflow_stage TEXT DEFAULT 'Draft', 
                status TEXT DEFAULT 'Active',
                created_by TEXT,
                last_updated DATETIME
            )
        ''')

        try:
            cursor.execute("ALTER TABLE projects ADD COLUMN lead_engineer TEXT DEFAULT 'Eng. John Mwangi'")
        except sqlite3.OperationalError:
            pass

        if cursor.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0:
            sample_projects = [
                ("PRJ-2026-001", "Karatina Market Modernization & Drainage", "Mathira East", "Infrastructure & Energy", "Apex Builders Ltd", "Eng. David Kariuki", 45000000.0, 38000000.0, 85, "Director Review", "Active", "admin", "2026-07-21 09:00:00"),
                ("PRJ-2026-002", "Othaya Sub-County Hospital Wing Extension", "Othaya", "Health Services", "Mount Kenya Construction", "Eng. John Mwangi", 60000000.0, 60000000.0, 100, "Completed", "Completed", "director", "2026-07-20 11:30:00"),
                ("PRJ-2026-003", "Tetu High-Altitude Training Water Pipeline", "Tetu", "Water & Sanitation", "Aberdare Water Systems", "Eng. Grace Nderitu", 18500000.0, 12000000.0, 65, "Engineer Signoff", "Active", "engineer", "2026-07-21 14:15:00"),
                ("PRJ-2026-004", "Mukurwe-ini Feeder Roads Tarmacking", "Mukurweini", "Roads & Transport", "Highland Civils Ltd", "Eng. Peter Kamau", 82000000.0, 25000000.0, 30, "Project Officer Review", "Delayed", "engineer", "2026-07-18 10:45:00"),
                ("PRJ-2026-005", "Nyeri Town Bus Park Stormwater System", "Nyeri Town", "Public Works", "County In-House", "Eng. John Mwangi", 12000000.0, 1500000.0, 15, "Project Officer Review", "Active", "admin", "2026-07-21 10:20:00"),
                ("PRJ-2026-006", "Kieni East Earth Dam Rehabilitation", "Kieni East", "Water & Sanitation", "Rift Valley Hydraulics", "Eng. Grace Nderitu", 35000000.0, 32000000.0, 90, "Chief Officer Approval", "Active", "chief", "2026-07-19 08:50:00"),
                ("PRJ-2026-007", "Chinga Dam Eco-Tourism Infrastructure", "Othaya", "Public Works", "GreenPath Contractors", "Eng. David Kariuki", 22000000.0, 0.0, 0, "Project Officer Review", "Rejected", "engineer", "2026-07-15 16:00:00")
            ]
            cursor.executemany("""
                INSERT INTO projects 
                (project_code, project_name, sub_county, department, contractor, lead_engineer, budget_allocated, actual_spend, percentage_complete, workflow_stage, status, created_by, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, sample_projects)

        # Audit Log & Documents
        cursor.execute('CREATE TABLE IF NOT EXISTS documents (doc_id INTEGER PRIMARY KEY AUTOINCREMENT, project_code TEXT, filename TEXT, file_path TEXT, uploaded_by TEXT, upload_timestamp DATETIME)')
        cursor.execute('CREATE TABLE IF NOT EXISTS audit_logs (log_id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME, username TEXT, action TEXT, target_record TEXT, details TEXT)')

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

def fetch_project_data():
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        df = pd.read_sql_query("SELECT * FROM projects", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def fetch_audit_logs(limit=20):
    try:
        conn = sqlite3.connect("nyeri_public_works.db")
        df = pd.read_sql_query(f"SELECT timestamp, username, action, target_record, details FROM audit_logs ORDER BY log_id DESC LIMIT {limit}", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def format_currency_short(val):
    if val >= 1e9: return f"KES {val/1e9:.2f}B"
    elif val >= 1e6: return f"KES {val/1e6:.2f}M"
    elif val >= 1e3: return f"KES {val/1e3:.2f}K"
    return f"KES {val:,.2f}"

def get_time_greeting():
    hour = datetime.datetime.now().hour
    if hour < 12: return "Good Morning"
    elif hour < 17: return "Good Afternoon"
    return "Good Evening"


# --- 2. CUSTOM ENTERPRISE CSS ---
def inject_custom_styles():
    st.markdown("""
    <style>
        /* Enterprise Sidebar Gradient */
        [data-testid="stSidebar"] {
            background-color: #0A4D20 !important;
            background-image: linear-gradient(180deg, #0A4D20 0%, #031e0c 100%) !important;
            color: #FFFFFF !important;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label, [data-testid="stSidebar"] div {
            color: #FFFFFF !important;
            font-family: 'Inter', sans-serif;
        }
        [data-testid="stSidebar"] strong { color: #D4AF37 !important; }

        /* Modern KPI Card Styling */
        .kpi-card {
            background: #FFFFFF;
            border-radius: 12px;
            padding: 18px 20px;
            border: 1px solid #E5E7EB;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
            margin-bottom: 15px;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .kpi-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
        }
        .kpi-title { font-size: 13px; font-weight: 600; color: #6B7280; text-transform: uppercase; letter-spacing: 0.5px; }
        .kpi-value { font-size: 28px; font-weight: 800; color: #111827; margin: 4px 0; }
        .kpi-badge-up { color: #10B981; font-size: 12px; font-weight: 700; background: #ECFDF5; padding: 3px 8px; border-radius: 20px; display: inline-block; }
        .kpi-badge-down { color: #EF4444; font-size: 12px; font-weight: 700; background: #FEF2F2; padding: 3px 8px; border-radius: 20px; display: inline-block; }

        /* Project Modern Grid Cards */
        .project-card {
            background: #FFFFFF;
            border-radius: 10px;
            border: 1px solid #E2E8F0;
            padding: 16px;
            margin-bottom: 16px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.02);
        }
        .project-card-header { font-size: 16px; font-weight: 700; color: #0A4D20; margin-bottom: 6px; }
        .status-pill {
            font-size: 11px; font-weight: 700; padding: 2px 10px; border-radius: 12px; text-transform: uppercase;
        }
        .status-active { background: #D1FAE5; color: #065F46; }
        .status-delayed { background: #FEE2E2; color: #991B1B; }
        .status-completed { background: #E0E7FF; color: #3730A3; }

        /* Approval Workflow Stepper */
        .stepper-wrapper { display: flex; justify-content: space-between; margin: 15px 0; }
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

        /* Notification Center Cards */
        .notif-card {
            padding: 12px; border-radius: 8px; background: #F9FAFB; border-left: 4px solid #0A4D20; margin-bottom: 10px;
        }
    </style>
    """, unsafe_allow_html=True)


# --- 3. INITIALIZE APP & AUTHENTICATION ---
st.set_page_config(page_title="Nyeri Public Works MIS", layout="wide", initial_sidebar_state="expanded")
inject_custom_styles()
init_enterprise_db()

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("<h1 style='text-align: center; color: #0A4D20;'>🏛️ County Government of Nyeri</h1>", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #D4AF37; margin-top: -15px;'>Public Works & Infrastructure MIS Enterprise Portal</h3>", unsafe_allow_html=True)

    _, auth_col, _ = st.columns([1, 1.5, 1])
    with auth_col:
        with st.form("login_form"):
            st.subheader("🔒 Secure Sign In")
            u_input = st.text_input("Username")
            p_input = st.text_input("Password", type="password")
            if st.form_submit_button("Sign In Securely", use_container_width=True):
                user_data = verify_login(u_input, p_input)
                if user_data:
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = user_data["username"]
                    st.session_state["role"] = user_data["role"]
                    st.session_state["full_name"] = user_data["full_name"]
                    log_audit_action(user_data["username"], "Login", "System", "Successful Enterprise Auth")
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
    st.stop()


# --- 4. ENTERPRISE SIDEBAR NAVIGATION MENU ---
st.sidebar.markdown(f"""
<div style="text-align: center; padding: 10px 0;">
    <h2 style="color: #FFFFFF; font-weight: 800; margin: 0;">NYERI COUNTY</h2>
    <span style="color: #D4AF37; font-size: 11px; letter-spacing: 1px;">PUBLIC WORKS MIS</span>
</div>
<hr style="border: 0; border-top: 1px solid rgba(255, 255, 255, 0.15); margin-bottom: 15px;" />
""", unsafe_allow_html=True)

st.sidebar.markdown(f"👤 **{st.session_state['full_name']}**")
st.sidebar.markdown(f"🛡️ Role: **{st.session_state['role']}**")

st.sidebar.markdown("---")

nav_choice = st.sidebar.radio(
    "SYSTEM MODULES",
    [
        "🏠 Executive Home",
        "📂 Projects Portfolio",
        "📄 Documents Repository",
        "💰 Finance & Budget",
        "👷 Contractor Performance",
        "🗺️ GIS Map Center",
        "📊 Reports & Scorecards",
        "🔔 Notification Center",
        "🤖 Ask Nyeri AI",
        "⚙️ System & Audit Trail"
    ]
)

if st.sidebar.button("Logout"):
    log_audit_action(st.session_state["username"], "Logout", "System", "User logged out")
    st.session_state["authenticated"] = False
    st.rerun()

df = fetch_project_data()

# ==========================================
# 1. 🏠 EXECUTIVE HOME & LANDING PAGE
# ==========================================
if nav_choice == "🏠 Executive Home":
    greeting = get_time_greeting()
    st.markdown(f"""
    <div style="background-color: #F0FDF4; border-left: 6px solid #0A4D20; padding: 16px 24px; border-radius: 8px; margin-bottom: 24px;">
        <h2 style="color: #0A4D20; margin: 0;">☀️ {greeting}, {st.session_state['full_name']}!</h2>
        <p style="color: #4B5563; margin: 4px 0 0 0;">Welcome back. Here is your executive portfolio pulse for today, {datetime.datetime.now().strftime('%B %d, %Y')}.</p>
    </div>
    """, unsafe_allow_html=True)

    if not df.empty:
        total_p = len(df)
        active_p = len(df[df["status"] == "Active"])
        delayed_p = len(df[df["status"] == "Delayed"])
        total_b = df["budget_allocated"].sum()
        total_s = df["actual_spend"].sum()
        util_pct = (total_s / total_b * 100) if total_b > 0 else 0

        # Modern KPI Cards Row
        kpi1, kpi2, kpi3, kpi4 = st.columns(4)
        with kpi1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Projects</div>
                <div class="kpi-value">{total_p}</div>
                <span class="kpi-badge-up">▲ +2 this month</span>
            </div>
            """, unsafe_allow_html=True)

        with kpi2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Active Infrastructure</div>
                <div class="kpi-value">{active_p}</div>
                <span class="kpi-badge-up">{(active_p/total_p*100):.0f}% operational</span>
            </div>
            """, unsafe_allow_html=True)

        with kpi3:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Delayed Projects</div>
                <div class="kpi-value">{delayed_p}</div>
                <span class="kpi-badge-down">▼ {delayed_p} requires review</span>
            </div>
            """, unsafe_allow_html=True)

        with kpi4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Total Portfolio Budget</div>
                <div class="kpi-value">{format_currency_short(total_b)}</div>
                <span class="kpi-badge-up">Spend: {format_currency_short(total_s)}</span>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Row 2: Circular Progress Ring & Sunburst Chart
        c_left, c_right = st.columns([1, 1.5])

        with c_left:
            st.subheader("🎯 Budget Utilization Gauge")
            fig_gauge = go.Figure(go.Indicator(
                mode="gauge+number",
                value=util_pct,
                number={'suffix': "%", 'font': {'size': 36, 'color': "#0A4D20"}},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1},
                    'bar': {'color': "#0A4D20"},
                    'bgcolor': "white",
                    'borderwidth': 2,
                    'bordercolor': "#E5E7EB",
                    'steps': [
                        {'range': [0, 70], 'color': "#E0E7FF"},
                        {'range': [70, 90], 'color': "#FEF3C7"},
                        {'range': [90, 100], 'color': "#FEE2E2"}
                    ],
                }
            ))
            fig_gauge.update_layout(height=280, margin=dict(t=30, b=10, l=30, r=30))
            st.plotly_chart(fig_gauge, use_container_width=True)

        with c_right:
            st.subheader("🌐 Portfolio Breakdown (Dept ➔ Sub-County)")
            fig_sunburst = px.sunburst(
                df,
                path=['department', 'sub_county', 'status'],
                values='budget_allocated',
                color='status',
                color_discrete_map={'Active': '#10B981', 'Delayed': '#EF4444', 'Completed': '#3B82F6', 'Rejected': '#6B7280'}
            )
            fig_sunburst.update_layout(height=300, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig_sunburst, use_container_width=True)


# ==========================================
# 2. 📂 PROJECTS PORTFOLIO
# ==========================================
elif nav_choice == "📂 Projects Portfolio":
    st.subheader("📂 Infrastructure Projects Portfolio")
    
    view_type = st.radio("Display Layout", ["🎴 Modern Cards View", "📋 Detailed Table View", "🔄 Workflow Stepper Visualizer"], horizontal=True)

    if view_type == "🎴 Modern Cards View":
        cols = st.columns(3)
        for idx, row in df.iterrows():
            with cols[idx % 3]:
                status_class = "status-active" if row["status"] == "Active" else ("status-delayed" if row["status"] == "Delayed" else "status-completed")
                st.markdown(f"""
                <div class="project-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span class="status-pill {status_class}">{row['status']}</span>
                        <span style="font-size: 12px; color: #6B7280; font-weight:600;">{row['project_code']}</span>
                    </div>
                    <div class="project-card-header" style="margin-top:8px;">{row['project_name']}</div>
                    <div style="font-size: 13px; color: #4B5563;">📍 Sub-County: <strong>{row['sub_county']}</strong></div>
                    <div style="font-size: 13px; color: #4B5563;">👷 Engineer: <strong>{row['lead_engineer']}</strong></div>
                    <div style="font-size: 15px; font-weight:700; color:#0A4D20; margin: 10px 0 4px 0;">{format_currency_short(row['budget_allocated'])}</div>
                </div>
                """, unsafe_allow_html=True)
                st.progress(int(row['percentage_complete'])/100)

    elif view_type == "📋 Detailed Table View":
        st.dataframe(df, use_container_width=True, hide_index=True)

    elif view_type == "🔄 Workflow Stepper Visualizer":
        st.info("Select a project below to visualize its multi-tier county governance approval stage:")
        selected_p = st.selectbox("Select Project", df["project_name"].unique())
        p_row = df[df["project_name"] == selected_p].iloc[0]

        stages = ["Project Officer Review", "Engineer Signoff", "Director Review", "Chief Officer Approval", "Completed"]
        current_stage = p_row["workflow_stage"]
        curr_idx = stages.index(current_stage) if current_stage in stages else 0

        stepper_html = '<div class="stepper-wrapper">'
        for i, s_name in enumerate(stages):
            if i < curr_idx:
                s_class = "stepper-complete"
                icon = "✓"
            elif i == curr_idx:
                s_class = "stepper-active"
                icon = "🔄"
            else:
                s_class = ""
                icon = str(i+1)
            
            stepper_html += f"""
            <div class="stepper-item {s_class}">
                <div class="stepper-circle">{icon}</div>
                <div class="stepper-title">{s_name}</div>
            </div>
            """
        stepper_html += '</div>'
        st.markdown(stepper_html, unsafe_allow_html=True)


# ==========================================
# 3. 💰 FINANCE & BUDGET
# ==========================================
elif nav_choice == "💰 Finance & Budget":
    st.subheader("💰 Financial Analytics & Budget Distribution")
    
    st.markdown("### Budget Allocation Treemap by Department")
    fig_tree = px.treemap(
        df,
        path=['department', 'contractor', 'project_name'],
        values='budget_allocated',
        color='actual_spend',
        color_continuous_scale='Greens'
    )
    fig_tree.update_layout(height=450)
    st.plotly_chart(fig_tree, use_container_width=True)


# ==========================================
# 4. 🗺️ GIS MAP CENTER
# ==========================================
elif nav_choice == "🗺️ GIS Map Center":
    st.subheader("🗺️ County Infrastructure GIS Map")
    
    coords = {
        "Mathira East": (-0.4812, 37.1281), "Othaya": (-0.5439, 36.9472),
        "Tetu": (-0.4350, 36.8833), "Mukurweini": (-0.5606, 37.0483),
        "Nyeri Town": (-0.4201, 36.9476), "Kieni East": (-0.1500, 37.0500)
    }

    df["lat"] = df["sub_county"].map(lambda x: coords.get(x, (-0.4201, 36.9476))[0] + np.random.uniform(-0.005, 0.005))
    df["lon"] = df["sub_county"].map(lambda x: coords.get(x, (-0.4201, 36.9476))[1] + np.random.uniform(-0.005, 0.005))

    fig_map = px.scatter_mapbox(
        df, lat="lat", lon="lon", hover_name="project_name",
        hover_data={"budget_allocated": ":,.2f", "percentage_complete": True, "lead_engineer": True, "lat": False, "lon": False},
        color="status", zoom=9.5, center={"lat": -0.4201, "lon": 36.9476}, height=550
    )
    fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_map, use_container_width=True)


# ==========================================
# 5. 🔔 NOTIFICATION CENTER
# ==========================================
elif nav_choice == "🔔 Notification Center":
    st.subheader("🔔 Enterprise Notification Feed")

    notifications = [
        {"icon": "⚠️", "title": "Schedule Delay Warning", "time": "10 min ago", "body": "Mukurwe-ini Feeder Roads Tarmacking has experienced schedule variance."},
        {"icon": "✅", "title": "Project Approved", "time": "1 hour ago", "body": "Kieni East Earth Dam Rehabilitation cleared Chief Officer signoff."},
        {"icon": "💡", "title": "High Budget Threshold Alert", "time": "3 hours ago", "body": "Karatina Market Modernization crossed 80% budget spend threshold."},
        {"icon": "📄", "title": "Document Uploaded", "time": "Yesterday", "body": "Tender specification PDF uploaded by Eng. Grace Nderitu."}
    ]

    for n in notifications:
        st.markdown(f"""
        <div class="notif-card">
            <div style="display:flex; justify-content:space-between;">
                <strong>{n['icon']} {n['title']}</strong>
                <span style="font-size:12px; color:#6B7280;">{n['time']}</span>
            </div>
            <div style="font-size:13px; color:#374151; margin-top:4px;">{n['body']}</div>
        </div>
        """, unsafe_allow_html=True)


# ==========================================
# 6. 🤖 ASK NYERI AI
# ==========================================
elif nav_choice == "🤖 Ask Nyeri AI":
    st.subheader("🤖 Ask Nyeri AI - Natural Language Query Assistant")
    st.caption("Ask questions about project budgets, delayed items, engineers, or sub-county statistics.")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            {"role": "assistant", "content": "Hello! I am Nyeri AI. Ask me anything about current projects, budgets, or delay statuses."}
        ]

    for msg in st.session_state.chat_history:
        st.chat_message(msg["role"]).write(msg["content"])

    user_query = st.chat_input("Type your question (e.g. 'Show delayed projects' or 'Total budget')...")
    if user_query:
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        st.chat_message("user").write(user_query)

        q_lower = user_query.lower()
        if "delayed" in q_lower:
            del_df = df[df["status"] == "Delayed"]
            names = ", ".join(del_df["project_name"].tolist()) if not del_df.empty else "None"
            ans = f"There are currently **{len(del_df)} delayed project(s)**: {names}."
        elif "budget" in q_lower or "total spend" in q_lower:
            ans = f"The total portfolio budget is **{format_currency_short(df['budget_allocated'].sum())}** with total spend at **{format_currency_short(df['actual_spend'].sum())}**."
        elif "hospital" in q_lower or "othaya" in q_lower:
            ans = "The Othaya Sub-County Hospital Wing Extension is 100% completed with KES 60M budget."
        else:
            ans = f"I retrieved {len(df)} projects in the database. Try asking specifically about 'delayed projects', 'budget', or sub-counties like 'Othaya'."

        st.session_state.chat_history.append({"role": "assistant", "content": ans})
        st.chat_message("assistant").write(ans)


# ==========================================
# 7. 📄 DOCUMENTS, 👷 CONTRACTORS, 📊 REPORTS & ⚙️ AUDIT
# ==========================================
elif nav_choice == "📄 Documents Repository":
    st.subheader("📄 County Document Repository")
    st.info("Attached files and engineering specifications for public works contracts.")
    st.dataframe(pd.DataFrame({
        "Project Code": ["PRJ-2026-001", "PRJ-2026-003"],
        "Filename": ["Karatina_Drainage_Specs.pdf", "Tetu_Water_Pipeline_BOQ.xlsx"],
        "Uploaded By": ["admin", "engineer"],
        "Timestamp": ["2026-07-20 10:00:00", "2026-07-21 11:30:00"]
    }), use_container_width=True)

elif nav_choice == "👷 Contractor Performance":
    st.subheader("👷 Contractor Performance & Workload")
    c_df = df.groupby("contractor").agg(Projects=("project_id", "count"), Avg_Completion=("percentage_complete", "mean"), Total_Contract_Value=("budget_allocated", "sum")).reset_index()
    st.dataframe(c_df, use_container_width=True)

elif nav_choice == "📊 Reports & Scorecards":
    st.subheader("📊 Departmental Scorecards & Analytics")
    dept_df = df.groupby("department").agg(Total_Budget=("budget_allocated", "sum"), Total_Spend=("actual_spend", "sum"), Avg_Progress=("percentage_complete", "mean")).reset_index()
    st.dataframe(dept_df, use_container_width=True)

elif nav_choice == "⚙️ System & Audit Trail":
    st.subheader("🔐 System Security & Audit Trail")
    logs = fetch_audit_logs()
    st.dataframe(logs, use_container_width=True)
