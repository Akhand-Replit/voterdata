import logging
from sqlalchemy import create_engine, Column, String, Integer, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

Base = declarative_base()

class RelationType(enum.Enum):
    NONE = "none"
    FRIEND = "friend"
    ENEMY = "enemy"

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
    relation_type = Column(Enum(RelationType), default=RelationType.NONE)

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
        return [self._record_to_dict(record, include_id=True) for record in records]

    def search_records(self, **kwargs):
        """Search records based on given criteria."""
        query = self.session.query(Record)

        for key, value in kwargs.items():
            if value:
                query = query.filter(getattr(Record, key).ilike(f"%{value}%"))

        results = query.all()
        return [self._record_to_dict(record, include_id=True) for record in results]

    def update_record(self, record_id, updated_data):
        """Update a specific record by ID."""
        try:
            record = self.session.query(Record).filter_by(id=record_id).first()
            if record:
                for key, value in updated_data.items():
                    if hasattr(record, key):
                        setattr(record, key, value)
                self.session.commit()
                logger.info(f"Successfully updated record with ID: {record_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error updating record {record_id}: {str(e)}")
            return False

    def delete_record(self, record_id):
        """Delete a specific record by ID."""
        try:
            record = self.session.query(Record).filter_by(id=record_id).first()
            if record:
                self.session.delete(record)
                self.session.commit()
                logger.info(f"Successfully deleted record with ID: {record_id}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting record {record_id}: {str(e)}")
            return False

    def delete_all_records(self):
        """Delete all records from the database."""
        try:
            self.session.query(Record).delete()
            self.session.commit()
            logger.info("Successfully deleted all records from the database")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting all records: {str(e)}")
            raise Exception(f"Failed to delete all records: {str(e)}")

    def _record_to_dict(self, record, include_id=False):
        """Convert Record object to dictionary."""
        result = {
            'ক্রমিক_নং': record.ক্রমিক_নং,
            'নাম': record.নাম,
            'ভোটার_নং': record.ভোটার_নং,
            'পিতার_নাম': record.পিতার_নাম,
            'মাতার_নাম': record.মাতার_নাম,
            'পেশা': record.পেশা,
            'জন্ম_তারিখ': record.জন্ম_তারিখ,
            'ঠিকানা': record.ঠিকানা,
            'file_name': record.file_name,
            'relation_type': record.relation_type.value if record.relation_type else 'none'
        }
        if include_id:
            result['id'] = record.id
        return result

    def delete_file_data(self, filename):
        """Delete all records associated with a specific file."""
        try:
            deleted = self.session.query(Record).filter_by(file_name=filename).delete()
            self.session.commit()
            logger.info(f"Successfully deleted {deleted} records for file: {filename}")
            return True
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error deleting records for file {filename}: {str(e)}")
            raise Exception(f"Failed to delete records for file {filename}: {str(e)}")

    def get_file_data_with_batch(self, filename, batch_name):
        """Get data for a specific file with batch information."""
        return self.session.query(Record).filter_by(
            file_name=f"{batch_name}/{filename}"
        ).all()

    def add_file_data_with_batch(self, filename, batch_name, records):
        """Add or update file data with batch information."""
        full_filename = f"{batch_name}/{filename}"
        for record in records:
            db_record = Record(
                file_name=full_filename,
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

    def mark_relation(self, record_id: int, relation_type: RelationType) -> bool:
        """Mark a record as friend or enemy"""
        try:
            record = self.session.query(Record).filter_by(id=record_id).first()
            if record:
                record.relation_type = relation_type
                self.session.commit()
                logger.info(f"Successfully marked record {record_id} as {relation_type.value}")
                return True
            return False
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error marking record {record_id}: {str(e)}")
            return False

    def get_relations_by_type(self, relation_type: RelationType, folder: str = None):
        """Get all records marked as friends or enemies, optionally filtered by folder"""
        query = self.session.query(Record).filter_by(relation_type=relation_type)

        if folder:
            query = query.filter(Record.file_name.like(f"{folder}/%"))

        records = query.all()
        return [self._record_to_dict(record, include_id=True) for record in records]