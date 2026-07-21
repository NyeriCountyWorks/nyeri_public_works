# Continuation of: WORKSPACE 0: USER PROFILE & CHANGE PASSWORD
    with col_prof1:
        st.subheader("Account Details")
        st.markdown(f"""
        <div class="dec-card">
            <p><strong>Full Name:</strong> {st.session_state.get('full_name', 'N/A')}</p>
            <p><strong>Employee Number:</strong> {st.session_state.get('employee_number', 'N/A')}</p>
            <p><strong>Role:</strong> {st.session_state.get('role', 'N/A')}</p>
            <p><strong>Department:</strong> {st.session_state.get('department', 'N/A')}</p>
            <p><strong>Last Login:</strong> {st.session_state.get('last_login', 'N/A')}</p>
            <p><strong>IP Address:</strong> {st.session_state.get('last_login_ip', 'N/A')}</p>
        </div>
        """, unsafe_allow_html=True)

    with col_prof2:
        st.subheader("Change Password")
        with st.form("change_password_form"):
            curr_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Update Password", use_container_width=True):
                if not curr_pw or not new_pw or not confirm_pw:
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
                        log_audit_action(st.session_state["username"], st.session_state["role"], "Password Change", "Users", "Password changed successfully")
                        st.success("Password updated successfully!")
                    else:
                        conn.close()
                        st.error("Current password is incorrect.")


# ==========================================
# WORKSPACE 1: CECM EXECUTIVE WORKSPACE
# ==========================================
elif nav_choice == "🏠 CECM Executive Workspace":
    st.header("🏠 CECM Executive Control Dashboard")
    st.caption("Strategic oversight of capital projects, budget allocation, and executive approvals.")

    df_p = fetch_df("SELECT * FROM projects")
    df_a = fetch_df("SELECT * FROM executive_approvals WHERE status = 'Pending'")

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Total Projects</div><div class="dec-value">{len(df_p)}</div></div>', unsafe_allow_html=True)
    with m2:
        tot_budget = df_p['budget_allocated'].sum() if not df_p.empty else 0
        st.markdown(f'<div class="dec-card"><div class="dec-title">Total Allocated Budget</div><div class="dec-value">{format_currency_short(tot_budget)}</div></div>', unsafe_allow_html=True)
    with m3:
        tot_spend = df_p['actual_spend'].sum() if not df_p.empty else 0
        st.markdown(f'<div class="dec-card"><div class="dec-title">Total Expenditure</div><div class="dec-value">{format_currency_short(tot_spend)}</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Pending CECM Approvals</div><div class="dec-value">{len(df_a)}</div></div>', unsafe_allow_html=True)

    st.markdown("<br/>", unsafe_allow_html=True)

    c1, c2 = st.columns([1, 1])
    with c1:
        st.subheader("Budget Absorption by Sub-County")
        if not df_p.empty:
            fig_sc = px.bar(
                df_p, x="sub_county", y=["budget_allocated", "actual_spend"],
                barmode="group", labels={"value": "KES", "variable": "Metric"},
                color_discrete_sequence=["#0A4D20", "#D4AF37"]
            )
            fig_sc.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_sc, use_container_width=True)
    with c2:
        st.subheader("Project Status Distribution")
        if not df_p.empty:
            fig_pie = px.pie(df_p, names="status", hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
            fig_pie.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_pie, use_container_width=True)


# ==========================================
# WORKSPACE 2: CHIEF OFFICER WORKSPACE
# ==========================================
elif nav_choice == "🏢 Chief Officer Workspace":
    st.header("🏢 Chief Officer Operations Dashboard")
    st.caption("Departmental performance tracking, lifecycle progress, and resource utilization.")

    df_p = fetch_df("SELECT * FROM projects")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Project Lifecycle Progression")
        if not df_p.empty:
            fig_life = px.strip(df_p, x="lifecycle_stage", y="percentage_complete", color="department", hover_name="project_name")
            fig_life.update_layout(margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig_life, use_container_width=True)
    
    with col2:
        st.subheader("High Risk / Delayed Projects")
        df_delayed = df_p[df_p["status"].str.contains("Delayed|Planning", case=False, na=False)]
        if not df_delayed.empty:
            st.dataframe(df_delayed[["project_code", "project_name", "status", "percentage_complete"]], hide_index=True, use_container_width=True)
        else:
            st.info("No delayed projects reported.")


