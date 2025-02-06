import re

def process_text_file(content):
    """Process the text file content and extract structured data."""
    records = []

    # Split content into individual records using a more robust pattern
    # Look for patterns like "০০০১." or "১." at the start of lines
    raw_records = re.split(r'\n*(?=[\u0966-\u096F]+\.)', content.strip())

    for record in raw_records:
        if not record.strip():
            continue

        # Extract data using regular expressions
        record_dict = {}

        # Extract SI number - handle both Bengali and English numerals
        si_match = re.search(r'^([\u0966-\u096F\d]+)\.', record)
        if si_match:
            record_dict['ক্রমিক_নং'] = si_match.group(1)

        # Extract name with improved pattern
        name_match = re.search(r'নাম:\s*([^,\n।]+)', record)
        if name_match:
            record_dict['নাম'] = name_match.group(1).strip()

        # Extract voter number with improved pattern
        voter_match = re.search(r'ভোটার\s*নং:\s*([^,\n।]+)', record)
        if voter_match:
            record_dict['ভোটার_নং'] = voter_match.group(1).strip()

        # Extract father's name with improved pattern
        father_match = re.search(r'পিতা:\s*([^,\n।]+)', record)
        if father_match:
            record_dict['পিতার_নাম'] = father_match.group(1).strip()

        # Extract mother's name with improved pattern
        mother_match = re.search(r'মাতা:\s*([^,\n।]+)', record)
        if mother_match:
            record_dict['মাতার_নাম'] = mother_match.group(1).strip()

        # Extract occupation with improved pattern
        occupation_match = re.search(r'পেশা:\s*([^,\n।]+)', record)
        if occupation_match:
            record_dict['পেশা'] = occupation_match.group(1).strip()

        # Extract date of birth with improved pattern
        dob_match = re.search(r'জন্ম\s*তারিখ:\s*([^,\n।]+)', record)
        if dob_match:
            record_dict['জন্ম_তারিখ'] = dob_match.group(1).strip()

        # Extract address with improved pattern
        address_match = re.search(r'ঠিকানা:\s*([^,\n।]+)', record)
        if address_match:
            record_dict['ঠিকানা'] = address_match.group(1).strip()

        if record_dict:
            records.append(record_dict)

    return records