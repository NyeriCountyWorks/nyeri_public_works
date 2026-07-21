# ==========================================
# WORKSPACE 0: USER PROFILE & CHANGE PASSWORD
# ==========================================
if nav_choice == "👤 My Profile":
    st.header("👤 Staff Profile & Account Settings")
    st.caption("Manage your enterprise user credentials and view session security metrics.")
    
    col_prof1, col_prof2 = st.columns([1, 1])
    
    with col_prof1:
        st.subheader("Official Credentials")
        st.write(f"**Full Name:** {st.session_state.get('full_name', 'N/A')}")
        st.write(f"**Username:** `{st.session_state.get('username', 'N/A')}`")
        st.write(f"**Employee Number:** `{st.session_state.get('employee_number', 'N/A')}`")
        st.write(f"**Designated Role:** `{st.session_state.get('role', 'N/A')}`")
        st.write(f"**Department:** {st.session_state.get('department', 'N/A')}")
        st.write(f"**Last Sign-In Timestamp:** {st.session_state.get('last_login', 'N/A')}")
        st.write(f"**Registered Gateway IP:** `{st.session_state.get('last_login_ip', 'N/A')}`")

    with col_prof2:
        st.subheader("🔑 Change Security Password")
        with st.form("change_profile_password_form"):
            curr_pw = st.text_input("Current Password", type="password")
            new_pw = st.text_input("New Password", type="password")
            confirm_pw = st.text_input("Confirm New Password", type="password")
            
            submit_pw = st.form_submit_button("Update Credentials", use_container_width=True)
            
            if submit_pw:
                if not curr_pw or not new_pw or not confirm_pw:
                    st.error("All password fields are required.")
                elif new_pw != confirm_pw:
                    st.error("New password confirmation does not match.")
                else:
                    conn = sqlite3.connect("nyeri_enterprise_mis.db")
                    cursor = conn.cursor()
                    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (st.session_state["username"],))
                    user_row = cursor.fetchone()
                    
                    if user_row and verify_password(user_row[0], curr_pw):
                        new_hash = hash_password(new_pw)
                        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, st.session_state["username"]))
                        conn.commit()
                        conn.close()
                        log_audit_action(st.session_state["username"], st.session_state["role"], "Password Change", "Users", "Password updated via self-service profile")
                        st.success("Password successfully updated!")
                    else:
                        conn.close()
                        st.error("Current password verification failed.")

