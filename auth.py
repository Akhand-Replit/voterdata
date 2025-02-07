import os
import streamlit as st
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Magic.link configuration
MAGIC_SECRET_KEY = os.environ.get('MAGIC_SECRET_KEY')
MAGIC_PUBLISHABLE_KEY = os.environ.get('MAGIC_PUBLISHABLE_KEY')

# Fixed email for OTP
ADMIN_EMAIL = "replit@akhandfoundation.com"

def configure_allowlist():
    """Configure domain allowlist for Magic.link"""
    try:
        headers = {
            'X-Magic-Secret-Key': MAGIC_SECRET_KEY,
            'Content-Type': 'application/json'
        }

        data = {
            'access_type': 'domain',
            'target_client_id': 'etjubJsY5Cvn6ukDzJYpd3MEAtgw45oetxxoX1PxvP4=',
            'value': 'https://magic.link'
        }

        response = requests.post(
            'https://api.magic.link/v2/api/magic_client/allowlist/add',
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            logger.info("Magic.link allowlist configured successfully")
            return True
        else:
            logger.error(f"Failed to configure allowlist: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Error configuring allowlist: {str(e)}")
        return False

def send_magic_otp():
    """Send OTP via Magic.link v2 API"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-Magic-Secret-Key': MAGIC_SECRET_KEY
        }

        data = {
            'email': ADMIN_EMAIL,
            'showUI': True
        }

        response = requests.post(
            'https://api.magic.link/v2/auth/login',
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            logger.info(f"OTP sent successfully to {ADMIN_EMAIL}")
            return True
        else:
            logger.error(f"Failed to send OTP: {response.text}")
            st.error("OTP পাঠাতে সমস্যা হয়েছে")
            return False

    except Exception as e:
        logger.error(f"Error sending OTP: {str(e)}")
        st.error(f"ওটিপি পাঠাতে সমস্যা হয়েছে: {str(e)}")
        return False

def verify_magic_otp(otp):
    """Verify OTP via Magic.link v2 API"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'X-Magic-Secret-Key': MAGIC_SECRET_KEY
        }

        data = {
            'email': ADMIN_EMAIL,
            'code': otp
        }

        response = requests.post(
            'https://api.magic.link/v2/auth/verify-otp',
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            logger.info("OTP verified successfully")
            return response.json().get('didToken')

        logger.error(f"Failed to verify OTP: {response.text}")
        return None

    except Exception as e:
        logger.error(f"Error verifying OTP: {str(e)}")
        st.error(f"ওটিপি যাচাই করতে সমস্যা হয়েছে: {str(e)}")
        return None

def init_auth():
    """Initialize authentication in session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'email_verified' not in st.session_state:
        st.session_state.email_verified = False
    if 'magic_did_token' not in st.session_state:
        st.session_state.magic_did_token = None

    # Configure allowlist on initialization
    if not st.session_state.get('allowlist_configured'):
        if configure_allowlist():
            st.session_state.allowlist_configured = True
            logger.info("Allowlist configured successfully")
        else:
            logger.warning("Failed to configure allowlist")

def login_form():
    """Display login form and handle authentication"""
    if st.session_state.authenticated:
        return True

    st.markdown("""
        <div style="background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="text-align: center; margin-bottom: 2rem;">🔐 প্রবেশ করুন</h2>
        </div>
    """, unsafe_allow_html=True)

    # Send OTP if not already verified
    if not st.session_state.email_verified:
        st.info(f"ওটিপি পাঠানো হবে: {ADMIN_EMAIL}")
        if st.button("ওটিপি পাঠান", type="primary"):
            if send_magic_otp():
                st.session_state.email_verified = True
                st.success("ওটিপি পাঠানো হয়েছে!")
                st.rerun()
    else:
        otp_input = st.text_input("ওটিপি", type="password")
        if st.button("প্রবেশ করুন", type="primary"):
            did_token = verify_magic_otp(otp_input)
            if did_token:
                st.session_state.authenticated = True
                st.session_state.magic_did_token = did_token
                st.success("সফলভাবে প্রবেশ করা হয়েছে!")
                st.rerun()
            else:
                st.error("ভুল ওটিপি")

    return st.session_state.authenticated

def logout():
    """Handle logout"""
    if st.session_state.authenticated:
        st.session_state.authenticated = False
        st.session_state.magic_did_token = None
        if 'email_verified' in st.session_state:
            del st.session_state.email_verified
        logger.info("User logged out successfully")