import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_text_file(content):
    """Process the text file content and extract structured data."""
    records = []

    # Strip any BOM and normalize whitespace
    content = content.strip().replace('\ufeff', '')

    try:
        # Split records by looking for Bengali/English numerals followed by dot at line start
        # More robust pattern that handles various formats
        raw_records = re.split(r'\n\s*(?=(?:[\u0966-\u096F]+|[0-9]+)\.)', content)
        logger.info(f"Found {len(raw_records)} potential records in the file")

        for record in raw_records:
            if not record.strip():
                continue

            logger.debug(f"Processing record: {record[:50]}...")  # Log first 50 chars
            record_dict = {}

            # Extract data with more flexible patterns
            patterns = {
                'ক্রমিক_নং': r'^(?:[\u0966-\u096F]+|[0-9]+)\.',
                'নাম': r'নাম:\s*([^,\n।]+)',
                'ভোটার_নং': r'ভোটার\s*নং:?\s*([^,\n।]+)',
                'পিতার_নাম': r'পিতা:?\s*([^,\n।]+)',
                'মাতার_নাম': r'মাতা:?\s*([^,\n।]+)',
                'পেশা': r'পেশা:?\s*([^,\n।]+)',
                'জন্ম_তারিখ': r'জন্ম\s*তারিখ:?\s*([^,\n।]+)',
                'ঠিকানা': r'ঠিকানা:?\s*([^,\n।]+)'
            }

            for field, pattern in patterns.items():
                match = re.search(pattern, record)
                if match:
                    # For ক্রমিক_নং, we want the full number including the dot
                    value = match.group(0).strip() if field == 'ক্রমিক_নং' else match.group(1).strip()
                    # Remove the trailing dot from ক্রমিক_নং
                    if field == 'ক্রমিক_নং':
                        value = value.rstrip('.')
                    record_dict[field] = value

            if record_dict:
                records.append(record_dict)
                logger.debug(f"Successfully extracted fields: {list(record_dict.keys())}")
            else:
                logger.warning(f"No fields extracted from record: {record[:100]}...")

        logger.info(f"Successfully processed {len(records)} records")
        return records

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise Exception(f"Failed to process file: {str(e)}")