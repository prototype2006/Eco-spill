
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh
from core.data_interface import get_latest_reading


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

        error_code = (
            result.get("error", {}).get("message", "")
        )

        messages = {
            "INVALID_LOGIN_CREDENTIALS":
                "Incorrect email or password.",
            "EMAIL_NOT_FOUND":
                "No account was found for that email.",
            "INVALID_PASSWORD":
                "Incorrect email or password.",
            "USER_DISABLED":
                "This account has been disabled.",
            "INVALID_EMAIL":
                "Enter a valid email address.",
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

    # ---------------- Sidebar ----------------

    with st.sidebar:
        st.markdown("## 🌊 EcoSpillGuard")
        st.caption("Marine Monitoring")

        st.write("Signed in as")
        st.caption(st.session_state.user["email"])

        st.divider()

        if st.button("Sign out", use_container_width=True):
            st.session_state.user = None
            st.session_state.firebase_token = None
            st.rerun()

        st.divider()
        st.caption("Development preview")

    # ---------------- Dashboard header ----------------

    st.title("Marine Monitoring Dashboard")
    st.caption("EcoSpillGuard · Sensor Monitoring")

    st.info(
        "Sensor readings are retrieved from Blossom's local HTTP server. "
        "Values marked N/A are not currently available."
    )

    # ---------------- Fetch latest reading ----------------

    st_autorefresh(
    interval=5000,
    limit=None,
    key="sensor_refresh",
)

    result = get_latest_reading()

    reading = result.get("reading")
    connected = result.get("connected", False)

    # ---------------- Connection error handling ----------------

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

    # ---------------- Display sensor data ----------------

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

        col3.metric(
            "Sensor status",
            str(sensor_status),
        )

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
                "The sensor reports NORMAL status. "
                "This does not independently confirm that the water is "
                "free of oil. ML detection has not been integrated yet."
            )

    # ---------------- Future modules ----------------

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


# =========================================================
# LOGIN PAGE
# =========================================================

else:

    st.markdown(
        '<div class="brand">ECO<span>SPILL</span>GUARD</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    left, right = st.columns(
        [1.15, 0.85],
        gap="large",
    )

    # ---------------- Introduction panel ----------------

    with left:
        st.markdown(
            """
            <div style="padding-top:55px;padding-right:35px">
                <div class="eyebrow">
                    MARINE INTELLIGENCE PLATFORM
                </div>

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

                <div class="feature">
                    <span>✦</span>
                    Sensor monitoring and incident tracking
                </div>

                <div class="feature">
                    <span>✦</span>
                    AI-assisted image analysis
                </div>

                <div class="feature">
                    <span>✦</span>
                    Location-aware incident reporting
                </div>

                <div class="footer-note">
                    ENVIRONMENTAL MONITORING · RESPONSIBLE RESPONSE
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ---------------- Login form ----------------

    with right:
        st.markdown(
            "<div style='height:35px'></div>",
            unsafe_allow_html=True,
        )

        with st.container(border=True):

            st.markdown(
                """
                <div class="login-heading">Welcome back</div>

                <div class="login-subtitle">
                    Sign in to access your monitoring workspace.
                </div>
                """,
                unsafe_allow_html=True,
            )

            with st.form("login_form"):

                email = st.text_input(
                    "Email address",
                    placeholder="name@organisation.com",
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                )

                submitted = st.form_submit_button(
                    "Sign in →",
                    use_container_width=True,
                )

            if submitted:

                if not email.strip() or not password:
                    st.error("Enter both your email and password.")

                else:
                    with st.spinner("Signing in securely..."):
                        user, error = firebase_sign_in(
                            email,
                            password,
                        )

                    if error:
                        st.error(error)

                    else:
                        st.session_state.user = {
                            "email": user["email"],
                            "local_id": user["localId"],
                        }

                        st.session_state.firebase_token = (
                            user["idToken"]
                        )

                        st.rerun()

            st.markdown(
                """
                <div class="security-note">
                    <strong>SECURE WORKSPACE</strong><br>
                    Sign-in is verified through Firebase Authentication.
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        """
        <div style="text-align:center;color:#647e8d;
        font-size:11px;padding-top:22px">
            ECOSPILLGUARD · DEVELOPMENT PREVIEW
        </div>
        """,
        unsafe_allow_html=True,
    )
