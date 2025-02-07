import streamlit as st
import pandas as pd
from data_processor import process_text_file
from storage import Storage, RelationType
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

# Sidebar navigation with icons
page = st.sidebar.radio(
    "📑 পৃষ্ঠা নির্বাচন করুন",
    ["🏠 হোম", "📤 ফাইল আপলোড", "🔍 অনুসন্ধান", "📋 সকল তথ্য", "📊 ডেটা বিশ্লেষণ", "👥 সম্পর্ক তালিকা"]
)

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

# Initialize file deletion state
if 'file_to_delete' not in st.session_state:
    st.session_state.file_to_delete = None

# Initialize confirmation dialogs state
if 'confirm_delete_all' not in st.session_state:
    st.session_state.confirm_delete_all = False

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
        logger.info(f"Processed {len(records) if records else 0} records from {uploaded_file.name}")

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

    # Add batch name input
    batch_name = st.text_input(
        "📁 ব্যাচ/ফোল্ডারের নাম",
        help="একাধিক ফাইল একই ফোল্ডারে সংরক্ষণ করতে একটি নাম দিন",
        placeholder="উদাহরণ: ময়মনসিংহ_২০২৪"
    )

    try:
        uploaded_files = st.file_uploader(
            "টেক্সট ফাইল নির্বাচন করুন",
            type=['txt'],
            accept_multiple_files=True,
            key="file_uploader",
            help="একাধিক ফাইল নির্বাচন করতে Ctrl/Cmd চেপে ক্লিক করুন"
        )

        if uploaded_files and not batch_name:
            st.warning("⚠️ অনুগ্রহ করে প্রথমে একটি ব্যাচ/ফোল্ডারের নাম দিন")
            return

        if uploaded_files and batch_name:
            total_records = 0
            for uploaded_file in uploaded_files:
                if not uploaded_file:
                    continue

                batch_file_key = f"{batch_name}/{uploaded_file.name}"
                if batch_file_key in st.session_state.processed_files:
                    continue

                with st.spinner(f'"{uploaded_file.name}" প্রক্রিয়াকরণ চলছে...'):
                    try:
                        records, error = process_uploaded_file(uploaded_file)

                        if error:
                            st.error(f"❌ '{uploaded_file.name}': {error}")
                            continue

                        if not records:
                            st.warning(f"⚠️ '{uploaded_file.name}': কোন রেকর্ড পাওয়া যায়নি")
                            continue

                        try:
                            # Save to database with batch information
                            st.session_state.storage.add_file_data_with_batch(
                                uploaded_file.name,
                                batch_name,
                                records
                            )

                            # Update success status
                            total_records += len(records)
                            st.success(f"✅ '{uploaded_file.name}' সফলভাবে '{batch_name}' ফোল্ডারে আপলোড হয়েছে ({len(records)}টি রেকর্ড)")

                            # Show sample data
                            if records:
                                st.markdown("##### নমুনা ডেটা:")
                                sample_df = pd.DataFrame([records[0]])
                                st.dataframe(sample_df, use_container_width=True)

                            # Mark as processed
                            st.session_state.processed_files.add(batch_file_key)

                        except Exception as e:
                            logger.error(f"Error saving file {uploaded_file.name}: {str(e)}")
                            st.error(f"❌ ডেটা সংরক্ষণে সমস্যা। অনুগ্রহ করে আবার চেষ্টা করুন।")

                    except Exception as e:
                        logger.error(f"Error processing file {uploaded_file.name}: {str(e)}")
                        st.error(f"❌ ফাইল প্রক্রিয়াকরণে সমস্যা: {str(e)}")

            if total_records > 0:
                st.info(f"📈 সর্বমোট {total_records}টি রেকর্ড সফলভাবে '{batch_name}' ফোল্ডারে আপলোড হয়েছে")

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
    """Display a single record in a card format with relation buttons"""
    try:
        relation_type = record.get('relation_type', RelationType.NONE.value)

        # Create the card display
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
                <p style="color: #666; font-size: 0.9em;">🔗 বর্তমান সম্পর্ক: {
                    "বন্ধু" if relation_type == RelationType.FRIEND.value 
                    else "শত্রু" if relation_type == RelationType.ENEMY.value 
                    else "অজানা"
                }</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Action buttons in columns
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            if st.button("✏️ সম্পাদনা", key=f"edit_{record_id}"):
                st.session_state.editing = record_id

        with col2:
            if st.button("🗑️ মুছুন", key=f"delete_{record_id}"):
                if st.session_state.storage.delete_record(record_id):
                    st.success("✅ রেকর্ড মুছে ফেলা হয়েছে")
                    st.rerun()
                else:
                    st.error("❌ রেকর্ড মুছে ফেলা যায়নি")

        with col3:
            if relation_type != RelationType.FRIEND.value:
                if st.button("👥 বন্ধু হিসেবে চিহ্নিত করুন", key=f"friend_{record_id}"):
                    if st.session_state.storage.mark_relation(record_id, RelationType.FRIEND):
                        st.success("✅ বন্ধু হিসেবে চিহ্নিত করা হয়েছে")
                        st.rerun()
                    else:
                        st.error("❌ বন্ধু হিসেবে চিহ্নিত করা যায়নি")

        with col4:
            if relation_type != RelationType.ENEMY.value:
                if st.button("⚔️ শত্রু হিসেবে চিহ্নিত করুন", key=f"enemy_{record_id}"):
                    if st.session_state.storage.mark_relation(record_id, RelationType.ENEMY):
                        st.success("✅ শত্রু হিসেবে চিহ্নিত করা হয়েছে")
                        st.rerun()
                    else:
                        st.error("❌ শত্রু হিসেবে চিহ্নিত করা যায়নি")

        if st.session_state.editing == record_id:
            if edit_record(record_id, record):
                st.session_state.editing = None
                st.rerun()

    except Exception as e:
        st.error(f"রেকর্ড প্রদর্শনে সমস্যা: {str(e)}")

