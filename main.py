import streamlit as st
import pandas as pd
from data_processor import process_text_file
from storage import Storage
import io
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize session state for file upload and editing
if 'upload_state' not in st.session_state:
    st.session_state.upload_state = {
        'processing': False,
        'current_file': None,
        'error': None
    }

# Initialize editing state
if 'editing' not in st.session_state:
    st.session_state.editing = None

# Initialize confirmation dialogs state
if 'confirm_delete' not in st.session_state:
    st.session_state.confirm_delete = False

# Initialize processed files state
if 'processed_files' not in st.session_state:
    st.session_state.processed_files = set()

# Initialize storage if not exists
if 'storage' not in st.session_state:
    st.session_state.storage = Storage()

def process_uploaded_file(uploaded_file):
    """Process a single uploaded file with proper error handling"""
    try:
        if uploaded_file.size > 200 * 1024 * 1024:  # 200MB limit
            return None, "ফাইলের সাইজ 200MB এর বেশি হতে পারবে না"

        # Read file content with explicit encoding and error handling
        try:
            content = uploaded_file.getvalue().decode('utf-8-sig', errors='replace')
        except UnicodeDecodeError:
            return None, "ফাইলটি সঠিক ফরম্যাটে নেই। দয়া করে UTF-8 এনকোডিং ব্যবহার করুন।"

        # Process the content
        records = process_text_file(content)

        if not records:
            return None, "কোন রেকর্ড পাওয়া যায়নি"

        return records, None
    except Exception as e:
        logger.error(f"Error processing file {uploaded_file.name}: {str(e)}")
        return None, f"ফাইল প্রক্রিয়াকরণে সমস্যা: {str(e)}"

def show_upload_page():
    st.header("📤 ফাইল আপলোড")

    # Add description with clear file requirements
    st.markdown("""
    #### ব্যবহার নির্দেশিকা:
    1. একাধিক টেক্সট ফাইল একসাথে আপলোড করতে পারবেন
    2. প্রতিটি ফাইল স্বয়ংক্রিয়ভাবে প্রক্রিয়াকরণ করা হবে
    3. ডেটা সুরক্ষিতভাবে সংরক্ষণ করা হবে

    **সীমাবদ্ধতা:**
    - সর্বোচ্চ ফাইল সাইজ: 200MB
    - শুধুমাত্র .txt ফাইল সমর্থিত
    - ফাইল এনকোডিং: UTF-8
    """)

    # Initialize upload states if not exists
    if 'processed_files' not in st.session_state:
        st.session_state.processed_files = set()

    try:
        uploaded_files = st.file_uploader(
            "টেক্সট ফাইল নির্বাচন করুন",
            type=['txt'],
            accept_multiple_files=True,
            key="file_uploader",
            help="একাধিক ফাইল নির্বাচন করতে Ctrl/Cmd চেপে ক্লিক করুন"
        )

        if uploaded_files:
            total_records = 0
            for uploaded_file in uploaded_files:
                if uploaded_file.name in st.session_state.processed_files:
                    continue

                with st.spinner(f'"{uploaded_file.name}" প্রক্রিয়াকরণ চলছে...'):
                    records, error = process_uploaded_file(uploaded_file)

                    if error:
                        st.error(f"❌ '{uploaded_file.name}': {error}")
                        continue

                    try:
                        # Save to database
                        st.session_state.storage.add_file_data(uploaded_file.name, records)

                        # Update success status
                        total_records += len(records)
                        st.success(f"✅ '{uploaded_file.name}' সফলভাবে আপলোড হয়েছে ({len(records)}টি রেকর্ড)")

                        # Show sample data
                        st.markdown("##### নমুনা ডেটা:")
                        sample_df = pd.DataFrame([records[0]])
                        st.dataframe(sample_df, use_container_width=True)

                        # Mark as processed
                        st.session_state.processed_files.add(uploaded_file.name)
                    except Exception as e:
                        logger.error(f"Error saving file {uploaded_file.name}: {str(e)}")
                        st.error(f"❌ ডেটা সংরক্ষণে সমস্যা: {str(e)}")

            if total_records > 0:
                st.info(f"📈 সর্বমোট {total_records}টি রেকর্ড সফলভাবে আপলোড হয়েছে")

    except Exception as e:
        st.error(f"❌ অপ্রত্যাশিত সমস্যা: {str(e)}")
        logger.error(f"Unexpected error in file upload: {str(e)}")

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
        <div style="border-top: 1px solid #eee; margin-top: 1rem; padding-top: 0.5rem;">
            <p style="color: #666; font-size: 0.9em;">📂 ফাইল অবস্থান: {record['file_name']}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✏️ সম্পাদনা", key=f"edit_{record_id}"):
            st.session_state.editing = record_id

    with col2:
        if st.button("🗑️ মুছুন", key=f"delete_{record_id}"):
            # Add confirmation dialog
            st.warning("আপনি কি নিশ্চিত যে আপনি এই রেকর্ডটি মুছতে চান?")
            if st.button("হ্যাঁ, মুছে ফেলুন", key=f"confirm_delete_{record_id}"):
                try:
                    if st.session_state.storage.delete_record(record_id):
                        st.success("✅ রেকর্ড মুছে ফেলা হয়েছে")
                        st.rerun()
                    else:
                        st.error("❌ রেকর্ড মুছে ফেলা যায়নি")
                except Exception as e:
                    st.error(f"❌ রেকর্ড মুছে ফেলার সময় সমস্যা: {str(e)}")

    # Show edit form if this record is being edited
    if st.session_state.editing == record_id:
        if edit_record(record_id, record):
            st.session_state.editing = None
            st.rerun()

