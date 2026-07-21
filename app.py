st.markdown(f"""
        * **Full Name:** {st.session_state['full_name']}
        * **Username:** {st.session_state['username']}
        * **Employee Number:** {st.session_state['employee_number']}
        * **Role:** {st.session_state['role']}
        * **Department:** {st.session_state['department']}
        * **Last Login:** `{st.session_state.get('last_login', 'N/A')}`
        * **Last Login IP:** `{st.session_state.get('last_login_ip', 'N/A')}`
        """)

    with col_prof2:
        st.subheader("Change Password")
        with st.form("change_pass_form"):
            curr_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Update Password", use_container_width=True):
                if not curr_pw or not new_pw or not confirm_pw:
                    st.error("All fields are required.")
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
                        log_audit_action(st.session_state["username"], st.session_state["role"], "Password Change", "users", "User updated password")
                        st.success("Password updated successfully!")
                    else:
                        conn.close()
                        st.error("Current password is incorrect.")


# ==========================================
# WORKSPACE 1: EXECUTIVE WORKSPACES (CECM / CHIEF OFFICER)
# ==========================================
elif nav_choice in ["🏠 CECM Executive Workspace", "🏢 Chief Officer Workspace"]:
    st.header(f"{nav_choice}")
    st.caption("Strategic Dashboard & High-Level Decision Support System")

    df_p = fetch_df("SELECT * FROM projects")
    total_budget = df_p["budget_allocated"].sum()
    total_spend = df_p["actual_spend"].sum()
    avg_progress = df_p["percentage_complete"].mean()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Total Allocated Budget</div><div class="dec-value">{format_currency_short(total_budget)}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Actual Expenditure</div><div class="dec-value">{format_currency_short(total_spend)}</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Avg Execution Rate</div><div class="dec-value">{avg_progress:.1f}%</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="dec-card"><div class="dec-title">Total Active Projects</div><div class="dec-value">{len(df_p)}</div></div>', unsafe_allow_html=True)

    st.write("")
    st.subheader("Departmental Budget Allocation vs Actual Spend")
    fig_bar = px.bar(
        df_p, 
        x="department", 
        y=["budget_allocated", "actual_spend"], 
        barmode="group",
        labels={"value": "Amount (KES)", "variable": "Metric", "department": "Department"},
        color_discrete_map={"budget_allocated": "#0A4D20", "actual_spend": "#D4AF37"}
    )
    st.plotly_chart(fig_bar, use_container_width=True)


# ==========================================
# WORKSPACE 2: ENGINEER FIELD WORKSPACE
# ==========================================
elif nav_choice == "🏗️ Engineer Field Workspace":
    st.header("🏗️ Engineer Field Workspace")
    st.caption("Technical project oversight, assigned site monitoring, and engineering logs.")

    df_eng = fetch_df("SELECT * FROM projects WHERE lead_engineer = ?", (user_name,))
    if df_eng.empty:
        df_eng = fetch_df("SELECT * FROM projects")

    st.subheader("Assigned Projects Overview")
    st.dataframe(df_eng, use_container_width=True, hide_index=True)


