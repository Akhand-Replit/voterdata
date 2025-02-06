import streamlit as st
import pandas as pd
from data_processor import process_text_file
from storage import Storage
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        font-family: 'SolaimanLipi', Arial, sans-serif !important;
    }
    h1 {
        color: #1E1E1E;
        padding-bottom: 2rem;
    }
    h2 {
        color: #2E2E2E;
        padding-bottom: 1rem;
    }
    .stProgress > div > div > div > div {
        background-color: #f63366;
    }
    .upload-stats {
        padding: 1rem;
        background-color: #f8f9fa;
        border-radius: 5px;
        margin: 1rem 0;
    }
    .delete-button {
        background-color: #dc3545;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border: none;
        cursor: pointer;
    }
    .edit-button {
        background-color: #28a745;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        border: none;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# Add Bangla font support
st.markdown("""
<style>
@font-face {
    font-family: 'SolaimanLipi';
    src: url('https://cdn.jsdelivr.net/gh/maateen/bangla-web-fonts/fonts/SolaimanLipi/SolaimanLipi.ttf') format('truetype');
}
* {
    font-family: 'SolaimanLipi', Arial, sans-serif !important;
}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'storage' not in st.session_state:
    st.session_state.storage = Storage()

def edit_record(record_id, record_data):
    """Edit record dialog"""
    with st.form(key=f'edit_form_{record_id}'):
        st.subheader("📝 রেকর্ড সম্পাদনা")
        edited_data = {}

        edited_data['ক্রমিক_নং'] = st.text_input("ক্রমিক নং", value=record_data['ক্রমিক_নং'])
        edited_data['নাম'] = st.text_input("নাম", value=record_data['নাম'])
        edited_data['ভোটার_নং'] = st.text_input("ভোটার নং", value=record_data['ভোটার_নং'])
        edited_data['পিতার_নাম'] = st.text_input("পিতার নাম", value=record_data['পিতার_নাম'])
        edited_data['মাতার_নাম'] = st.text_input("মাতার নাম", value=record_data['মাতার_নাম'])
        edited_data['পেশা'] = st.text_input("পেশা", value=record_data['পেশা'])
        edited_data['জন্ম_তারিখ'] = st.text_input("জন্ম তারিখ", value=record_data['জন্ম_তারিখ'])
        edited_data['ঠিকানা'] = st.text_input("ঠিকানা", value=record_data['ঠিকানা'])

        submit = st.form_submit_button("💾 সংরক্ষণ করুন")
        if submit:
            if st.session_state.storage.update_record(record_id, edited_data):
                st.success("✅ রেকর্ড সফলভাবে আপডেট করা হয়েছে")
                return True
            else:
                st.error("❌ রেকর্ড আপডেট করা যায়নি")
    return False

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
        total_records = 0
        for uploaded_file in uploaded_files:
            with st.spinner(f'"{uploaded_file.name}" প্রক্রিয়াকরণ চলছে...'):
                try:
                    # Add a progress bar
                    progress_bar = st.progress(0)

                    # Read file content
                    content = uploaded_file.read().decode('utf-8')
                    progress_bar.progress(25)

                    # Process records
                    records = process_text_file(content)
                    progress_bar.progress(50)

                    if not records:
                        st.warning(f"⚠️ '{uploaded_file.name}' থেকে কোন রেকর্ড পাওয়া যায়নি")
                        continue

                    # Save to database
                    st.session_state.storage.add_file_data(uploaded_file.name, records)
                    progress_bar.progress(100)

                    # Show success message with record count
                    total_records += len(records)
                    st.success(f"✅ '{uploaded_file.name}' সফলভাবে আপলোড হয়েছে ({len(records)}টি রেকর্ড)")

                    # Show sample of processed data
                    if len(records) > 0:
                        st.markdown("##### নমুনা ডেটা:")
                        sample_df = pd.DataFrame([records[0]])
                        st.dataframe(sample_df, use_container_width=True)

                    # Show detailed stats
                    st.markdown(f"""
                    <div class="upload-stats">
                        📊 <b>ফাইল তথ্য:</b><br>
                        - মোট রেকর্ড: {len(records)}<br>
                        - ফাইল নাম: {uploaded_file.name}<br>
                        - ফাইল সাইজ: {round(len(content)/1024, 2)} KB
                    </div>
                    """, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"❌ ফাইল প্রক্রিয়াকরণে সমস্যা: {str(e)}")
                    logger.error(f"Error processing file {uploaded_file.name}: {str(e)}")
                finally:
                    # Clean up progress bar
                    if 'progress_bar' in locals():
                        progress_bar.empty()

        if total_records > 0:
            st.info(f"📈 সর্বমোট {total_records}টি রেকর্ড সফলভাবে আপলোড হয়েছে")

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

                    # Show results with edit and delete buttons
                    for record in results:
                        record_id = record.pop('id')  # Remove id from display but keep for operations

                        # Create columns for record and buttons
                        record_col, edit_col, delete_col = st.columns([6, 1, 1])

                        with record_col:
                            st.write(record)

                        with edit_col:
                            if st.button("✏️ সম্পাদনা", key=f"edit_{record_id}"):
                                if edit_record(record_id, record):
                                    st.experimental_rerun()

                        with delete_col:
                            if st.button("🗑️ মুছুন", key=f"delete_{record_id}"):
                                if st.session_state.storage.delete_record(record_id):
                                    st.success("✅ রেকর্ড মুছে ফেলা হয়েছে")
                                    st.experimental_rerun()
                                else:
                                    st.error("❌ রেকর্ড মুছে ফেলা যায়নি")
                else:
                    st.info("❌ কোন ফলাফল পাওয়া যায়নি")

def show_all_data_page():
    st.header("📋 সংরক্ষিত সকল তথ্য")

    # Add delete all button
    if st.button("🗑️ সব ডেটা মুছে ফেলুন", key="delete_all"):
        if st.checkbox("আপনি কি নিশ্চিত?"):
            st.session_state.storage.delete_all_records()
            st.success("✅ সব ডেটা মুছে ফেলা হয়েছে")
            st.experimental_rerun()

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