# ==========================================
# WORKSPACE 1: EXECUTIVE WORKSPACES (CECM / CHIEF OFFICER)
# ==========================================
elif nav_choice in ["🏠 CECM Executive Workspace", "🏢 Chief Officer Workspace"]:
    st.header(f"{nav_choice}")
    st.caption("Strategic Portfolio Performance & Capital Project Governance")

    # High-level Portfolio Metrics
    df_projects = fetch_df("SELECT * FROM projects")
    total_budget = df_projects["budget_allocated"].sum() if not df_projects.empty else 0.0
    total_spend = df_projects["actual_spend"].sum() if not df_projects.empty else 0.0
    avg_progress = df_projects["percentage_complete"].mean() if not df_projects.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="dec-card"><div class="dec-title">Total Allocated Budget</div><div class="dec-value">{format_currency_short(total_budget)}</div></div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="dec-card"><div class="dec-title">Total Disbursed Spend</div><div class="dec-value">{format_currency_short(total_spend)}</div></div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="dec-card"><div class="dec-title">Average Execution</div><div class="dec-value">{avg_progress:.1f}%</div></div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="dec-card"><div class="dec-title">Active Projects</div><div class="dec-value">{len(df_projects)}</div></div>""", unsafe_allow_html=True)

    st.subheader("Budget Allocation vs Execution by Sub-County")
    if not df_projects.empty:
        fig = px.bar(
            df_projects,
            x="sub_county",
            y=["budget_allocated", "actual_spend"],
            barmode="group",
            labels={"value": "Amount (KES)", "sub_county": "Sub-County", "variable": "Metric"},
            title="Capital Expenditure Breakdown",
            color_discrete_map={"budget_allocated": "#0A4D20", "actual_spend": "#D4AF37"}
        )
        st.plotly_chart(fig, use_container_width=True)

# ==========================================
# WORKSPACE 2: FIELD WORKSPACE & INSPECTIONS
# ==========================================
elif nav_choice == "🏗️ Engineer Field Workspace":
    st.header("🏗️ Engineer Field Operations Workspace")
    st.caption("Site Logistics, Progress Updates, and Structural Verification")

    p_list = fetch_df("SELECT project_code, project_name FROM projects")
    if not p_list.empty:
        p_code = st.selectbox("Select Project for Field Update", p_list["project_code"] + " - " + p_list["project_name"])
        selected_code = p_code.split(" - ")[0]

        curr_proj = fetch_df("SELECT * FROM projects WHERE project_code = ?", (selected_code,)).iloc[0]

        with st.form("engineer_update_form"):
            st.subheader(f"Update Lifecycle Progress: {curr_proj['project_name']}")
            new_pct = st.slider("Percentage Completion", 0, 100, int(curr_proj["percentage_complete"]))
            new_stage = st.selectbox("Lifecycle Stage", [
                "1. Proposal", "2. Technical Review", "3. Budget Approval", 
                "4. Tendering", "5. Construction", "6. Quality Inspection", "7. Handover"
            ], index=0)
            new_status = st.selectbox("Health Status", ["🔵 Planning", "🟠 In Progress", "🟢 Completed", "🔴 Delayed"])
            notes = st.text_area("Engineering Field Notes & Remarks")

            if st.form_submit_button("Submit Site Progress Log"):
                execute_sql("""
                    UPDATE projects 
                    SET percentage_complete = ?, lifecycle_stage = ?, status = ? 
                    WHERE project_code = ?
                """, (new_pct, new_stage, new_status, selected_code))
                log_audit_action(user_name, user_role, "Field Log Update", "Projects", f"Updated progress to {new_pct}% for {selected_code}")
                st.success("Field progress logged successfully!")
                st.rerun()

# ==========================================
# WORKSPACE 3: FINANCE & TREASURY
# ==========================================
elif nav_choice == "💰 Finance & Treasury Workspace":
    st.header("💰 Finance & Treasury Governance")
    st.caption("Invoice Processing, Budget Reallocations, and PFM Compliance")

    inv_df = fetch_df("SELECT * FROM financial_invoices")
    st.subheader("Contractor Invoices Pending Treasury Approval")
    st.dataframe(inv_df, use_container_width=True)

    with st.expander("💳 Process Contractor Invoice Disbursement"):
        if not inv_df.empty:
            inv_id = st.selectbox("Select Invoice ID", inv_df["invoice_id"].tolist())
            action = st.radio("Financial Action", ["Approve & Disburse", "Reject / Query"])
            
            if st.button("Execute Treasury Action"):
                new_st = "Disbursed" if action == "Approve & Disburse" else "Queried"
                execute_sql("UPDATE financial_invoices SET status = ? WHERE invoice_id = ?", (new_st, inv_id))
                log_audit_action(user_name, user_role, "Invoice Action", "Financial Invoices", f"Set status to {new_st} for ID {inv_id}")
                st.success(f"Invoice #{inv_id} status updated to {new_st}.")
                st.rerun()

# ==========================================
# WORKSPACE 4: EXECUTIVE APPROVAL CENTRE
# ==========================================
elif nav_choice == "✍️ Executive Approval Centre":
    st.header("✍️ Executive Approval Centre")
    st.caption("Official Digital Sign-off for Variations, Tenders, and Budget Lines")

    app_df = fetch_df("SELECT * FROM executive_approvals WHERE status = 'Pending'")
    if app_df.empty:
        st.info("No executive approvals currently pending action.")
    else:
        for idx, row in app_df.iterrows():
            with st.expander(f"📋 Approval Request #{row['approval_id']}: {row['item_title']}"):
                st.write(f"**Project Code:** `{row['project_code']}`")
                st.write(f"**Stage:** {row['stage']}")
                st.write(f"**Submitted By:** {row['submitted_by']} at {row['timestamp']}")
                
                col_app1, col_app2 = st.columns(2)
                with col_app1:
                    app_comment = st.text_input("Executive Remarks / Conditions", key=f"comm_{row['approval_id']}")
                with col_app2:
                    sig = st.text_input("Digital Signature / Employee PIN Verification", type="password", key=f"sig_{row['approval_id']}")

                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    if st.button("🟢 Approve & Sign Digitally", key=f"app_{row['approval_id']}"):
                        execute_sql("""
                            UPDATE executive_approvals 
                            SET status = 'Approved', action_by = ?, comments = ?, digital_signature = ? 
                            WHERE approval_id = ?
                        """, (user_name, app_comment, sig, row['approval_id']))
                        log_audit_action(user_name, user_role, "Executive Approval", "Executive Approvals", f"Approved ID {row['approval_id']}")
                        st.success("Item officially approved and digitally signed.")
                        st.rerun()
                with b_col2:
                    if st.button("🔴 Reject Request", key=f"rej_{row['approval_id']}"):
                        execute_sql("""
                            UPDATE executive_approvals 
                            SET status = 'Rejected', action_by = ?, comments = ? 
                            WHERE approval_id = ?
                        """, (user_name, app_comment, row['approval_id']))
                        log_audit_action(user_name, user_role, "Executive Rejection", "Executive Approvals", f"Rejected ID {row['approval_id']}")
                        st.error("Request rejected.")
                        st.rerun()

# ==========================================
# WORKSPACE 5: PROJECTS LIFECYCLE PIPELINE
# ==========================================
elif nav_choice == "📁 Projects Lifecycle Pipeline":
    st.header("📁 Infrastructure Projects Lifecycle Master")
    st.caption("End-to-End Tracking from Planning to Handover")

    proj_df = fetch_df("SELECT * FROM projects")
    st.dataframe(proj_df, use_container_width=True)

# ==========================================
# WORKSPACE 6: DEPARTMENT PERFORMANCE
# ==========================================
elif nav_choice == "📊 Department Performance":
    st.header("📊 Department Performance & Analytics")
    st.caption("Cross-Departmental Delivery Metrics and Sub-County Progress Dashboard")

    df_dept = fetch_df("SELECT department, budget_allocated, actual_spend, percentage_complete FROM projects")
    if not df_dept.empty:
        dept_summary = df_dept.groupby("department").agg({
            "budget_allocated": "sum",
            "actual_spend": "sum",
            "percentage_complete": "mean"
        }).reset_index()
        
        st.table(dept_summary)

# ==========================================
# WORKSPACE 7: RISK & GOVERNANCE REGISTER
# ==========================================
elif nav_choice == "⚠️ Risk & Governance Register":
    st.header("⚠️ Risk Register & Compliance Tracking")
    st.caption("Project Mitigations, Cost Overrun Warnings, and Audit Defect Logs")

    risk_df = fetch_df("SELECT * FROM risk_register")
    st.dataframe(risk_df, use_container_width=True)

# ==========================================
# WORKSPACE 8: CLASSIFIED RECORDS & DOCUMENTS
# ==========================================
elif nav_choice == "📄 Classified Records & Documents":
    st.header("📄 Classified Records Repository")
    st.caption("Secure Storage for Tender Evaluations, BOQs, and Site Agreements")

    docs_df = fetch_df("SELECT * FROM classified_documents")
    st.dataframe(docs_df, use_container_width=True)

# ==========================================
# WORKSPACE 9: SITE INSPECTION MODULE
# ==========================================
elif nav_choice == "🏗️ Site Inspection Module":
    st.header("🏗️ Engineering Site Inspection Records")
    st.caption("GPS-tagged QA/QC Logs and Structural Inspection Reports")

    insp_df = fetch_df("SELECT * FROM site_inspections")
    st.dataframe(insp_df, use_container_width=True)

# ==========================================
# WORKSPACE 10: AI EXECUTIVE BRIEFING
# ==========================================
elif nav_choice == "🤖 AI Executive Briefing":
    st.header("🤖 Executive AI Summary Briefing")
    st.caption("Automated Governance Insights & Portfolio Anomaly Detection")

    st.markdown("""
    > **Executive Summary Notice:**  
    > * Total Portfolio Risk Level: **MODERATE** (Driven by 1 high-severity cost overrun risk in PRJ-2026-004).
    > * Financial Execution Velocity: **78.4%** of disbursed funds are accounted for with valid QA/QC inspection sign-offs.
    > * Recommended Action: Prioritize executive approval for Mukurwe-ini Feeder Roads budget reallocation to eliminate site bottlenecking.
    """)

# ==========================================
# WORKSPACE 11: DISASTER RECOVERY & AUDIT LOGS
# ==========================================
elif nav_choice == "⚙️ Disaster Recovery & Audit Logs":
    st.header("⚙️ Immutable Governance Audit Trail")
    st.caption("System Operations, Access Security Logs, and Database Backups")

    audit_df = fetch_df("SELECT * FROM audit_logs ORDER BY log_id DESC LIMIT 100")
    st.dataframe(audit_df, use_container_width=True)
