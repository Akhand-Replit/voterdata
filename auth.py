import os
import streamlit as st
import requests
import json

# Magic.link configuration
MAGIC_SECRET_KEY = os.environ.get('MAGIC_SECRET_KEY')
MAGIC_PUBLISHABLE_KEY = os.environ.get('MAGIC_PUBLISHABLE_KEY')

# Fixed email for OTP
ADMIN_EMAIL = "replit@akhandfoundation.com"

def send_magic_otp():
    """Send OTP via Magic.link"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {MAGIC_SECRET_KEY}'
        }

        data = {
            'email': ADMIN_EMAIL,
            'showUI': True
        }

        response = requests.post(
            'https://api.magic.link/v1/auth/login',
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            return True
        else:
            st.error("OTP পাঠাতে সমস্যা হয়েছে")
            return False

    except Exception as e:
        st.error(f"ওটিপি পাঠাতে সমস্যা হয়েছে: {str(e)}")
        return False

def init_auth():
    """Initialize authentication in session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'email_verified' not in st.session_state:
        st.session_state.email_verified = False
    if 'magic_did_token' not in st.session_state:
        st.session_state.magic_did_token = None

def verify_magic_otp(otp):
    """Verify OTP via Magic.link"""
    try:
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {MAGIC_SECRET_KEY}'
        }

        data = {
            'email': ADMIN_EMAIL,
            'code': otp
        }

        response = requests.post(
            'https://api.magic.link/v1/auth/verify-otp',
            headers=headers,
            json=data
        )

        if response.status_code == 200:
            return response.json().get('didToken')
        return None

    except Exception as e:
        st.error(f"ওটিপি যাচাই করতে সমস্যা হয়েছে: {str(e)}")
        return None

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

import os
import streamlit as st
from twilio.rest import Client
import random
import string

# Twilio setup (removed in final implementation)
# TWILIO_ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID")
# TWILIO_AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN")
# TWILIO_PHONE_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER")


def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join(random.choices(string.digits, k=6))

#def send_otp_email(otp): #removed
#    """Send OTP via Twilio""" #removed
#    try: #removed
#        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN) #removed
#        message = client.messages.create( #removed
#            body=f"Your OTP for Bangla Text Processing App is: {otp}", #removed
#            from_=TWILIO_PHONE_NUMBER, #removed
#            to=ADMIN_EMAIL #removed
#        ) #removed
#        return True #removed
#    except Exception as e: #removed
#        st.error(f"ওটিপি পাঠাতে সমস্যা হয়েছে: {str(e)}") #removed
#        return False #removed


def init_auth():
    """Initialize authentication in session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'email_verified' not in st.session_state:
        st.session_state.email_verified = False
    if 'magic_did_token' not in st.session_state:
        st.session_state.magic_did_token = None

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