# ==========================================
# WORKSPACE 3: FINANCE & TREASURY WORKSPACE
# ==========================================
elif nav_choice == "💰 Finance & Treasury Workspace":
    st.header("💰 Finance & Treasury Workspace")
    st.caption("Invoice processing, payment disbursement tracking, and budget compliance.")

    df_inv = fetch_df("SELECT * FROM financial_invoices")
    st.subheader("Invoice & Payment Register")
    st.dataframe(df_inv, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Process & Verify Pending Invoice")
    with st.form("invoice_process_form"):
        inv_id = st.number_input("Invoice ID", min_value=1, step=1)
        new_status = st.selectbox("Update Status", ["Pending Verification", "Approved for Payment", "Disbursed", "Rejected"])
        
        if st.form_submit_button("Submit Invoice Status Update", use_container_width=True):
            execute_sql("UPDATE financial_invoices SET status = ? WHERE invoice_id = ?", (new_status, inv_id))
            log_audit_action(st.session_state["username"], user_role, "Invoice Processing", "financial_invoices", f"Invoice ID {inv_id} updated to {new_status}")
            st.success(f"Invoice #{inv_id} status successfully updated to '{new_status}'.")
            st.rerun()


# ==========================================
# WORKSPACE 4: EXECUTIVE APPROVAL CENTRE
# ==========================================
elif nav_choice == "✍️ Executive Approval Centre":
    st.header("✍️ Executive Approval Centre")
    st.caption("Review, sign, and authorize budget reallocations and site variations under PFM guidelines.")

    df_app = fetch_df("SELECT * FROM executive_approvals WHERE status = 'Pending'")
    if df_app.empty:
        st.info("🎉 No pending executive approvals at this time.")
    else:
        st.dataframe(df_app, use_container_width=True, hide_index=True)
        st.divider()
        st.subheader("Action Pending Items")

        for _, row in df_app.iterrows():
            with st.expander(f"📌 Item #{row['approval_id']}: {row['item_title']}"):
                st.write(f"**Project Code:** `{row['project_code']}` | **Workflow Stage:** `{row['stage']}`")
                st.write(f"**Submitted By:** `{row['submitted_by']}` | **Submitted At:** `{row['timestamp']}`")
                
                comments = st.text_input("Executive Comments / Directives", key=f"comm_{row['approval_id']}")
                col_app, col_rej = st.columns(2)
                
                with col_app:
                    if st.button(f"✅ Approve #{row['approval_id']}", type="primary", key=f"app_{row['approval_id']}", use_container_width=True):
                        digital_sig = hashlib.sha256(f"{user_name}_{datetime.datetime.now()}".encode()).hexdigest()[:16].upper()
                        execute_sql(
                            "UPDATE executive_approvals SET status = 'Approved', action_by = ?, digital_signature = ?, comments = ? WHERE approval_id = ?",
                            (user_name, digital_sig, comments, row['approval_id'])
                        )
                        log_audit_action(st.session_state["username"], user_role, "Approval Grant", "executive_approvals", f"Approved #{row['approval_id']} (Sig: {digital_sig})")
                        st.success(f"Approved! Digital Signature Hash: {digital_sig}")
                        st.rerun()
                        
                with col_rej:
                    if st.button(f"❌ Reject #{row['approval_id']}", key=f"rej_{row['approval_id']}", use_container_width=True):
                        execute_sql(
                            "UPDATE executive_approvals SET status = 'Rejected', action_by = ?, comments = ? WHERE approval_id = ?",
                            (user_name, comments, row['approval_id'])
                        )
                        log_audit_action(st.session_state["username"], user_role, "Approval Rejection", "executive_approvals", f"Rejected #{row['approval_id']}")
                        st.warning(f"Item #{row['approval_id']} rejected.")
                        st.rerun()


# ==========================================
# WORKSPACE 5: PROJECTS LIFECYCLE PIPELINE
# ==========================================
elif nav_choice == "📁 Projects Lifecycle Pipeline":
    st.header("📁 Projects Lifecycle Pipeline")
    st.caption("Lifecycle tracking, project onboarding, and progress milestone updates.")

    df_p = fetch_df("SELECT * FROM projects")
    st.dataframe(df_p, use_container_width=True, hide_index=True)

    t_add, t_edit = st.tabs(["➕ Onboard New Project", "✏️ Update Project Lifecycle"])

    with t_add:
        with st.form("new_project_form"):
            p_code = st.text_input("Project Code (e.g. PRJ-2026-006)")
            p_name = st.text_input("Project Name")
            p_sc = st.selectbox("Sub-County", ["Nyeri Town", "Mathira East", "Mathira West", "Othaya", "Tetu", "Mukurweini", "Kieni East", "Kieni West"])
            p_dept = st.selectbox("Department", ["Roads & Transport", "Infrastructure & Energy", "Health Services", "Water & Sanitation", "Public Works"])
            p_contractor = st.text_input("Contractor Name", "Unassigned")
            p_engineer = st.text_input("Lead Engineer", user_name)
            p_budget = st.number_input("Allocated Budget (KES)", min_value=0.0, step=500000.0)
            p_stage = st.selectbox("Lifecycle Stage", ["1. Proposal", "2. Technical Review", "3. Budget Approval", "4. Procurement", "5. Construction", "6. Inspection", "7. Handover"])
            p_status = st.selectbox("Initial Status Indicator", ["🔵 Planning", "🟠 In Progress", "🟢 Completed", "🔴 Delayed"])
            p_desc = st.text_area("Scope Description")

            if st.form_submit_button("Register New Project", use_container_width=True):
                if not p_code or not p_name:
                    st.error("Project Code and Project Name are required.")
                else:
                    execute_sql("""
                        INSERT INTO projects (project_code, project_name, sub_county, department, contractor, lead_engineer, budget_allocated, lifecycle_stage, status, description, start_date)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (p_code, p_name, p_sc, p_dept, p_contractor, p_engineer, p_budget, p_stage, p_status, p_desc, datetime.date.today().strftime("%Y-%m-%d")))
                    log_audit_action(st.session_state["username"], user_role, "Project Creation", "projects", f"Created project {p_code}")
                    st.success(f"Project '{p_code}' registered successfully!")
                    st.rerun()

    with t_edit:
        with st.form("edit_project_form"):
            ep_code = st.selectbox("Select Target Project", df_p["project_code"].tolist() if not df_p.empty else ["None"])
            ep_stage = st.selectbox("Update Lifecycle Stage", ["1. Proposal", "2. Technical Review", "3. Budget Approval", "4. Procurement", "5. Construction", "6. Inspection", "7. Handover"])
            ep_progress = st.slider("Completion Rate (%)", 0, 100, 50)
            ep_spend = st.number_input("Actual Cumulative Spend (KES)", min_value=0.0, step=100000.0)
            ep_status = st.selectbox("Status Indicator", ["🔵 Planning", "🟠 In Progress", "🟢 Completed", "🔴 Delayed"])

            if st.form_submit_button("Save Lifecycle Updates", use_container_width=True):
                if ep_code != "None":
                    execute_sql("""
                        UPDATE projects SET lifecycle_stage = ?, percentage_complete = ?, actual_spend = ?, status = ? WHERE project_code = ?
                    """, (ep_stage, ep_progress, ep_spend, ep_status, ep_code))
                    log_audit_action(st.session_state["username"], user_role, "Project Update", "projects", f"Updated {ep_code}")
                    st.success(f"Project '{ep_code}' lifecycle updated!")
                    st.rerun()


# ==========================================
# WORKSPACE 6: DEPARTMENT PERFORMANCE
# ==========================================
elif nav_choice == "📊 Department Performance":
    st.header("📊 Department Performance & Analytics")
    st.caption("Cross-departmental performance metrics, completion rates, and status distributions.")

    df_p = fetch_df("SELECT * FROM projects")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Project Status Breakdown")
        fig_pie = px.pie(df_p, names="status", title="Status Distribution Across Nyeri County", hole=0.45)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_b:
        st.subheader("Budget Allocation by Sub-County")
        fig_sc = px.bar(df_p, x="sub_county", y="budget_allocated", color="status", title="Sub-County Budget Distribution")
        st.plotly_chart(fig_sc, use_container_width=True)

    st.subheader("Departmental Execution Matrix")
    dept_summary = df_p.groupby("department").agg(
        Total_Projects=('project_id', 'count'),
        Total_Budget=('budget_allocated', 'sum'),
        Total_Spend=('actual_spend', 'sum'),
        Avg_Progress=('percentage_complete', 'mean')
    ).reset_index()
    
    dept_summary["Total_Budget"] = dept_summary["Total_Budget"].apply(format_currency_short)
    dept_summary["Total_Spend"] = dept_summary["Total_Spend"].apply(format_currency_short)
    dept_summary["Avg_Progress"] = dept_summary["Avg_Progress"].apply(lambda x: f"{x:.1f}%")
    st.dataframe(dept_summary, use_container_width=True, hide_index=True)


# ==========================================
# WORKSPACE 7: RISK & GOVERNANCE REGISTER
# ==========================================
elif nav_choice == "⚠️ Risk & Governance Register":
    st.header("⚠️ Risk & Governance Register")
    st.caption("Identify, mitigate, and monitor operational and financial infrastructure risks.")

    df_risk = fetch_df("SELECT * FROM risk_register")
    st.dataframe(df_risk, use_container_width=True, hide_index=True)

    with st.expander("➕ Log New Risk Entry"):
        with st.form("add_risk_form"):
            df_p = fetch_df("SELECT project_code FROM projects")
            r_pcode = st.selectbox("Associated Project Code", df_p["project_code"].tolist() if not df_p.empty else ["N/A"])
            r_desc = st.text_area("Risk Description")
            r_sev = st.selectbox("Severity Level", ["Low", "Medium", "High", "Critical"])
            r_mit = st.text_area("Proposed Mitigation Strategy")
            r_owner = st.text_input("Risk Owner", user_name)

            if st.form_submit_button("Register Risk Entry", use_container_width=True):
                execute_sql("""
                    INSERT INTO risk_register (project_code, risk_description, severity, mitigation_strategy, risk_owner)
                    VALUES (?, ?, ?, ?, ?)
                """, (r_pcode, r_desc, r_sev, r_mit, r_owner))
                log_audit_action(st.session_state["username"], user_role, "Risk Log", "risk_register", f"Logged risk for {r_pcode}")
                st.success("Risk entry logged successfully!")
                st.rerun()


# ==========================================
# WORKSPACE 8: SITE INSPECTION MODULE
# ==========================================
elif nav_choice == "🏗️ Site Inspection Module":
    st.header("🏗️ Site Inspection Module")
    st.caption("Field inspection documentation, defect logging, and geo-location recording.")

    df_insp = fetch_df("SELECT * FROM site_inspections")
    st.dataframe(df_insp, use_container_width=True, hide_index=True)

    with st.expander("📝 Record New Site Inspection Report"):
        with st.form("site_inspection_form"):
            df_p = fetch_df("SELECT project_code FROM projects")
            insp_pcode = st.selectbox("Project Code", df_p["project_code"].tolist() if not df_p.empty else ["PRJ-2026-001"])
            insp_date = st.date_input("Inspection Date", datetime.date.today())
            insp_gps = st.text_input("GPS Coordinates (Lat, Long)", "-0.4201, 36.9475")
            insp_weather = st.selectbox("Weather Conditions", ["Sunny / Dry", "Rainy / Muddy", "Cloudy / Overcast"])
            insp_defects = st.text_area("Defects / Structural Observations")
            insp_recs = st.text_area("Recommendations & Directives")
            insp_next = st.date_input("Next Scheduled Follow-up Date", datetime.date.today() + datetime.timedelta(days=14))

            if st.form_submit_button("Submit Field Inspection Report", use_container_width=True):
                execute_sql("""
                    INSERT INTO site_inspections (project_code, engineer_name, inspection_date, gps_coordinates, weather, defects_found, recommendations, next_inspection_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (insp_pcode, user_name, str(insp_date), insp_gps, insp_weather, insp_defects, insp_recs, str(insp_next)))
                log_audit_action(st.session_state["username"], user_role, "Site Inspection", "site_inspections", f"Inspection logged for {insp_pcode}")
                st.success("Inspection report saved!")
                st.rerun()


# ==========================================
# WORKSPACE 9: CLASSIFIED RECORDS & DOCUMENTS
# ==========================================
elif nav_choice == "📄 Classified Records & Documents":
    st.header("📄 Classified Records & Documents Repository")
    st.caption("Document archiving, security level tagging, and record retention management.")

    df_docs = fetch_df("SELECT * FROM classified_documents")
    st.dataframe(df_docs, use_container_width=True, hide_index=True)

    with st.expander("📤 Register / Upload Document Metadata"):
        with st.form("doc_upload_form"):
            df_p = fetch_df("SELECT project_code FROM projects")
            doc_pcode = st.selectbox("Associated Project", df_p["project_code"].tolist() if not df_p.empty else ["PRJ-2026-001"])
            doc_name = st.text_input("Document File Name (e.g., Technical_Audit_v1.pdf)")
            doc_sec = st.selectbox("Security Classification", ["PUBLIC", "INTERNAL", "RESTRICTED", "SECRET"])
            doc_ret = st.number_input("Retention Period (Years)", min_value=1, max_value=30, value=7)

            if st.form_submit_button("Upload Document Metadata", use_container_width=True):
                if not doc_name:
                    st.error("Document Name is required.")
                else:
                    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    execute_sql("""
                        INSERT INTO classified_documents (project_code, doc_name, security_classification, uploaded_by, retention_period_yrs, upload_date)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (doc_pcode, doc_name, doc_sec, user_name, doc_ret, now_str))
                    log_audit_action(st.session_state["username"], user_role, "Document Metadata Upload", "classified_documents", f"Uploaded {doc_name}")
                    st.success(f"Document '{doc_name}' registered under status '{doc_sec}'!")
                    st.rerun()


# ==========================================
# WORKSPACE 10: AI EXECUTIVE BRIEFING
# ==========================================
elif nav_choice == "🤖 AI Executive Briefing":
    st.header("🤖 AI Executive Briefing & Decision Support")
    st.caption("Automated executive synthesis, operational alerts, and project status analysis.")

    df_p = fetch_df("SELECT * FROM projects")
    df_r = fetch_df("SELECT * FROM risk_register")
    df_app = fetch_df("SELECT * FROM executive_approvals WHERE status = 'Pending'")

    delayed_projects = df_p[df_p["status"] == "🔴 Delayed"]
    completed_projects = df_p[df_p["status"] == "🟢 Completed"]

    st.markdown(f"""
    > **Executive Briefing Summary:**
    > * **Active Projects Managed:** Total `{len(df_p)}` infrastructure projects across Nyeri County.
    > * **Completed Projects:** `{len(completed_projects)}` project(s) delivered to handover stage.
    > * **Projects Delayed:** `{len(delayed_projects)}` project(s) requiring executive attention.
    > * **Pending Approvals:** `{len(df_app)}` item(s) awaiting signature.
    > * **Total Capital Commitment:** KES `{df_p['budget_allocated'].sum():,.2f}`
    """)

    if not delayed_projects.empty:
        st.warning(f"⚠️ **Attention Required:** {len(delayed_projects)} project(s) are currently marked as delayed: **{', '.join(delayed_projects['project_name'].tolist())}**.")
    else:
        st.success("✅ Operational performance on schedule across active projects.")


# ==========================================
# WORKSPACE 11: DISASTER RECOVERY & AUDIT LOGS
# ==========================================
elif nav_choice == "⚙️ Disaster Recovery & Audit Logs":
    st.header("⚙️ Disaster Recovery & System Audit Logs")
    st.caption("Immutable system security audit trail and database disaster recovery tools.")

    t_audit, t_backup = st.tabs(["📜 Security Audit Logs", "💾 Disaster Recovery Snapshot"])

    with t_audit:
        st.subheader("System Access & Action Log")
        df_audit = fetch_df("SELECT * FROM audit_logs ORDER BY log_id DESC")
        st.dataframe(df_audit, use_container_width=True, hide_index=True)

        csv_logs = df_audit.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Audit Trail Dataset (CSV)",
            data=csv_logs,
            file_name=f"Nyeri_MIS_AuditTrail_{datetime.date.today()}.csv",
            mime="text/csv"
        )

    with t_backup:
        st.subheader("Database Snapshot & Archival")
        st.write("Generate a full SQLite database snapshot for archival and disaster recovery operations.")

        try:
            with open("nyeri_enterprise_mis.db", "rb") as fp:
                db_bytes = fp.read()
            st.download_button(
                label="💾 Download Full Enterprise Database Backup (.db)",
                data=db_bytes,
                file_name=f"nyeri_enterprise_mis_backup_{datetime.date.today()}.db",
                mime="application/x-sqlite3"
            )
        except Exception as e:
            st.error(f"Error accessing database snapshot: {e}")
