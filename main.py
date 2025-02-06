import streamlit as st
import pandas as pd
from data_processor import process_text_file
from storage import Storage
import io

# Initialize session state
if 'storage' not in st.session_state:
    st.session_state.storage = Storage()

def main():
    st.title("বাংলা টেক্সট প্রসেসিং অ্যাপ্লিকেশন")
    
    # Sidebar navigation
    page = st.sidebar.radio("পৃষ্ঠা নির্বাচন করুন", ["ফাইল আপলোড", "অনুসন্ধান", "সকল তথ্য"])
    
    if page == "ফাইল আপলোড":
        show_upload_page()
    elif page == "অনুসন্ধান":
        show_search_page()
    else:
        show_all_data_page()

def show_upload_page():
    st.header("ফাইল আপলোড")
    uploaded_files = st.file_uploader(
        "টেক্সট ফাইল নির্বাচন করুন",
        type=['txt'],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            content = uploaded_file.read().decode('utf-8')
            records = process_text_file(content)
            st.session_state.storage.add_file_data(uploaded_file.name, records)
            st.success(f"'{uploaded_file.name}' সফলভাবে আপলোড হয়েছে")

def show_search_page():
    st.header("উন্নত অনুসন্ধান")
    
    col1, col2 = st.columns(2)
    
    with col1:
        si_number = st.text_input("ক্রমিক নং")
        name = st.text_input("নাম")
        father_name = st.text_input("পিতার নাম")
        mother_name = st.text_input("মাতার নাম")
    
    with col2:
        occupation = st.text_input("পেশা")
        address = st.text_input("ঠিকানা")
        dob = st.text_input("জন্ম তারিখ")
    
    if st.button("অনুসন্ধান করুন"):
        results = st.session_state.storage.search_records(
            si_number=si_number,
            name=name,
            father_name=father_name,
            mother_name=mother_name,
            occupation=occupation,
            address=address,
            dob=dob
        )
        
        if results:
            st.write(f"মোট {len(results)} টি ফলাফল পাওয়া গেছে:")
            df = pd.DataFrame(results)
            st.dataframe(df)
        else:
            st.info("কোন ফলাফল পাওয়া যায়নি")
    
    if st.button("সকল তথ্য দেখুন"):
        all_records = st.session_state.storage.get_all_records()
        if all_records:
            df = pd.DataFrame(all_records)
            st.dataframe(df)
        else:
            st.info("কোন তথ্য সংরক্ষিত নেই")

def show_all_data_page():
    st.header("সংরক্ষিত সকল তথ্য")
    
    files = st.session_state.storage.get_file_names()
    
    if not files:
        st.info("কোন ফাইল আপলোড করা হয়নি")
        return
    
    selected_file = st.selectbox("ফাইল নির্বাচন করুন", files)
    
    if selected_file:
        records = st.session_state.storage.get_file_data(selected_file)
        if records:
            df = pd.DataFrame(records)
            st.dataframe(df)
        else:
            st.info("নির্বাচিত ফাইলে কোন তথ্য নেই")

if __name__ == "__main__":
    main()
