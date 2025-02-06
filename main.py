import streamlit as st
import pandas as pd
from data_processor import process_text_file
from storage import Storage
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state for file upload
if 'upload_state' not in st.session_state:
    st.session_state.upload_state = {
        'processing': False,
        'current_file': None,
        'error': None
    }

def edit_record(record_id, record_data):
    """Edit record dialog"""
    st.markdown("<div class='edit-form'>", unsafe_allow_html=True)
    with st.form(key=f'edit_form_{record_id}'):
        st.subheader("📝 রেকর্ড সম্পাদনা")
        edited_data = {}

        # Create two columns for the form
        col1, col2 = st.columns(2)

        with col1:
            edited_data['ক্রমিক_নং'] = st.text_input("ক্রমিক নং", value=record_data['ক্রমিক_নং'])
            edited_data['নাম'] = st.text_input("নাম", value=record_data['নাম'])
            edited_data['ভোটার_নং'] = st.text_input("ভোটার নং", value=record_data['ভোটার_নং'])
            edited_data['পিতার_নাম'] = st.text_input("পিতার নাম", value=record_data['পিতার_নাম'])

        with col2:
            edited_data['মাতার_নাম'] = st.text_input("মাতার নাম", value=record_data['মাতার_নাম'])
            edited_data['পেশা'] = st.text_input("পেশা", value=record_data['পেশা'])
            edited_data['জন্ম_তারিখ'] = st.text_input("জন্ম তারিখ", value=record_data['জন্ম_তারিখ'])
            edited_data['ঠিকানা'] = st.text_input("ঠিকানা", value=record_data['ঠিকানা'])

        submit = st.form_submit_button("💾 সংরক্ষণ করুন")
        if submit:
            try:
                if st.session_state.storage.update_record(record_id, edited_data):
                    st.success("✅ রেকর্ড সফলভাবে আপডেট করা হয়েছে")
                    st.balloons()
                    return True
                else:
                    st.error("❌ রেকর্ড আপডেট করা যায়নি")
            except Exception as e:
                st.error(f"❌ আপডেট করার সময় সমস্যা হয়েছে: {str(e)}")
    st.markdown("</div>", unsafe_allow_html=True)
    return False

def display_record_card(record, record_id):
    """Display a single record in a card format"""
    st.markdown(f"""
    <div class='record-card'>
        <h4>🪪 {record['নাম']}</h4>
        <p><strong>ক্রমিক নং:</strong> {record['ক্রমিক_নং']}</p>
        <p><strong>ভোটার নং:</strong> {record['ভোটার_নং']}</p>
        <p><strong>পিতার নাম:</strong> {record['পিতার_নাম']}</p>
        <p><strong>মাতার নাম:</strong> {record['মাতার_নাম']}</p>
        <p><strong>পেশা:</strong> {record['পেশা']}</p>
        <p><strong>জন্ম তারিখ:</strong> {record['জন্ম_তারিখ']}</p>
        <p><strong>ঠিকানা:</strong> {record['ঠিকানা']}</p>
    </div>
    """, unsafe_allow_html=True)

    # Add edit state to session state if not exists
    if 'editing' not in st.session_state:
        st.session_state.editing = None

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✏️ সম্পাদনা", key=f"edit_{record_id}"):
            st.session_state.editing = record_id

    with col2:
        if st.button("🗑️ মুছুন", key=f"delete_{record_id}"):
            if st.session_state.storage.delete_record(record_id):
                st.success("✅ রেকর্ড মুছে ফেলা হয়েছে")
                st.experimental_rerun()
            else:
                st.error("❌ রেকর্ড মুছে ফেলা যায়নি")

    # Show edit form if this record is being edited
    if st.session_state.editing == record_id:
        if edit_record(record_id, record):
            st.session_state.editing = None
            st.experimental_rerun()

