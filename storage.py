from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()

class Record(Base):
    __tablename__ = 'records'

    id = Column(Integer, primary_key=True)
    file_name = Column(String)
    ক্রমিক_নং = Column(String)
    নাম = Column(String)
    ভোটার_নং = Column(String)
    পিতার_নাম = Column(String)
    মাতার_নাম = Column(String)
    পেশা = Column(String)
    জন্ম_তারিখ = Column(String)
    ঠিকানা = Column(String)

class Storage:
    def __init__(self):
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is not set")

        self.engine = create_engine(database_url)
        Base.metadata.create_all(self.engine)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add_file_data(self, filename, records):
        """Add or update file data."""
        for record in records:
            db_record = Record(
                file_name=filename,
                ক্রমিক_নং=record.get('ক্রমিক_নং', ''),
                নাম=record.get('নাম', ''),
                ভোটার_নং=record.get('ভোটার_নং', ''),
                পিতার_নাম=record.get('পিতার_নাম', ''),
                মাতার_নাম=record.get('মাতার_নাম', ''),
                পেশা=record.get('পেশা', ''),
                জন্ম_তারিখ=record.get('জন্ম_তারিখ', ''),
                ঠিকানা=record.get('ঠিকানা', '')
            )
            self.session.add(db_record)
        self.session.commit()

    def get_file_data(self, filename):
        """Get data for a specific file."""
        records = self.session.query(Record).filter_by(file_name=filename).all()
        return [self._record_to_dict(record) for record in records]

    def get_file_names(self):
        """Get list of all uploaded files."""
        files = self.session.query(Record.file_name).distinct().all()
        return [file[0] for file in files]

    def get_all_records(self):
        """Get all records from all files."""
        records = self.session.query(Record).all()
        return [self._record_to_dict(record) for record in records]

    def search_records(self, **kwargs):
        """Search records based on given criteria."""
        query = self.session.query(Record)

        for key, value in kwargs.items():
            if value:
                query = query.filter(getattr(Record, key).ilike(f"%{value}%"))

        results = query.all()
        return [self._record_to_dict(record) for record in results]

    def _record_to_dict(self, record):
        """Convert Record object to dictionary."""
        return {
            'ক্রমিক_নং': record.ক্রমিক_নং,
            'নাম': record.নাম,
            'ভোটার_নং': record.ভোটার_নং,
            'পিতার_নাম': record.পিতার_নাম,
            'মাতার_নাম': record.মাতার_নাম,
            'পেশা': record.পেশা,
            'জন্ম_তারিখ': record.জন্ম_তারিখ,
            'ঠিকানা': record.ঠিকানা
        }