def show_all_data_page():
    st.header("📋 সংরক্ষিত সকল তথ্য")

    # Clear All Data button at the top
    if st.button("🗑️ সমস্ত ডেটা মুছুন", type="secondary", use_container_width=True):
        st.session_state.confirm_delete_all = True

    # Confirmation dialog for clearing all data
    if 'confirm_delete_all' in st.session_state and st.session_state.confirm_delete_all:
        st.warning("""
        ⚠️ সতর্কতা!
        আপনি কি নিশ্চিত যে আপনি সমস্ত ডেটা মুছে ফেলতে চান?
        এই কাজটি অপরিবর্তনীয়!
        """)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("হ্যাঁ, সব মুছে ফেলুন", type="primary", use_container_width=True):
                try:
                    st.session_state.storage.delete_all_records()
                    st.success("✅ সমস্ত ডেটা সফলভাবে মুছে ফেলা হয়েছে")
                    st.session_state.confirm_delete_all = False
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ ডেটা মুছে ফেলার সময় সমস্যা হয়েছে: {str(e)}")

        with col2:
            if st.button("না, বাতিল করুন", type="secondary", use_container_width=True):
                st.session_state.confirm_delete_all = False
                st.rerun()

    # Data management section
    st.markdown("""
        <div style="background-color: #f8f9fa; padding: 1rem; border-radius: 10px; text-align: center; margin-bottom: 2rem;">
            <h4 style="margin-bottom: 0.5rem;">ডাটা ম্যানেজমেন্ট</h4>
        </div>
    """, unsafe_allow_html=True)

    # Get all files and organize them by folders
    files = st.session_state.storage.get_file_names()
    if not files:
        st.info("❌ কোন ফাইল আপলোড করা হয়নি")
        return

    # Organize files by folders
    folders = {}
    for file in files:
        if '/' in file:
            folder, filename = file.split('/', 1)
            if folder not in folders:
                folders[folder] = []
            folders[folder].append(file)
        else:
            if 'অন্যান্য' not in folders:
                folders['অন্যান্য'] = []
            folders['অন্যান্য'].append(file)

    # Display folders as tabs
    selected_folder = st.selectbox("📁 ফোল্ডার নির্বাচন করুন", list(folders.keys()))

    if selected_folder:
        files_in_folder = folders[selected_folder]

        # File selection and delete button in the same row
        col1, col2 = st.columns([4, 1])

        with col1:
            selected_file = st.selectbox(
                "📄 ফাইল নির্বাচন করুন",
                files_in_folder,
                index=0 if files_in_folder else None
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
                    df = pd.DataFrame(records)
                    st.dataframe(
                        df,
                        use_container_width=True,
                        hide_index=True
                    )
                else:
                    st.info("❌ নির্বাচিত ফাইলে কোন তথ্য নেই")

def show_home_page():
    # Container for better spacing
    container = st.container()

    with container:
        # Hero Section with Gradient
        st.markdown(
            """
            <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #FF4B4B 0%, #FF8080 100%); 
                        border-radius: 20px; margin-bottom: 2rem; color: white;">
                <h1 style="font-size: 2.5rem; margin-bottom: 1rem; color: white;">
                    📚 বাংলা টেক্সট প্রসেসিং
                </h1>
                <p style="font-size: 1.2rem; opacity: 0.9;">
                    দ্রুত, নির্ভুল এবং সহজ টেক্সট ডেটা ম্যানেজমেন্ট
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Stats Section
        if hasattr(st.session_state, 'storage'):
            files = st.session_state.storage.get_file_names()
            folders = set(file.split('/')[0] for file in files if '/' in file)
            total_records = len(st.session_state.storage.get_all_records())

            # Create three columns for stats
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 1.5rem; background: white; 
                                border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h3 style="color: #FF4B4B; font-size: 2rem;">📁</h3>
                        <h4>মোট ফোল্ডার</h4>
                        <p style="font-size: 1.5rem; color: #FF4B4B;">{len(folders)}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col2:
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 1.5rem; background: white; 
                                border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h3 style="color: #FF4B4B; font-size: 2rem;">📄</h3>
                        <h4>মোট ফাইল</h4>
                        <p style="font-size: 1.5rem; color: #FF4B4B;">{len(files)}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with col3:
                st.markdown(
                    f"""
                    <div style="text-align: center; padding: 1.5rem; background: white; 
                                border-radius: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <h3 style="color: #FF4B4B; font-size: 2rem;">📊</h3>
                        <h4>মোট রেকর্ড</h4>
                        <p style="font-size: 1.5rem; color: #FF4B4B;">{total_records}</p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Features Section
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown(
            """
            <h2 style="text-align: center; margin-bottom: 2rem; color: #333;">
                🌟 মূল বৈশিষ্ট্যসমূহ
            </h2>
            """,
            unsafe_allow_html=True
        )

        # Feature Cards in columns
        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(
                """
                <div style="background: white; padding: 1.5rem; border-radius: 15px; 
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1); height: 100%;">
                    <h3 style="color: #FF4B4B; margin-bottom: 1rem;">
                        📤 ফাইল আপলোড
                    </h3>
                    <p style="color: #666;">
                        সহজে একাধিক টেক্সট ফাইল আপলোড করুন এবং ফোল্ডার অনুযায়ী সাজান
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col2:
            st.markdown(
                """
                <div style="background: white; padding: 1.5rem; border-radius: 15px; 
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1); height: 100%;">
                    <h3 style="color: #FF4B4B; margin-bottom: 1rem;">
                        🔍 অনুসন্ধান
                    </h3>
                    <p style="color: #666;">
                        দ্রুত এবং সহজে প্রয়োজনীয় তথ্য খুঁজে বের করুন
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

        with col3:
            st.markdown(
                """
                <div style="background: white; padding: 1.5rem; border-radius: 15px; 
                            box-shadow: 0 4px 6px rgba(0,0,0,0.1); height: 100%;">
                    <h3 style="color: #FF4B4B; margin-bottom: 1rem;">
                        📊 ডেটা ব্যবস্থাপনা
                    </h3>
                    <p style="color: #666;">
                        সকল তথ্য সুশৃঙ্খলভাবে সংরক্ষণ এবং পরিচালনা করুন
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

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

def show_analysis_page():
    st.header("📊 পেশা ভিত্তিক বিশ্লেষণ")

    # Get all files and organize them by folders
    files = st.session_state.storage.get_file_names()
    if not files:
        st.info("❌ কোন ফাইল আপলোড করা হয়নি")
        return

    # Organize files by folders
    folders = {}
    for file in files:
        if '/' in file:
            folder, filename = file.split('/', 1)
            if folder not in folders:
                folders[folder] = []
            folders[folder].append(file)
        else:
            if 'অন্যান্য' not in folders:
                folders['অন্যান্য'] = []
            folders['অন্যান্য'].append(file)

    # Folder selection
    selected_folder = st.selectbox(
        "📁 ফোল্ডার নির্বাচন করুন",
        list(folders.keys()),
        key="analysis_folder_select"
    )

    if selected_folder:
        st.subheader(f"📊 {selected_folder} - পেশা অনুযায়ী বিশ্লেষণ")

        # Get all records for the selected folder's files
        all_records = []
        for file in folders[selected_folder]:
            records = st.session_state.storage.get_file_data(file)
            all_records.extend(records)

        if all_records:
            # Count occupations
            occupation_counts = {}
            for record in all_records:
                occupation = record.get('পেশা', 'অজানা')
                occupation = occupation.strip() if occupation else 'অজানা'
                occupation_counts[occupation] = occupation_counts.get(occupation, 0) + 1

            # Create DataFrame for visualization
            df = pd.DataFrame(
                list(occupation_counts.items()),
                columns=['পেশা', 'সংখ্যা']
            ).sort_values('সংখ্যা', ascending=False)

            # Show total records
            st.markdown(f"""
                <div style="background-color: #f0f2f6; padding: 1rem; border-radius: 10px; margin-bottom: 1rem;">
                    <h4 style="margin: 0;">📈 মোট রেকর্ড: {len(all_records)}</h4>
                </div>
            """, unsafe_allow_html=True)

            # Display data in two columns
            col1, col2 = st.columns([3, 2])

            with col1:
                # Bar chart
                st.bar_chart(
                    df.set_index('পেশা')['সংখ্যা'],
                    use_container_width=True
                )

            with col2:
                # Detailed stats table
                st.markdown("""
                    <div style="background-color: white; padding: 1rem; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h4 style="margin-bottom: 1rem;">📋 বিস্তারিত তথ্য</h4>
                    </div>
                """, unsafe_allow_html=True)

                st.dataframe(
                    df,
                    use_container_width=True,
                    hide_index=True
                )

                # Calculate and show percentages
                df['শতাংশ'] = (df['সংখ্যা'] / len(all_records) * 100).round(2)
                st.markdown("#### শতাংশ বিভাজন")
                st.dataframe(
                    df[['পেশা', 'শতাংশ']],
                    use_container_width=True,
                    hide_index=True
                )

        else:
            st.info("❌ নির্বাচিত ফোল্ডারে কোন রেকর্ড নেই")


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
    .stTextInput>div>>div>input {
        border-radius: 8px;
        font-family: 'SolaimanLipi', Arial, sans-serif !important;
        border: 1px solid #e0e0e0;
        font-size: 16px !important;
        min-height: 45px;
        padding: 0.5rem;
    }
    h1 {
        color: #1E1E1E;padding-bottom: 2rem;
        font-weight: 600;
    }
    h2 {
        color: #2E2E2E;
        padding-bottom: 1rem;
        font-weight: 500;
    }
    .stProgress > div > div > div > div{
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



def show_relations_page():
    """Display relations list page with improved functionality"""
    st.header("👥 সম্পর্ক তালিকা")

    # Get all files and organize them by folders
    files = st.session_state.storage.get_file_names()
    if not files:
        st.info("❌ কোন ফাইল আপলোড করা হয়নি")
        return

    # Organize files by folders
    folders = set()
    for file in files:
        if '/' in file:
            folder = file.split('/', 1)[0]
            folders.add(folder)

    # Add "All" option at the beginning
    folder_list = ["সকল"] + sorted(list(folders))

    # Folder selection
    selected_folder = st.selectbox(
        "📁 ফোল্ডার নির্বাচন করুন",
        folder_list,
        index=0
    )

    # Create tabs for Friends and Enemies
    friend_tab, enemy_tab = st.tabs(["👥 বন্ধু তালিকা", "⚔️ শত্রু তালিকা"])

    with friend_tab:
        try:
            friends = st.session_state.storage.get_relations_by_type(RelationType.FRIEND, selected_folder)
            if friends:
                st.write(f"📊 মোট {len(friends)}টি বন্ধু")
                for friend in friends:
                    display_record_card(friend, friend['id'])
            else:
                st.info("❌ কোন বন্ধু তালিকাভুক্ত নেই")
        except Exception as e:
            st.error(f"বন্ধু তালিকা লোড করতে সমস্যা: {str(e)}")

    with enemy_tab:
        try:
            enemies = st.session_state.storage.get_relations_by_type(RelationType.ENEMY, selected_folder)
            if enemies:
                st.write(f"📊 মোট {len(enemies)}টি শত্রু")
                for enemy in enemies:
                    display_record_card(enemy, enemy['id'])
            else:
                st.info("❌ কোন শত্রু তালিকাভুক্ত নেই")
        except Exception as e:
            st.error(f"শত্রু তালিকা লোড করতে সমস্যা: {str(e)}")

# Update the page routing to include the relations page
def main():
    st.title("📚 বাংলা টেক্সট প্রসেসিং অ্যাপ্লিকেশন")

    if page == "🏠 হোম":
        show_home_page()
    elif page == "📤 ফাইল আপলোড":
        show_upload_page()
    elif page == "🔍 অনুসন্ধান":
        show_search_page()
    elif page == "📊 ডেটা বিশ্লেষণ":
        show_analysis_page()
    elif page == "👥 সম্পর্ক তালিকা":
        show_relations_page()
    else:
        show_all_data_page()

if __name__ == "__main__":
    main()