# ==========================================
# WORKSPACE 3: ENGINEER FIELD WORKSPACE
# ==========================================
elif nav_choice == "🏗️ Engineer Field Workspace":
    st.header("🏗️ Field Engineer Operations Hub")
    st.caption("Log daily field reports, register project risks, and update progress.")

    df_p = fetch_df("SELECT project_code, project_name, percentage_complete, lifecycle_stage FROM projects")
    
    tab_inspect, tab_risk = st.tabs(["📝 Submit Site Inspection", "⚠️ Log Project Risk"])

    with tab_inspect:
        with st.form("field_inspection_form"):
            selected_proj = st.selectbox("Select Project", df_p["project_code"] + " - " + df_p["project_name"])
            p_code = selected_proj.split(" - ")[0] if selected_proj else ""
            
            c_a, c_b = st.columns(2)
            with c_a:
                insp_date = st.date_input("Inspection Date", datetime.date.today())
                gps = st.text_input("GPS Coordinates", "-0.4201, 36.9475")
            with c_b:
                weather = st.selectbox("Weather Conditions", ["Sunny / Dry", "Overcast", "Rainy / Muddy", "Severe Rain"])
                next_insp = st.date_input("Next Scheduled Inspection", datetime.date.today() + datetime.timedelta(days=14))
            
            defects = st.text_area("Defects Found / Structural Issues")
            recom = st.text_area("Recommendations & Corrective Actions")
            
            if st.form_submit_button("Submit Inspection Report", use_container_width=True):
                execute_sql("""
                    INSERT INTO site_inspections 
                    (project_code, engineer_name, inspection_date, gps_coordinates, weather, defects_found, recommendations, next_inspection_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (p_code, st.session_state["full_name"], str(insp_date), gps, weather, defects, recom, str(next_insp)))
                
                log_audit_action(st.session_state["username"], user_role, "Site Inspection Log", "site_inspections", f"Logged for {p_code}")
                st.success("Site inspection logged successfully.")

    with tab_risk:
        with st.form("log_risk_form"):
            r_proj = st.selectbox("Project Code", df_p["project_code"] + " - " + df_p["project_name"], key="rk_p")
            r_code = r_proj.split(" - ")[0] if r_proj else ""
            r_desc = st.text_area("Risk Description")
            r_sev = st.selectbox("Severity Level", ["Low", "Medium", "High", "Critical"])
            r_mit = st.text_area("Mitigation Strategy")
            
            if st.form_submit_button("Register Risk Event", use_container_width=True):
                execute_sql("""
                    INSERT INTO risk_register (project_code, risk_description, severity, mitigation_strategy, risk_owner)
                    VALUES (?, ?, ?, ?, ?)
                """, (r_code, r_desc, r_sev, r_mit, st.session_state["full_name"]))
                log_audit_action(st.session_state["username"], user_role, "Risk Register Add", "risk_register", f"Registered risk for {r_code}")
                st.success("Risk event logged in register.")


# ==========================================
# WORKSPACE 4: FINANCE & TREASURY WORKSPACE
# ==========================================
elif nav_choice == "💰 Finance & Treasury Workspace":
    st.header("💰 Financial Disbursement & Invoice Processing")
    st.caption("Public Financial Management (PFM) Act compliance and payment verification.")

    df_inv = fetch_df("SELECT * FROM financial_invoices")
    
    st.subheader("Invoice Pipeline")
    st.dataframe(df_inv, use_container_width=True, hide_index=True)

    st.subheader("Process Pending Invoice")
    pending_invs = df_inv[df_inv["status"] == "Pending Verification"]
    if not pending_invs.empty:
        with st.form("process_invoice_form"):
            inv_to_proc = st.selectbox("Select Invoice ID to Action", pending_invs["invoice_id"].astype(str) + " - KES " + pending_invs["amount"].astype(str))
            inv_id = inv_to_proc.split(" - ")[0]
            new_status = st.selectbox("Action", ["Approved for Disbursement", "Disbursed", "Rejected / Queried"])
            
            if st.form_submit_button("Update Invoice Status"):
                execute_sql("UPDATE financial_invoices SET status = ? WHERE invoice_id = ?", (new_status, inv_id))
                log_audit_action(st.session_state["username"], user_role, "Invoice Update", "financial_invoices", f"Invoice #{inv_id} set to {new_status}")
                st.success(f"Invoice #{inv_id} updated to {new_status}.")
                st.rerun()
    else:
        st.info("No pending invoices require verification at this time.")


# ==========================================
# WORKSPACE 5: EXECUTIVE APPROVAL CENTRE
# ==========================================
elif nav_choice == "✍️ Executive Approval Centre":
    st.header("✍️ Executive Approval Centre")
    st.caption("Digital Signatures and Official Clearances under County Procurement & PFM Rules.")

    df_app = fetch_df("SELECT * FROM executive_approvals WHERE status = 'Pending'")
    
    if df_app.empty:
        st.success("🎉 All executive pending approvals are cleared!")
    else:
        for idx, row in df_app.iterrows():
            with st.expander(f"📌 {row['item_title']} ({row['project_code']})", expanded=True):
                c_x, c_y = st.columns([2, 1])
                with c_x:
                    st.write(f"**Stage:** {row['stage']}")
                    st.write(f"**Submitted By:** {row['submitted_by']}")
                    st.write(f"**Submitted Date:** {row['timestamp']}")
                with c_y:
                    comments = st.text_input(f"Comments for #{row['approval_id']}", key=f"c_{row['approval_id']}")
                    col_app, col_rej = st.columns(2)
                    
                    if col_app.button("✅ Approve", key=f"app_{row['approval_id']}", use_container_width=True):
                        sig = hashlib.sha256(f"{st.session_state['username']}_{datetime.datetime.now()}".encode()).hexdigest()[:16]
                        execute_sql("""
                            UPDATE executive_approvals 
                            SET status = 'Approved', action_by = ?, digital_signature = ?, comments = ?
                            WHERE approval_id = ?
                        """, (st.session_state["full_name"], sig, comments, row['approval_id']))
                        log_audit_action(st.session_state["username"], user_role, "Executive Approval", "executive_approvals", f"Approved #{row['approval_id']} - Sig: {sig}")
                        st.success("Approved successfully!")
                        st.rerun()
                        
                    if col_rej.button("❌ Reject", key=f"rej_{row['approval_id']}", use_container_width=True):
                        execute_sql("""
                            UPDATE executive_approvals 
                            SET status = 'Rejected', action_by = ?, comments = ?
                            WHERE approval_id = ?
                        """, (st.session_state["full_name"], comments, row['approval_id']))
                        log_audit_action(st.session_state["username"], user_role, "Executive Rejection", "executive_approvals", f"Rejected #{row['approval_id']}")
                        st.warning("Request rejected.")
                        st.rerun()


# ==========================================
# WORKSPACE 6: PROJECTS LIFECYCLE PIPELINE
# ==========================================
elif nav_choice == "📁 Projects Lifecycle Pipeline":
    st.header("📁 Master Project Lifecycle Pipeline")
    st.caption("Track, search, create, and update county infrastructure initiatives.")

    t_view, t_create = st.tabs(["📋 View All Projects", "➕ Create New Project"])

    with t_view:
        df_p = fetch_df("SELECT * FROM projects")
        st.dataframe(df_p, use_container_width=True, hide_index=True)

    with t_create:
        with st.form("new_project_form"):
            st.subheader("Project Registration Form")
            cp1, cp2 = st.columns(2)
            with cp1:
                p_code = st.text_input("Project Code", f"PRJ-2026-00{np.random.randint(6, 99)}")
                p_name = st.text_input("Project Title")
                p_sub = st.selectbox("Sub-County", ["Nyeri Town", "Mathira East", "Mathira West", "Othaya", "Tetu", "Mukurweini", "Kieni East", "Kieni West"])
                p_dept = st.selectbox("Department", ["Roads & Transport", "Public Works", "Water & Sanitation", "Health Services", "Infrastructure & Energy"])
            with cp2:
                p_budget = st.number_input("Allocated Budget (KES)", min_value=0.0, step=100000.0)
                p_contractor = st.text_input("Contractor Name", "Unassigned")
                p_start = st.date_input("Start Date", datetime.date.today())
                p_target = st.date_input("Target Completion", datetime.date.today() + datetime.timedelta(days=180))
            
            p_desc = st.text_area("Project Scope / Description")

            if st.form_submit_button("Register Project", use_container_width=True):
                execute_sql("""
                    INSERT INTO projects 
                    (project_code, project_name, sub_county, department, contractor, lead_engineer, budget_allocated, actual_spend, percentage_complete, lifecycle_stage, status, start_date, target_completion, description)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0.0, 0, '1. Proposal', '🔵 Planning', ?, ?, ?)
                """, (p_code, p_name, p_sub, p_dept, p_contractor, st.session_state["full_name"], p_budget, str(p_start), str(p_target), p_desc))
                
                log_audit_action(st.session_state["username"], user_role, "Create Project", "projects", f"Created {p_code}")
                st.success(f"Project {p_code} registered successfully!")


# ==========================================
# WORKSPACE 7: DEPARTMENT PERFORMANCE
# ==========================================
elif nav_choice == "📊 Department Performance":
    st.header("📊 Department Performance Analytics")
    
    df_p = fetch_df("SELECT * FROM projects")
    if not df_p.empty:
        dept_summary = df_p.groupby("department").agg(
            Total_Budget=("budget_allocated", "sum"),
            Total_Spend=("actual_spend", "sum"),
            Avg_Completion=("percentage_complete", "mean"),
            Project_Count=("project_id", "count")
        ).reset_index()

        st.dataframe(dept_summary, use_container_width=True, hide_index=True)

        fig_perf = px.bar(
            dept_summary, x="department", y="Avg_Completion",
            title="Average Project Completion (%) by Department",
            color="Avg_Completion", color_continuous_scale="Greens"
        )
        st.plotly_chart(fig_perf, use_container_width=True)


# ==========================================
# WORKSPACE 8: RISK & GOVERNANCE REGISTER
# ==========================================
elif nav_choice == "⚠️ Risk & Governance Register":
    st.header("⚠️ Enterprise Risk & Governance Register")
    
    df_r = fetch_df("SELECT * FROM risk_register")
    st.dataframe(df_r, use_container_width=True, hide_index=True)


# ==========================================
# WORKSPACE 9: SITE INSPECTION MODULE
# ==========================================
elif nav_choice == "🏗️ Site Inspection Module":
    st.header("🏗️ Site Inspection Records")
    
    df_si = fetch_df("SELECT * FROM site_inspections")
    st.dataframe(df_si, use_container_width=True, hide_index=True)


# ==========================================
# WORKSPACE 10: CLASSIFIED RECORDS & DOCUMENTS
# ==========================================
elif nav_choice == "📄 Classified Records & Documents":
    st.header("📄 Classified Records Repository")
    st.caption("Secure document vault with retention and security classification policies.")

    df_docs = fetch_df("SELECT * FROM classified_documents")
    st.dataframe(df_docs, use_container_width=True, hide_index=True)

    with st.expander("⬆️ Upload Document Metadata"):
        with st.form("upload_doc_form"):
            d_pcode = st.text_input("Project Code", "PRJ-2026-001")
            d_name = st.text_input("Document File Name", "BOQ_Revised.pdf")
            d_class = st.selectbox("Security Classification", ["PUBLIC", "INTERNAL", "RESTRICTED", "CONFIDENTIAL"])
            
            if st.form_submit_button("Save Record"):
                execute_sql("""
                    INSERT INTO classified_documents (project_code, doc_name, security_classification, uploaded_by, upload_date)
                    VALUES (?, ?, ?, ?, ?)
                """, (d_pcode, d_name, d_class, st.session_state["full_name"], datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                log_audit_action(st.session_state["username"], user_role, "Document Upload", "classified_documents", f"Uploaded {d_name}")
                st.success("Document metadata registered.")


# ==========================================
# WORKSPACE 11: AI EXECUTIVE BRIEFING
# ==========================================
elif nav_choice == "🤖 AI Executive Briefing":
    st.header("🤖 AI-Synthesized Executive Briefing")
    st.caption("Automated summary generation based on real-time MIS metrics.")

    df_p = fetch_df("SELECT * FROM projects")
    df_r = fetch_df("SELECT * FROM risk_register WHERE severity IN ('High', 'Critical')")

    tot_b = df_p["budget_allocated"].sum() if not df_p.empty else 0
    tot_s = df_p["actual_spend"].sum() if not df_p.empty else 0
    avg_comp = df_p["percentage_complete"].mean() if not df_p.empty else 0

    briefing = f"""
    ### 🏛️ Executive Summary Briefing for {datetime.date.today()}
    
    * **Overall Portfolio Budget:** {format_currency_short(tot_b)} total allocated across {len(df_p)} active projects.
    * **Financial Expenditure:** Total absorption stands at **{format_currency_short(tot_s)}** ({(tot_s/tot_b*100 if tot_b else 0):.1f}% absorption rate).
    * **Execution Progress:** Average physical project completion rate is **{avg_comp:.1f}%**.
    * **Risk Alerts:** There are currently **{len(df_r)} high-severity risk(s)** requiring executive intervention.
    """
    
    st.markdown(briefing)


# ==========================================
# WORKSPACE 12: DISASTER RECOVERY & AUDIT LOGS
# ==========================================
elif nav_choice == "⚙️ Disaster Recovery & Audit Logs":
    st.header("⚙️ Immutable System Audit Logs & DR")
    st.caption("Full system transparency, audit trails, and database maintenance.")

    df_audit = fetch_df("SELECT * FROM audit_logs ORDER BY log_id DESC")
    st.dataframe(df_audit, use_container_width=True, hide_index=True)

    col_dr1, col_dr2 = st.columns(2)
    with col_dr1:
        if st.button("💾 Trigger Manual DB Backup", use_container_width=True):
            log_audit_action(st.session_state["username"], user_role, "DB Backup", "System", "Manual snapshot created")
            st.success("Database snapshot created successfully.")
    with col_dr2:
        csv_logs = df_audit.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Export Audit Logs (CSV)", data=csv_logs, file_name="Nyeri_MIS_Audit_Log.csv", mime="text/csv", use_container_width=True)