def show_all_data_page():
    st.header("📋 সংরক্ষিত সকল তথ্য")

    # Add delete all button with confirmation
    if 'confirm_delete' not in st.session_state:
        st.session_state.confirm_delete = False

    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("🗑️ সব ডেটা মুছে ফেলুন", key="delete_all"):
            st.session_state.confirm_delete = True

    if st.session_state.confirm_delete:
        st.markdown("""
        <div class='confirm-delete'>
            <h4>⚠️ সতর্কতা!</h4>
            <p>আপনি কি নিশ্চিত যে আপনি সমস্ত ডেটা মুছে ফেলতে চান?</p>
        </div>
        """, unsafe_allow_html=True)

        confirm_col1, confirm_col2 = st.columns([1, 3])
        with confirm_col1:
            if st.button("হ্যাঁ, মুছে ফেলুন", key="confirm_delete_final"):
                try:
                    st.session_state.storage.delete_all_records()
                    st.success("✅ সব ডেটা সফলভাবে মুছে ফেলা হয়েছে")
                    st.session_state.confirm_delete = False
                    st.experimental_rerun()
                except Exception as e:
                    st.error(f"❌ ডেটা মুছে ফেলার সময় সমস্যা হয়েছে: {str(e)}")

            if st.button("না, বাতিল করুন", key="cancel_delete"):
                st.session_state.confirm_delete = False
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

    # Initialize upload states if not exists
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = set()

    try:
        uploaded_files = st.file_uploader(
            "টেক্সট ফাইল নির্বাচন করুন",
            type=['txt'],
            accept_multiple_files=True,
            key="file_uploader"
        )

        if uploaded_files:
            total_records = 0

            # Process each file
            for uploaded_file in uploaded_files:
                # Skip if already processed in this session
                if uploaded_file.name in st.session_state.processed_files:
                    continue

                try:
                    with st.spinner(f'"{uploaded_file.name}" প্রক্রিয়াকরণ চলছে...'):
                        # Create a container for this file's status
                        file_container = st.container()

                        with file_container:
                            try:
                                # Read file content with explicit encoding
                                content = uploaded_file.getvalue().decode('utf-8-sig')

                                # Process the content
                                records = process_text_file(content)

                                if not records:
                                    st.warning(f"⚠️ '{uploaded_file.name}' থেকে কোন রেকর্ড পাওয়া যায়নি")
                                    continue

                                # Save to database
                                st.session_state.storage.add_file_data(uploaded_file.name, records)

                                # Update success status
                                total_records += len(records)
                                st.success(f"✅ '{uploaded_file.name}' সফলভাবে আপলোড হয়েছে ({len(records)}টি রেকর্ড)")

                                # Show sample data
                                if records:
                                    st.markdown("##### নমুনা ডেটা:")
                                    sample_df = pd.DataFrame([records[0]])
                                    st.dataframe(sample_df, use_container_width=True)

                                # Mark as processed
                                st.session_state.processed_files.add(uploaded_file.name)

                            except UnicodeDecodeError:
                                st.error(f"❌ '{uploaded_file.name}' ফাইলটি সঠিক ফরম্যাটে নেই। দয়া করে UTF-8 এনকোডিং ব্যবহার করুন।")
                            except Exception as e:
                                st.error(f"❌ ফাইল প্রক্রিয়াকরণে সমস্যা: {str(e)}")
                                logger.error(f"Error processing {uploaded_file.name}: {str(e)}")

                except Exception as outer_e:
                    st.error(f"❌ ফাইল আপলোডে সমস্যা: {str(outer_e)}")
                    logger.error(f"Outer error processing {uploaded_file.name}: {str(outer_e)}")

            if total_records > 0:
                st.info(f"📈 সর্বমোট {total_records}টি রেকর্ড সফলভাবে আপলোড হয়েছে")

        # Clear processed files when no files are selected
        if not uploaded_files:
            st.session_state.processed_files = set()

    except Exception as e:
        st.error(f"❌ অপ্রত্যাশিত সমস্যা: {str(e)}")
        logger.error(f"Unexpected error in file upload: {str(e)}")

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
        voter_id = st.text_input("🗳️ ভোটার নং")
        occupation = st.text_input("💼 পেশা")
        address = st.text_input("🏠 ঠিকানা")
        dob = st.text_input("📅 জন্ম তারিখ")

    if st.button("🔍 অনুসন্ধান করুন", key="search"):
        with st.spinner('অনুসন্ধান চলছে...'):
            results = st.session_state.storage.search_records(
                ক্রমিক_নং=si_number,
                নাম=name,
                ভোটার_নং=voter_id,
                পিতার_নাম=father_name,
                মাতার_নাম=mother_name,
                পেশা=occupation,
                ঠিকানা=address,
                জন্ম_তারিখ=dob
            )

            if results:
                st.write(f"📊 মোট {len(results)} টি ফলাফল পাওয়া গেছে:")

                # Show results in card format
                for record in results:
                    record_id = record.pop('id')  # Remove id from display but keep for operations
                    display_record_card(record, record_id)
            else:
                st.info("❌ কোন ফলাফল পাওয়া যায়নি")

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
    .record-card {
        background-color: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
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
    .edit-form {
        background-color: #f8f9fa;
        padding: 2rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .confirm-delete {
        background-color: #fff3f3;
        padding: 1rem;
        border-radius: 5px;
        border: 1px solid #dc3545;
        margin: 1rem 0;
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

if __name__ == "__main__":
    main()