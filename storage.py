import logging
from sqlalchemy import create_engine, Column, String, Integer, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
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

    # Add relationship to RelationRecord
    relations = relationship("RelationRecord", back_populates="record")

class RelationRecord(Base):
    __tablename__ = 'relations'

    id = Column(Integer, primary_key=True)
    record_id = Column(Integer, ForeignKey('records.id'))
    relation_type = Column(Enum(RelationType), nullable=False)
    folder = Column(String)

    # Store copied data for quick access
    ক্রমিক_নং = Column(String)
    নাম = Column(String)
    ভোটার_নং = Column(String)
    পিতার_নাম = Column(String)
    মাতার_নাম = Column(String)
    পেশা = Column(String)
    জন্ম_তারিখ = Column(String)
    ঠিকানা = Column(String)
    file_name = Column(String)

    # Add relationship to Record
    record = relationship("Record", back_populates="relations")

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
        try:
            full_filename = f"{batch_name}/{filename}"
            # Process records in smaller batches to avoid transaction issues
            batch_size = 100
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                try:
                    # Start a new transaction for each batch
                    for record in batch:
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
                    logger.info(f"Successfully added batch of {len(batch)} records")
                except Exception as e:
                    self.session.rollback()
                    logger.error(f"Error adding batch: {str(e)}")
                    raise
        except Exception as e:
            self.session.rollback()
            logger.error(f"Error in add_file_data_with_batch: {str(e)}")
            raise

    def mark_relation(self, record_id: int, relation_type: RelationType) -> bool:
        """Mark a record as friend or enemy by creating a relation record"""
        try:
            # Get the original record
            record = self.session.query(Record).filter_by(id=record_id).first()
            if not record:
                logger.warning(f"No record found with ID {record_id}")
                return False

            # Check if relation already exists
            existing_relation = self.session.query(RelationRecord).filter_by(
                record_id=record_id,
                relation_type=relation_type
            ).first()

            if existing_relation:
                logger.info(f"Relation already exists for record {record_id}")
                return True

            # Create new relation record with copied data
            folder = record.file_name.split('/')[0] if '/' in record.file_name else None
            relation = RelationRecord(
                record_id=record.id,
                relation_type=relation_type,
                folder=folder,
                ক্রমিক_নং=record.ক্রমিক_নং,
                নাম=record.নাম,
                ভোটার_নং=record.ভোটার_নং,
                পিতার_নাম=record.পিতার_নাম,
                মাতার_নাম=record.মাতার_নাম,
                পেশা=record.পেশা,
                জন্ম_তারিখ=record.জন্ম_তারিখ,
                ঠিকানা=record.ঠিকানা,
                file_name=record.file_name
            )

            self.session.add(relation)
            self.session.commit()
            logger.info(f"Successfully marked record {record_id} as {relation_type.value}")
            return True

        except Exception as e:
            self.session.rollback()
            logger.error(f"Error marking record {record_id} as {relation_type.value}: {str(e)}")
            return False

    def get_relations_by_type(self, relation_type: RelationType, folder: str = None):
        """Get all records marked as friends or enemies, optionally filtered by folder"""
        try:
            query = self.session.query(RelationRecord).filter_by(relation_type=relation_type)

            if folder and folder != "সকল":
                query = query.filter_by(folder=folder)

            relations = query.all()
            return [{
                'id': relation.record_id,
                'ক্রমিক_নং': relation.ক্রমিক_নং,
                'নাম': relation.নাম,
                'ভোটার_নং': relation.ভোটার_নং,
                'পিতার_নাম': relation.পিতার_নাম,
                'মাতার_নাম': relation.মাতার_নাম,
                'পেশা': relation.পেশা,
                'জন্ম_তারিখ': relation.জন্ম_তারিখ,
                'ঠিকানা': relation.ঠিকানা,
                'file_name': relation.file_name,
                'relation_type': relation.relation_type.value
            } for relation in relations]

        except Exception as e:
            logger.error(f"Error getting relations by type {relation_type}: {str(e)}")
            return []