def show_all_data_page():
    st.header("📋 সংরক্ষিত সকল তথ্য")

    # Data management section with full width
    st.markdown("""
        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;">
            <h4 style="margin-bottom: 0.5rem;">ডাটা ম্যানেজমেন্ট</h4>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🗑️ সব ডেটা মুছে ফেলুন", type="secondary", key="delete_all"):
        st.session_state.confirm_delete = True

    if st.session_state.confirm_delete:
        st.warning("""
        ⚠️ সতর্কতা!
        আপনি কি নিশ্চিত যে আপনি সমস্ত ডেটা মুছে ফেলতে চান?
        """)

        confirm_col1, confirm_col2 = st.columns([1, 1])
        with confirm_col1:
            if st.button("হ্যাঁ, মুছে ফেলুন", key="confirm_delete_final", type="primary"):
                try:
                    st.session_state.storage.delete_all_records()
                    st.success("✅ সব ডেটা সফলভাবে মুছে ফেলা হয়েছে")
                    st.session_state.confirm_delete = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ ডেটা মুছে ফেলার সময় সমস্যা হয়েছে: {str(e)}")

        with confirm_col2:
            if st.button("না, বাতিল করুন", key="cancel_delete", type="secondary"):
                st.session_state.confirm_delete = False
                st.rerun()

    # File selection with full width
    files = st.session_state.storage.get_file_names()

    if not files:
        st.info("❌ কোন ফাইল আপলোড করা হয়নি")
        return

    # Initialize file deletion state if not exists
    if 'file_to_delete' not in st.session_state:
        st.session_state.file_to_delete = None

    # File selection and delete button in the same row
    col1, col2 = st.columns([4, 1])

    with col1:
        selected_file = st.selectbox(
            "📁 ফাইল নির্বাচন করুন",
            files,
            index=0 if files else None
        )

    with col2:
        if selected_file and st.button("🗑️ ফাইল মুছুন", key=f"delete_file_{selected_file}"):
            st.session_state.file_to_delete = selected_file

    # File deletion confirmation
    if st.session_state.file_to_delete:
        st.warning(f"""
        ⚠️ সতর্কতা!
        আপনি কি নিশ্চিত যে আপনি '{st.session_state.file_to_delete}' ফাইল এবং এর সকল রেকর্ড মুছে ফেলতে চান?
        """)

        confirm_col1, confirm_col2 = st.columns([1, 1])
        with confirm_col1:
            if st.button("হ্যাঁ, মুছে ফেলুন", key="confirm_file_delete", type="primary"):
                try:
                    # Delete file and its records
                    st.session_state.storage.delete_file_data(st.session_state.file_to_delete)
                    st.success(f"✅ '{st.session_state.file_to_delete}' ফাইল এবং এর সকল রেকর্ড মুছে ফেলা হয়েছে")
                    st.session_state.file_to_delete = None
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ ফাইল মুছে ফেলার সময় সমস্যা হয়েছে: {str(e)}")

        with confirm_col2:
            if st.button("না, বাতিল করুন", key="cancel_file_delete", type="secondary"):
                st.session_state.file_to_delete = None
                st.rerun()

    # Display file data
    if selected_file:
        with st.spinner('তথ্য লোড হচ্ছে...'):
            records = st.session_state.storage.get_file_data(selected_file)
            if records:
                # Create a clean DataFrame display with full width
                df = pd.DataFrame(records)
                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("❌ নির্বাচিত ফাইলে কোন তথ্য নেই")

def show_home_page():
    # Hero Section with modern design
    st.markdown("""
        <div style="text-align: center; padding: 3rem 0; background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%); border-radius: 20px; margin-bottom: 2rem;">
            <h1 style="font-size: 2.5rem; margin-bottom: 1rem;">📚 বাংলা টেক্সট প্রসেসিং</h1>
            <p style="font-size: 1.2rem; color: #6c757d; margin-bottom: 2rem;">দ্রুত, নির্ভুল এবং সহজ টেক্সট ডেটা ম্যানেজমেন্ট</p>
            <div style="max-width: 600px; margin: 0 auto;">
                <img src="https://img.icons8.com/fluency/240/000000/database.png" style="width: 120px; margin-bottom: 2rem;">
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Features Section
    st.markdown("""
        <div style="margin: 2rem 0;">
            <h2 style="text-align: center; margin-bottom: 2rem;">🌟 মূল বৈশিষ্ট্যসমূহ</h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem;">
                <div style="background: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h3 style="color: #FF4B4B;">📤 ফাইল আপলোড</h3>
                    <p>সহজে একাধিক টেক্সট ফাইল আপলোড করুন</p>
                </div>
                <div style="background: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h3 style="color: #FF4B4B;">🔍 অনুসন্ধান</h3>
                    <p>দ্রুত এবং সহজে তথ্য খুঁজে বের করুন</p>
                </div>
                <div style="background: white; padding: 1.5rem; border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    <h3 style="color: #FF4B4B;">📊 ডেটা ম্যানেজমেন্ট</h3>
                    <p>সহজে তথ্য সংরক্ষণ এবং পরিচালনা করুন</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Call to Action Section
    st.markdown("""
        <div style="text-align: center; margin: 3rem 0; padding: 2rem; background: linear-gradient(135deg, #FF4B4B 0%, #ff6b6b 100%); border-radius: 20px; color: white;">
            <h2 style="margin-bottom: 1rem;">🚀 শুরু করুন</h2>
            <p style="margin-bottom: 2rem;">আপনার প্রথম ফাইল আপলোড করে শুরু করুন</p>
        </div>
    """, unsafe_allow_html=True)

    # Quick Stats or Info (if available)
    if hasattr(st.session_state, 'storage'):
        files = st.session_state.storage.get_file_names()
        if files:
            total_files = len(files)
            st.markdown(f"""
                <div style="text-align: center; margin-top: 2rem;">
                    <p style="font-size: 1.1rem; color: #6c757d;">
                        📈 বর্তমানে {total_files}টি ফাইল প্রক্রিয়াকরণ করা হয়েছে
                    </p>
                </div>
            """, unsafe_allow_html=True)


def show_search_page():
    st.header("🔍 উন্নত অনুসন্ধান")

    # Create two columns for search fields
    col1, col2 = st.columns(2)

    search_params = {}

    with col1:
        si_number = st.text_input("🔢 ক্রমিক নং", key="search_si")
        if si_number:
            search_params['ক্রমিক_নং'] = si_number

        name = st.text_input("👤 নাম", key="search_name")
        if name:
            search_params['নাম'] = name

        father_name = st.text_input("👨 পিতার নাম", key="search_father")
        if father_name:
            search_params['পিতার_নাম'] = father_name

        mother_name = st.text_input("👩 মাতার নাম", key="search_mother")
        if mother_name:
            search_params['মাতার_নাম'] = mother_name

    with col2:
        voter_id = st.text_input("🗳️ ভোটার নং", key="search_voter")
        if voter_id:
            search_params['ভোটার_নং'] = voter_id

        occupation = st.text_input("💼 পেশা", key="search_occupation")
        if occupation:
            search_params['পেশা'] = occupation

        address = st.text_input("🏠 ঠিকানা", key="search_address")
        if address:
            search_params['ঠিকানা'] = address

        dob = st.text_input("📅 জন্ম তারিখ", key="search_dob")
        if dob:
            search_params['জন্ম_তারিখ'] = dob

    if st.button("🔍 অনুসন্ধান করুন", key="search"):
        if not search_params:
            st.warning("অনুসন্ধানের জন্য কমপক্ষে একটি ক্ষেত্র পূরণ করুন")
            return

        with st.spinner('অনুসন্ধান চলছে...'):
            try:
                results = st.session_state.storage.search_records(**search_params)

                if results:
                    st.write(f"📊 মোট {len(results)} টি ফলাফল পাওয়া গেছে:")

                    # Show results in card format
                    for record in results:
                        record_id = record.pop('id')  # Remove id from display but keep for operations
                        display_record_card(record, record_id)
                else:
                    st.info("❌ কোন ফলাফল পাওয়া যায়নি")
            except Exception as e:
                st.error(f"অনুসন্ধানে সমস্যা হয়েছে: {str(e)}")
                logger.error(f"Search error: {str(e)}")

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
        border-radius: 10px;
        height: 3em;
        background-color: #FF4B4B;
        color: white;
        font-weight: 500;
        border: none;
        margin: 0.5rem 0;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #ff6b6b;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        transform: translateY(-2px);
    }
    .stButton>button:active {
        transform: translateY(0);
    }
    .stTextInput>div>div>input {
        border-radius: 8px;
        font-family: 'SolaimanLipi', Arial, sans-serif !important;
        border: 1px solid #e0e0e0;
        font-size: 16px !important;
        min-height: 45px;
        padding: 0.5rem;
    }
    h1 {
        color: #1E1E1E;
        padding-bottom: 2rem;
        font-weight: 600;
    }
    h2 {
        color: #2E2E2E;
        padding-bottom: 1rem;
        font-weight: 500;
    }
    .stProgress > div > div > div > div {
        background-color: #FF4B4B;
    }
    .upload-stats {
        padding: 1.5rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .record-card {
        background-color: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        border: 1px solid #f0f0f0;
    }
    .stAlert {
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    div[data-testid="stToolbar"] {
        display: none;
    }
    .stAlert > div {
        padding: 0.75rem 1rem;
        border-radius: 8px;
    }
    div[data-baseweb="select"] > div {
        border-radius: 8px;
        background-color: white;
    }
    .delete-button, .edit-button {
        width: 100%;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.3s ease;
        border: none;
        margin: 0.5rem 0;
    }
    .delete-button {
        background-color: #dc3545;
        color: white;
    }
    .delete-button:hover {
        background-color: #c82333;
        box-shadow: 0 4px 8px rgba(220,53,69,0.2);
    }
    .edit-button {
        background-color: #28a745;
        color: white;
    }
    .edit-button:hover {
        background-color: #218838;
        box-shadow: 0 4px 8px rgba(40,167,69,0.2);
    }
    input, textarea, .stTextInput, .stSelectbox, [data-baseweb="input"] {
        font-family: 'SolaimanLipi', Arial, sans-serif !important;
    }
    * {
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }
    ::placeholder {
        font-family: 'SolaimanLipi', Arial, sans-serif !important;
        opacity: 0.7;
    }
</style>
""", unsafe_allow_html=True)

# Add Bangla font support with multiple sources for better compatibility
st.markdown("""
<style>
@font-face {
    font-family: 'SolaimanLipi';
    src: url('https://cdn.jsdelivr.net/gh/maateen/bangla-web-fonts/fonts/SolaimanLipi/SolaimanLipi.woff2') format('woff2'),
         url('https://cdn.jsdelivr.net/gh/maateen/bangla-web-fonts/fonts/SolaimanLipi/SolaimanLipi.woff') format('woff'),
         url('https://cdn.jsdelivr.net/gh/maateen/bangla-web-fonts/fonts/SolaimanLipi/SolaimanLipi.ttf') format('truetype');
    font-weight: normal;
    font-style: normal;
    font-display: swap;
}
</style>
""", unsafe_allow_html=True)


def main():
    st.title("📚 বাংলা টেক্সট প্রসেসিং অ্যাপ্লিকেশন")

    # Sidebar navigation with icons
    page = st.sidebar.radio(
        "📑 পৃষ্ঠা নির্বাচন করুন",
        ["🏠 হোম", "📤 ফাইল আপলোড", "🔍 অনুসন্ধান", "📋 সকল তথ্য"]
    )

    if "🏠 হোম" in page:
        show_home_page()
    elif "📤 ফাইল আপলোড" in page:
        show_upload_page()
    elif "🔍 অনুসন্ধান" in page:
        show_search_page()
    else:
        show_all_data_page()

if __name__ == "__main__":
    main()