# ==========================================
# 5. LOGIN / GATEWAY INTERFACE
# ==========================================
if not st.session_state["authenticated"] and not st.session_state["is_public"]:

    # ==============================
    # ACCESSIBILITY
    # ==============================
    top_left, top_right = st.columns([8, 2])

    with top_right:
        with st.expander("♿ Accessibility"):
            high_contrast_option = st.checkbox(
                "High Contrast Mode",
                value=st.session_state["high_contrast"]
            )

            large_font_option = st.checkbox(
                "Larger Font Option",
                value=st.session_state["large_font"]
            )

            if st.button("Apply Settings", use_container_width=True):

                st.session_state["high_contrast"] = high_contrast_option
                st.session_state["large_font"] = large_font_option

                st.rerun()

    # ==============================
    # PAGE HEADER
    # ==============================
    st.markdown("<br>", unsafe_allow_html=True)

    header_left, header_center, header_right = st.columns([1, 2, 1])

    with header_center:

        if os.path.exists(SEAL_IMAGE):

            st.image(
                SEAL_IMAGE,
                width=115
            )

        else:

            st.markdown(
                """
                <div style="
                    text-align:center;
                    font-size:65px;
                    margin-bottom:10px;
                ">
                    🏛️
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown(
        """
        <div style="
            text-align:center;
            margin-top:5px;
        ">

            <div style="
                font-size:25px;
                font-weight:800;
                color:#0A4D20;
                letter-spacing:0.4px;
            ">
                COUNTY GOVERNMENT OF NYERI
            </div>

            <div style="
                font-size:14px;
                color:#4B5563;
                margin-top:5px;
            ">
                Department of Roads, Public Works & Transport
            </div>

            <div style="
                font-size:27px;
                font-weight:900;
                color:#0A4D20;
                letter-spacing:1.2px;
                margin-top:18px;
            ">
                NYERI UJENZI MIS
            </div>

            <div style="
                font-size:13px;
                color:#6B7280;
                margin-top:5px;
            ">
                Infrastructure, Projects & Public Works
                Management Information System
            </div>

            <div style="
                font-size:11px;
                color:#9CA3AF;
                margin-top:8px;
                margin-bottom:22px;
            ">
                Secure Enterprise Government Information System
                • Version 2.0.0
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    # ==============================
    # LOGIN CARD
    # ==============================
    login_left, login_center, login_right = st.columns(
        [1.1, 1.8, 1.1]
    )

    with login_center:

        st.markdown(
            """
            <div style="
                background:#FFFFFF;
                border:1px solid #E5E7EB;
                border-radius:14px 14px 0 0;
                padding:22px 25px 15px 25px;
                box-shadow:0 6px 20px rgba(0,0,0,0.06);
                text-align:center;
            ">

                <div style="
                    font-size:22px;
                    font-weight:800;
                    color:#111827;
                ">
                    Staff Sign In
                </div>

                <div style="
                    font-size:13px;
                    color:#6B7280;
                    margin-top:5px;
                ">
                    Access your authorized county workspace
                </div>

            </div>
            """,
            unsafe_allow_html=True
        )

        # ==============================
        # TABS
        # ==============================
        t_login, t_forgot, t_public = st.tabs(
            [
                "🔒 Sign In",
                "🔑 Password",
                "🌐 Citizen Portal"
            ]
        )

        # ==================================================
        # STAFF LOGIN
        # ==================================================
        with t_login:

            st.markdown(
                """
                <div style="
                    background:#F0FDF4;
                    border:1px solid #BBF7D0;
                    border-left:4px solid #16A34A;
                    padding:11px 13px;
                    border-radius:6px;
                    margin:12px 0 18px 0;
                    font-size:12px;
                    color:#166534;
                ">
                    🔒 <strong>Secure County Government System</strong><br>
                    Your account activity is protected and audited.
                </div>
                """,
                unsafe_allow_html=True
            )

            # ==============================
            # MFA LOGIN
            # ==============================
            if st.session_state["mfa_pending"]:

                st.info(
                    "🔐 Multi-Factor Authentication Required"
                )

                st.markdown(
                    f"""
                    <div style="
                        text-align:center;
                        background:#F9FAFB;
                        padding:12px;
                        border-radius:8px;
                        margin-bottom:15px;
                        font-size:13px;
                    ">
                        Authentication required for<br>
                        <strong>
                        {st.session_state["mfa_user_data"]["full_name"]}
                        </strong>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                with st.form("mfa_form"):

                    otp = st.text_input(
                        "One-Time Passcode",
                        type="password",
                        placeholder="Enter authentication code"
                    )

                    verify_button = st.form_submit_button(
                        "Verify & Complete Sign In",
                        use_container_width=True
                    )

                    if verify_button:

                        # DEMO MFA CODE
                        if otp == "1234":

                            u_data = st.session_state[
                                "mfa_user_data"
                            ]

                            st.session_state[
                                "authenticated"
                            ] = True

                            st.session_state[
                                "username"
                            ] = u_data["username"]

                            st.session_state[
                                "role"
                            ] = u_data["role"]

                            st.session_state[
                                "full_name"
                            ] = u_data["full_name"]

                            st.session_state[
                                "department"
                            ] = u_data["department"]

                            st.session_state[
                                "employee_number"
                            ] = u_data["employee_number"]

                            st.session_state[
                                "last_login"
                            ] = u_data["last_login"]

                            st.session_state[
                                "last_login_ip"
                            ] = u_data["last_login_ip"]

                            st.session_state[
                                "mfa_pending"
                            ] = False

                            log_audit_action(
                                u_data["username"],
                                u_data["role"],
                                "MFA Login",
                                "System",
                                "MFA verified successfully"
                            )

                            st.rerun()

                        else:

                            st.error(
                                "Invalid authentication code."
                            )

            # ==============================
            # NORMAL LOGIN
            # ==============================
            else:

                with st.form("clean_login_form"):

                    u_input = st.text_input(
                        "Username or Employee Number",
                        placeholder="e.g. ENG_Mwangi or EMP-1004"
                    )

                    p_input = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Enter your password"
                    )

                    st.markdown(
                        """
                        <div style="
                            text-align:center;
                            font-size:11px;
                            color:#6B7280;
                            margin:8px 0 12px 0;
                        ">
                            🔒 Secure access • 🔐 Activity audited
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    submitted = st.form_submit_button(
                        "🔐 Sign In Securely",
                        use_container_width=True,
                        type="primary"
                    )

                    if submitted:

                        if not u_input or not p_input:

                            st.warning(
                                "Please enter both your username and password."
                            )

                        else:

                            login_key = u_input.strip().lower()

                            attempts = st.session_state[
                                "failed_attempts"
                            ].get(
                                login_key,
                                0
                            )

                            if attempts >= 3:

                                st.error(
                                    "Account temporarily locked due to repeated failed login attempts. "
                                    "Contact the ICT Service Desk."
                                )

                            else:

                                user_data = verify_login(
                                    u_input,
                                    p_input
                                )

                                if user_data:

                                    st.session_state[
                                        "failed_attempts"
                                    ][login_key] = 0

                                    # MFA REQUIRED FOR SENIOR ROLES
                                    if user_data["role"] in [
                                        "CECM",
                                        "Chief Officer",
                                        "Admin"
                                    ]:

                                        st.session_state[
                                            "mfa_pending"
                                        ] = True

                                        st.session_state[
                                            "mfa_user_data"
                                        ] = user_data

                                        st.rerun()

                                    # NORMAL USER LOGIN
                                    else:

                                        st.session_state[
                                            "authenticated"
                                        ] = True

                                        st.session_state[
                                            "username"
                                        ] = user_data["username"]

                                        st.session_state[
                                            "role"
                                        ] = user_data["role"]

                                        st.session_state[
                                            "full_name"
                                        ] = user_data["full_name"]

                                        st.session_state[
                                            "department"
                                        ] = user_data["department"]

                                        st.session_state[
                                            "employee_number"
                                        ] = user_data["employee_number"]

                                        st.session_state[
                                            "last_login"
                                        ] = user_data["last_login"]

                                        st.session_state[
                                            "last_login_ip"
                                        ] = user_data["last_login_ip"]

                                        log_audit_action(
                                            user_data["username"],
                                            user_data["role"],
                                            "Login",
                                            "System",
                                            "Authenticated successfully"
                                        )

                                        st.rerun()

                                else:

                                    st.session_state[
                                        "failed_attempts"
                                    ][login_key] = attempts + 1

                                    remaining = 3 - (
                                        attempts + 1
                                    )

                                    if remaining > 0:

                                        st.error(
                                            f"Invalid credentials. "
                                            f"{remaining} attempts remaining."
                                        )

                                    else:

                                        st.error(
                                            "Account temporarily locked."
                                        )

            st.markdown(
                """
                <div style="
                    text-align:center;
                    font-size:11px;
                    color:#6B7280;
                    margin-top:18px;
                    padding-top:12px;
                    border-top:1px solid #E5E7EB;
                ">
                    ⏱️ Session timeout: 15 minutes of inactivity
                    <br>
                    🔒 All authorized activities are recorded in the audit trail
                </div>
                """,
                unsafe_allow_html=True
            )

        # ==================================================
        # PASSWORD RESET
        # ==================================================
        with t_forgot:

            st.subheader(
                "🔑 Password Reset"
            )

            st.caption(
                "Verify your official identity to reset your account password."
            )

            with st.form("forgot_password_form"):

                fp_username = st.text_input(
                    "Username"
                )

                fp_emp_num = st.text_input(
                    "Employee Number",
                    placeholder="e.g. EMP-1004"
                )

                fp_new_pw = st.text_input(
                    "New Password",
                    type="password"
                )

                fp_confirm_pw = st.text_input(
                    "Confirm New Password",
                    type="password"
                )

                fp_submit = st.form_submit_button(
                    "Reset Password",
                    use_container_width=True
                )

                if fp_submit:

                    if not fp_username or not fp_emp_num or not fp_new_pw:

                        st.error(
                            "Please fill in all required fields."
                        )

                    elif fp_new_pw != fp_confirm_pw:

                        st.error(
                            "New passwords do not match."
                        )

                    else:

                        conn = sqlite3.connect(
                            "nyeri_enterprise_mis.db"
                        )

                        cursor = conn.cursor()

                        cursor.execute(
                            """
                            SELECT user_id, full_name
                            FROM users
                            WHERE LOWER(username) = LOWER(?)
                            AND LOWER(employee_number) = LOWER(?)
                            """,
                            (
                                fp_username.strip(),
                                fp_emp_num.strip()
                            )
                        )

                        user_rec = cursor.fetchone()

                        if user_rec:

                            new_hash = hash_password(
                                fp_new_pw
                            )

                            cursor.execute(
                                """
                                UPDATE users
                                SET password_hash = ?
                                WHERE user_id = ?
                                """,
                                (
                                    new_hash,
                                    user_rec[0]
                                )
                            )

                            conn.commit()
                            conn.close()

                            log_audit_action(
                                fp_username,
                                "Self-Service",
                                "Password Reset",
                                "Users",
                                f"Password reset for {user_rec[1]}"
                            )

                            st.success(
                                "Password successfully reset. "
                                "You can now sign in."
                            )

                        else:

                            conn.close()

                            st.error(
                                "Invalid Username and Employee Number combination."
                            )

        # ==================================================
        # CITIZEN PORTAL
        # ==================================================
        with t_public:

            st.subheader(
                "🌐 Citizen Open Data Portal"
            )

            st.write(
                "Access public infrastructure information, "
                "project progress and transparency records."
            )

            st.markdown(
                """
                <div style="
                    background:#F9FAFB;
                    border:1px solid #E5E7EB;
                    border-radius:8px;
                    padding:14px;
                    margin:15px 0;
                    font-size:13px;
                    color:#4B5563;
                ">
                    View selected public county projects, progress information,
                    and transparency records without creating an account.
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "Enter Citizen Portal ➜",
                use_container_width=True,
                type="primary"
            ):

                st.session_state[
                    "is_public"
                ] = True

                st.rerun()

        # ==============================
        # FOOTER
        # ==============================
        st.markdown(
            """
            <div style="
                text-align:center;
                margin-top:25px;
                padding-top:15px;
                border-top:1px solid #E5E7EB;
                font-size:11px;
                color:#6B7280;
                line-height:1.6;
            ">

                <strong>County Government of Nyeri</strong>
                <br>

                NYERI UJENZI MIS • Version 2.0.0
                <br>

                Authorized access only • All activities are audited

            </div>
            """,
            unsafe_allow_html=True
        )

    st.stop()
