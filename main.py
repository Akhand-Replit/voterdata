import streamlit as st
import pandas as pd
from data_processor import process_text_file
from storage import Storage
import io

# Set page configuration
st.set_page_config(
    page_title="বাংলা টেক্সট প্রসেসিং",
    page_icon="📝",
    layout="wide"
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 2rem;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #f63366;
        color: white;
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    h1 {
        color: #1E1E1E;
        padding-bottom: 2rem;
    }
    h2 {
        color: #2E2E2E;
        padding-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'storage' not in st.session_state:
    st.session_state.storage = Storage()

def main():
    st.title("📚 বাংলা টেক্সট প্রসেসিং অ্যাপ্লিকেশন")

    # Sidebar navigation with icons
    page = st.sidebar.radio(
        "📑 পৃষ্ঠা নির্বাচন করুন",
        ["📤 ফাইল আপলোড", "🔍 অনুসন্ধান", "📋 সকল তথ্য"]
    )

    if "📤 ফাইল আপলোড" in page:
        show_upload_page()
    elif "🔍 অনুসন্ধান" in page:
        show_search_page()
    else:
        show_all_data_page()

def show_upload_page():
    st.header("📤 ফাইল আপলোড")

    # Add description
    st.markdown("""
    #### ব্যবহার নির্দেশিকা:
    1. একাধিক টেক্সট ফাইল একসাথে আপলোড করতে পারবেন
    2. প্রতিটি ফাইল স্বয়ংক্রিয়ভাবে প্রক্রিয়াকরণ করা হবে
    3. ডেটা সুরক্ষিতভাবে সংরক্ষণ করা হবে
    """)

    uploaded_files = st.file_uploader(
        "টেক্সট ফাইল নির্বাচন করুন",
        type=['txt'],
        accept_multiple_files=True
    )

    if uploaded_files:
        with st.spinner('ফাইল প্রক্রিয়াকরণ চলছে...'):
            for uploaded_file in uploaded_files:
                content = uploaded_file.read().decode('utf-8')
                records = process_text_file(content)
                st.session_state.storage.add_file_data(uploaded_file.name, records)
                st.success(f"✅ '{uploaded_file.name}' সফলভাবে আপলোড হয়েছে ({len(records)}টি রেকর্ড)")

def show_search_page():
    st.header("🔍 উন্নত অনুসন্ধান")

    # Create two columns for search fields
    col1, col2 = st.columns(2)

    with col1:
        si_number = st.text_input("🔢 ক্রমিক নং")
        name = st.text_input("👤 নাম")
        father_name = st.text_input("👨 পিতার নাম")
        mother_name = st.text_input("👩 মাতার নাম")

    with col2:
        occupation = st.text_input("💼 পেশা")
        address = st.text_input("🏠 ঠিকানা")
        dob = st.text_input("📅 জন্ম তারিখ")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 অনুসন্ধান করুন", key="search"):
            with st.spinner('অনুসন্ধান চলছে...'):
                results = st.session_state.storage.search_records(
                    ক্রমিক_নং=si_number,
                    নাম=name,
                    পিতার_নাম=father_name,
                    মাতার_নাম=mother_name,
                    পেশা=occupation,
                    ঠিকানা=address,
                    জন্ম_তারিখ=dob
                )

                if results:
                    st.write(f"📊 মোট {len(results)} টি ফলাফল পাওয়া গেছে:")
                    df = pd.DataFrame(results)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("❌ কোন ফলাফল পাওয়া যায়নি")

    with col2:
        if st.button("📋 সকল তথ্য দেখুন", key="show_all"):
            with st.spinner('তথ্য লোড হচ্ছে...'):
                all_records = st.session_state.storage.get_all_records()
                if all_records:
                    df = pd.DataFrame(all_records)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("❌ কোন তথ্য সংরক্ষিত নেই")

def show_all_data_page():
    st.header("📋 সংরক্ষিত সকল তথ্য")

    files = st.session_state.storage.get_file_names()

    if not files:
        st.info("❌ কোন ফাইল আপলোড করা হয়নি")
        return

    selected_file = st.selectbox("📁 ফাইল নির্বাচন করুন", files)

    if selected_file:
        with st.spinner('তথ্য লোড হচ্ছে...'):
            records = st.session_state.storage.get_file_data(selected_file)
            if records:
                df = pd.DataFrame(records)
                st.dataframe(df, use_container_width=True)
            else:
                st.info("❌ নির্বাচিত ফাইলে কোন তথ্য নেই")

if __name__ == "__main__":
    main()