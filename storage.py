class Storage:
    def __init__(self):
        self.files = {}  # Dictionary to store file data
        
    def add_file_data(self, filename, records):
        """Add or update file data."""
        self.files[filename] = records
        
    def get_file_data(self, filename):
        """Get data for a specific file."""
        return self.files.get(filename, [])
        
    def get_file_names(self):
        """Get list of all uploaded files."""
        return list(self.files.keys())
        
    def get_all_records(self):
        """Get all records from all files."""
        all_records = []
        for records in self.files.values():
            all_records.extend(records)
        return all_records
        
    def search_records(self, **kwargs):
        """Search records based on given criteria."""
        results = []
        all_records = self.get_all_records()
        
        for record in all_records:
            match = True
            for key, value in kwargs.items():
                if value:  # Only check non-empty search criteria
                    record_value = record.get(key, "")
                    if value.lower() not in record_value.lower():
                        match = False
                        break
            if match:
                results.append(record)
                
        return results
