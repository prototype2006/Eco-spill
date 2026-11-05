import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh

from core.data_interface import get_latest_reading
from modules.incident_history import show_incident_history

from modules.vessel_management import (
    register_vessel,
    list_company_vessels,
)
from backend.authorization import AuthorizationError
# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="EcoSpillGuard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================================================
# FIREBASE CONFIGURATION
# =========================================================

try:
    API_KEY = st.secrets["firebase"]["api_key"]
except (KeyError, FileNotFoundError):
    st.error(
        "Firebase configuration is missing. "
        "Check .streamlit/secrets.toml."
    )
    st.stop()

FIREBASE_SIGN_UP_URL = (
    "https://identitytoolkit.googleapis.com/v1/"
    "accounts:signUp"
    f"?key={API_KEY}"
)

FIREBASE_SIGN_IN_URL = (
    "https://identitytoolkit.googleapis.com/v1/"
    "accounts:signInWithPassword"
    f"?key={API_KEY}"
)


# =========================================================
# CUSTOM STYLING
# =========================================================

st.markdown(
    """
    <style>
    @import url(
      'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@400;500;600;700;800&display=swap'
    );

    .stApp {
        background: #071824;
        color: #f2f8fc;
        font-family: 'DM Sans', sans-serif;
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    #MainMenu, footer {
        visibility: hidden;
    }

    .block-container {
        max-width: 1200px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    .brand {
        font-family: 'Manrope', sans-serif;
        font-size: 23px;
        font-weight: 800;
        color: #f2fbff;
        letter-spacing: -0.7px;
    }

    .brand span, .headline span {
        color: #43d8c2;
    }

    .eyebrow {
        color: #47dcca;
        font-size: 11px;
        letter-spacing: 3px;
        font-weight: 700;
        margin-bottom: 18px;
    }

    .headline {
        font-family: 'Manrope', sans-serif;
        font-size: clamp(36px, 4.5vw, 58px);
        font-weight: 800;
        color: #f2f8fc;
        line-height: 1.12;
        letter-spacing: -2px;
        margin-bottom: 20px;
    }

    .description {
        color: #9eb4c4;
        font-size: 15px;
        line-height: 1.8;
        max-width: 460px;
    }

    .feature {
        color: #c5d7e1;
        font-size: 13px;
        padding: 10px 0;
    }

    .feature span {
        color: #47dcca;
        margin-right: 10px;
    }

    .login-heading {
        color: #f2f8fc;
        font-family: 'Manrope', sans-serif;
        font-size: 29px;
        font-weight: 800;
    }

    .login-subtitle {
        color: #9eb4c4;
        font-size: 13px;
        margin-bottom: 24px;
    }

    div[data-testid="stTextInput"] label {
        color: #c8d8e2;
    }

    div[data-testid="stTextInput"] input {
        background: #102838;
        color: #f2f8fc;
        border: 1px solid #284454;
        border-radius: 9px;
        min-height: 45px;
    }

    div[data-testid="stTextInput"] input:focus {
        border-color: #43d8c2;
        box-shadow: 0 0 0 1px #43d8c2;
    }

    div[data-testid="stFormSubmitButton"] button,
    div[data-testid="stButton"] button[kind="primary"] {
        background: #36cbb6 !important;
        color: #06232b !important;
        border: none !important;
        border-radius: 9px;
        min-height: 44px;
        font-weight: 700;
    }

    div[data-testid="stFormSubmitButton"] button:hover,
    div[data-testid="stButton"] button[kind="primary"]:hover {
        background: #66e6d3 !important;
        color: #06232b !important;
    }

    div[data-testid="stMetric"] {
        background: #102838;
        border: 1px solid #244352;
        padding: 18px;
        border-radius: 12px;
    }

    div[data-testid="stMetricLabel"] {
        color: #a9c0cd;
    }

    .security-note {
        background: #102838;
        border: 1px solid #244352;
        padding: 12px 14px;
        border-radius: 9px;
        color: #a9c0cd;
        font-size: 11px;
        line-height: 1.6;
        margin-top: 18px;
    }

    .footer-note {
        color: #647e8d;
        font-size: 11px;
        margin-top: 35px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# FIREBASE AUTHENTICATION
# =========================================================

def firebase_sign_in(email: str, password: str):
    """Authenticate a user through Firebase email/password."""
    try:
        response = requests.post(
            FIREBASE_SIGN_IN_URL,
            json={
                "email": email.strip(),
                "password": password,
                "returnSecureToken": True,
            },
            timeout=15,
        )

        try:
            result = response.json()
        except ValueError:
            return None, "Firebase returned an invalid response."

        if response.ok:
            return result, None

        error_code = result.get("error", {}).get("message", "")

        messages = {
            "INVALID_LOGIN_CREDENTIALS": "Incorrect email or password.",
            "EMAIL_NOT_FOUND": "No account was found for that email.",
            "INVALID_PASSWORD": "Incorrect email or password.",
            "USER_DISABLED": "This account has been disabled.",
            "INVALID_EMAIL": "Enter a valid email address.",
            "TOO_MANY_ATTEMPTS_TRY_LATER":
                "Too many attempts. Please wait and try again.",
            "API_KEY_INVALID":
                "The Firebase API key is invalid. Check your configuration.",
            "OPERATION_NOT_ALLOWED":
                "Email/password authentication is not enabled in Firebase.",
        }

        return None, messages.get(
            error_code,
            "Sign-in failed. Check your details and Firebase settings.",
        )

    except requests.RequestException:
        return None, (
            "Could not reach Firebase. Check your internet connection."
        )


def firebase_create_account(email: str, password: str):
    """Create a Firebase email/password account."""
    try:
        response = requests.post(
            FIREBASE_SIGN_UP_URL,
            json={
                "email": email.strip(),
                "password": password,
                "returnSecureToken": True,
            },
            timeout=15,
        )

        try:
            result = response.json()
        except ValueError:
            return None, "Firebase returned an invalid response."

        if response.ok:
            return result, None

        error_code = result.get("error", {}).get("message", "")
        messages = {
            "EMAIL_EXISTS": "An account already exists for this email. Sign in instead.",
            "INVALID_EMAIL": "Enter a valid email address.",
            "WEAK_PASSWORD": "Choose a stronger password with at least 6 characters.",
            "OPERATION_NOT_ALLOWED": "Email/password authentication is not enabled in Firebase.",
            "API_KEY_INVALID": "The Firebase API key is invalid. Check your configuration.",
            "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many attempts. Please wait and try again.",
        }
        return None, messages.get(
            error_code,
            "Account creation failed. Check the details and Firebase settings.",
        )
    except requests.RequestException:
        return None, "Could not reach Firebase. Check your internet connection."


# =========================================================
# SESSION STATE
# =========================================================

if "user" not in st.session_state:
    st.session_state.user = None

if "firebase_token" not in st.session_state:
    st.session_state.firebase_token = None


# =========================================================
# AUTHENTICATED APPLICATION
# =========================================================

if st.session_state.user:
    # Sidebar
    with st.sidebar:
        st.markdown("## 🌊 EcoSpillGuard")
        st.caption("Marine Monitoring")
        st.write("Signed in as")
        st.caption(st.session_state.user["email"])
        st.divider()

        selected_page = st.radio(
            "Navigation",
            ["Dashboard", "Incident History", "Vessel Management"],
            key="main_navigation",
        )
        st.divider()

        if st.button("Sign out", use_container_width=True):
            st.session_state.user = None
            st.session_state.firebase_token = None
            st.rerun()

        st.divider()
        st.caption("Development preview")

    if selected_page == "Incident History":
        show_incident_history()

    elif selected_page == "Vessel Management":
        st.title("Vessel Management")
        st.caption("Register and manage vessels for your company.")

        token = st.session_state.get("firebase_token")

        if not token:
            st.error("Please sign in again to manage vessels.")
            st.stop()

        st.subheader("Register a vessel")

        with st.form("register_vessel_form"):
            vessel_name = st.text_input(
                "Vessel name *",
                placeholder="e.g. Ocean Explorer",
            )
            imo_number = st.text_input(
                "IMO number",
                placeholder="Optional",
            )
            call_sign = st.text_input(
                "Call sign",
                placeholder="Optional",
            )
            vessel_type = st.selectbox(
                "Vessel type",
                [
                    "Not specified",
                    "Cargo",
                    "Tanker",
                    "Container ship",
                    "Passenger",
                    "Fishing",
                    "Research",
                    "Other",
                ],
            )
            flag_state = st.text_input(
                "Flag state",
                placeholder="e.g. India",
            )
            device_id = st.text_input(
                "Sensor device ID",
                placeholder="Optional, if a device is assigned",
            )

            submitted = st.form_submit_button(
                "Register vessel",
                type="primary",
            )

        if submitted:
            if not vessel_name.strip():
                st.error("Vessel name is required.")
            else:
                try:
                    vessel = register_vessel(
                        id_token=token,
                        name=vessel_name.strip(),
                        imo_number=imo_number.strip() or None,
                        call_sign=call_sign.strip() or None,
                        vessel_type=(
                            None
                            if vessel_type == "Not specified"
                            else vessel_type
                        ),
                        flag_state=flag_state.strip() or None,
                        device_id=device_id.strip() or None,
                    )

                    st.success(
                        f"Vessel registered: {vessel['vessel_id']}"
                    )
                    st.rerun()

                
                except AuthorizationError as exc:
                    import logging
                    logging.exception("Vessel registration authorization failed")
                    st.error(f"Authorization error: {exc}")

                except (ValueError, RuntimeError) as exc:
                    import logging
                    logging.exception("Vessel registration failed")
                    st.error(f"Registration error: {type(exc).__name__}: {exc}")

                except Exception as exc:
                    import logging
                    logging.exception("Vessel registration failed")
                    st.error(f"Registration error: {type(exc).__name__}: {exc}")


        st.divider()
        st.subheader("Registered vessels")

        try:
            vessels = list_company_vessels(id_token=token)
        except AuthorizationError as exc:
            import logging
            logging.exception("Vessel list authorization failed")
            st.error(f"Authorization error loading vessels: {exc}")

        except Exception as exc:
            import logging
            logging.exception("Vessel list loading failed")
            st.error(f"Vessel loading error: {type(exc).__name__}: {exc}")
        else:
            if not vessels:
                st.info("No vessels have been registered for your company yet.")
            else:
                for vessel in vessels:
                    with st.container(border=True):
                        st.markdown(f"**{vessel.get('name', 'Unnamed vessel')}**")
                        st.caption(
                            f"Vessel ID: {vessel.get('vessel_id', 'N/A')}"
                        )
                        st.write(
                            f"Status: {vessel.get('status', 'Unknown')}"
                        )
                        if vessel.get("imo_number"):
                            st.write(
                                f"IMO number: {vessel['imo_number']}"
                            )
                        if vessel.get("device_id"):
                            st.write(
                                f"Sensor device: {vessel['device_id']}"
                            )

    else:
        # Dashboard header
        st.title("Marine Monitoring Dashboard")
        st.caption("EcoSpillGuard · Sensor Monitoring")

        st.info(
            "Sensor readings are retrieved from Blossom's local HTTP server. "
            "Values marked N/A are not currently available."
        )

        # Refresh the dashboard every five seconds.
        st_autorefresh(
            interval=5000,
            limit=None,
            key="sensor_refresh",
        )

        # Fetch latest reading
        result = get_latest_reading()
        reading = result.get("reading")
        connected = result.get("connected", False)

        # Connection error handling
        if not connected:
            st.error(
                result.get(
                    "error",
                    "The sensor server is currently unavailable.",
                )
            )
            st.caption(
                "Check that Blossom's Python server is running and that "
                "both computers can access the same local network."
            )

        elif reading is None:
            st.warning(
                "The server responded, but no valid reading object was returned."
            )

        else:
            st.success("Sensor server reachable")

            sensor_status = reading.get("status", "UNKNOWN")
            distance = reading.get("distance_cm")
            water = reading.get("water_percent")
            led = reading.get("led", "Unknown")
            gps_status = reading.get("gps_status", "Unknown")
            timestamp = reading.get("timestamp", "Unknown")

            if sensor_status == "INVALID":
                st.warning(
                    "The server is reachable, but the latest sensor reading "
                    "is marked INVALID. Check the sensor and hardware output."
                )

            # Metrics
            col1, col2, col3 = st.columns(3)

            col1.metric(
                "Distance",
                f"{distance} cm" if distance is not None else "N/A",
            )
            col2.metric(
                "Water reading",
                f"{water}%" if water is not None else "N/A",
            )
            col3.metric("Sensor status", str(sensor_status))

            # Sensor details
            st.subheader("Sensor Details")
            detail1, detail2, detail3 = st.columns(3)

            with detail1:
                st.markdown("**LED status**")
                st.write(led)

            with detail2:
                st.markdown("**GPS status**")
                st.write(gps_status)

            with detail3:
                st.markdown("**Sensor timestamp**")
                st.write(timestamp)

            # GPS coordinates
            latitude = reading.get("latitude")
            longitude = reading.get("longitude")

            st.subheader("Location")
            if latitude is not None and longitude is not None:
                st.write(f"Latitude: {latitude}")
                st.write(f"Longitude: {longitude}")
            else:
                st.info(
                    "GPS coordinates are unavailable. "
                    "The device may not have acquired a GPS fix."
                )

            # Honest interpretation of sensor state
            if sensor_status != "NORMAL":
                st.warning(
                    "The sensor is not reporting NORMAL status. "
                    "No oil-spill conclusion can be made from this reading alone."
                )
            else:
                st.info(
                    "The sensor reports NORMAL status. This does not independently "
                    "confirm that the water is free of oil. ML detection has not "
                    "been integrated yet."
                )

        # Future modules
        st.divider()
        st.subheader("Other Monitoring Modules")
        module1, module2, module3 = st.columns(3)

        with module1:
            st.markdown("**AI Detection**")
            st.caption("Pending ML model integration")

        with module2:
            st.markdown("**Incident History**")
            st.caption("Historical incident storage not connected yet")

        with module3:
            st.markdown("**Reports**")
            st.caption("Report generation not connected yet")

else:
    # =========================================================
    # LOGIN PAGE
    # =========================================================
    st.markdown(
        '<div class="brand">ECO<span>SPILL</span>GUARD</div>',
        unsafe_allow_html=True,
    )
    st.divider()

    left, right = st.columns([1.15, 0.85], gap="large")

    # Introduction panel
    with left:
        st.markdown(
            """
            <div style="padding-top:55px;padding-right:35px">
                <div class="eyebrow">MARINE INTELLIGENCE PLATFORM</div>
                <div class="headline">
                    Protecting our<br>
                    oceans through<br>
                    <span>early detection.</span>
                </div>
                <div class="description">
                    A unified monitoring platform designed to help identify
                    potential oil-spill indicators, review sensor readings,
                    and support faster environmental response.
                </div>
                <br>
                <div class="feature"><span>✦</span>Sensor monitoring and incident tracking</div>
                <div class="feature"><span>✦</span>AI-assisted image analysis</div>
                <div class="feature"><span>✦</span>Location-aware incident reporting</div>
                <div class="footer-note">ENVIRONMENTAL MONITORING · RESPONSIBLE RESPONSE</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Sign-in and registration forms
    with right:
        st.markdown("<div style='height:35px'></div>", unsafe_allow_html=True)
        with st.container(border=True):
            sign_in_tab, create_tab = st.tabs(["Sign In", "Create Account"])

            with sign_in_tab:
                st.markdown(
                    """
                    <div class="login-heading">Welcome back</div>
                    <div class="login-subtitle">Sign in to access your monitoring workspace.</div>
                    """,
                    unsafe_allow_html=True,
                )
                with st.form("login_form"):
                    login_email = st.text_input(
                        "Email address",
                        placeholder="name@organisation.com",
                        key="login_email",
                    )
                    login_password = st.text_input(
                        "Password",
                        type="password",
                        placeholder="Enter your password",
                        key="login_password",
                    )
                    login_submitted = st.form_submit_button(
                        "Sign in →",
                        use_container_width=True,
                    )

                if login_submitted:
                    if not login_email.strip() or not login_password:
                        st.error("Enter both your email and password.")
                    else:
                        with st.spinner("Signing in securely..."):
                            user, error = firebase_sign_in(login_email, login_password)
                        if error:
                            st.error(error)
                        else:
                            st.session_state.user = {
                                "email": user["email"],
                                "local_id": user["localId"],
                            }
                            st.session_state.firebase_token = user["idToken"]
                            st.rerun()

            with create_tab:
                st.markdown(
                    """
                    <div class="login-heading">Join EcoSpill</div>
                    <div class="login-subtitle">Create an account for your monitoring workspace.</div>
                    """,
                    unsafe_allow_html=True,
                )
                with st.form("create_account_form"):
                    signup_email = st.text_input(
                        "Email address",
                        placeholder="name@organisation.com",
                        key="signup_email",
                    )
                    signup_password = st.text_input(
                        "Create password",
                        type="password",
                        placeholder="At least 6 characters",
                        key="signup_password",
                    )
                    confirm_password = st.text_input(
                        "Confirm password",
                        type="password",
                        placeholder="Re-enter your password",
                        key="confirm_password",
                    )
                    signup_submitted = st.form_submit_button(
                        "Create account →",
                        use_container_width=True,
                    )

                if signup_submitted:
                    if not signup_email.strip() or not signup_password or not confirm_password:
                        st.error("Complete all fields to create your account.")
                    elif len(signup_password) < 6:
                        st.error("Your password must contain at least 6 characters.")
                    elif signup_password != confirm_password:
                        st.error("The passwords do not match.")
                    else:
                        with st.spinner("Creating your secure account..."):
                            user, error = firebase_create_account(signup_email, signup_password)
                        if error:
                            st.error(error)
                        else:
                            st.session_state.user = {
                                "email": user["email"],
                                "local_id": user["localId"],
                            }
                            st.session_state.firebase_token = user["idToken"]
                            st.success("Account created. Your Firebase UID is ready.")
                            st.rerun()

            st.markdown(
                """
                <div class="security-note">
                    <strong>SECURE WORKSPACE</strong><br>
                    Accounts are managed through Firebase Authentication.
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div style="text-align:center;color:#647e8d;font-size:11px;padding-top:22px">
            ECOSPILLGUARD · DEVELOPMENT PREVIEW
        </div>
        """,
        unsafe_allow_html=True,
    )
