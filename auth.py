import os
import streamlit as st

def init_auth():
    """Initialize authentication in session state"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'email_verified' not in st.session_state:
        st.session_state.email_verified = False

def login_form():
    """Display login form and handle authentication"""
    if st.session_state.authenticated:
        return True

    st.markdown("""
        <div style="background: white; padding: 2rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h2 style="text-align: center; margin-bottom: 2rem;">🔐 প্রবেশ করুন</h2>
        </div>
    """, unsafe_allow_html=True)

    # Only show OTP input if email is verified
    if 'email_verified' not in st.session_state:
        st.info("একটি ওটিপি পাঠানো হবে: replit@akhandfoundation.com")
        if st.button("ওটিপি পাঠান", type="primary"):
            try:
                # In a real implementation, this would generate and send an OTP
                # For now, we'll simulate it
                st.session_state.email_verified = True
                st.success("ওটিপি পাঠানো হয়েছে!")
                st.rerun()
            except Exception as e:
                st.error(f"ওটিপি পাঠাতে সমস্যা হয়েছে: {str(e)}")
    else:
        otp = st.text_input("ওটিপি", type="password")
        if st.button("প্রবেশ করুন", type="primary"):
            try:
                # Here we would validate the OTP with Magic.link
                # For demo, we'll use a simple check
                if otp == "123456":  # Replace with actual OTP validation
                    st.session_state.authenticated = True
                    st.success("সফলভাবে প্রবেশ করা হয়েছে!")
                    st.rerun()
                else:
                    st.error("ভুল ওটিপি")
            except Exception as e:
                st.error(f"লগইন সমস্যা: {str(e)}")

    return st.session_state.authenticated

def logout():
    """Handle logout"""
    if st.session_state.authenticated:
        st.session_state.authenticated = False
        if 'email_verified' in st.session_state:
            del st.session_state.email_verified