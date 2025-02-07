import logging
from sqlalchemy import create_engine, Column, String, Integer, Enum, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import OperationalError, SQLAlchemyError
import os
import enum
import time
from sqlalchemy.pool import QueuePool
from sqlalchemy.sql import text
import functools

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

class RelationRecord(Base):
    __tablename__ = 'relation_records'

    id = Column(Integer, primary_key=True)
    record_id = Column(Integer, ForeignKey('records.id', ondelete='CASCADE'))
    relation_type = Column(Enum(RelationType), nullable=False)
    folder = Column(String)
    ক্রমিক_নং = Column(String)
    নাম = Column(String)
    ভোটার_নং = Column(String)
    পিতার_নাম = Column(String)
    মাতার_নাম = Column(String)
    পেশা = Column(String)
    জন্ম_তারিখ = Column(String)
    ঠিকানা = Column(String)
    file_name = Column(String)

class Storage:
    def __init__(self):
        self.initialize_database()

    def initialize_database(self):
        """Initialize database with connection pooling and retry mechanism"""
        max_retries = 3
        retry_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                database_url = os.getenv("DATABASE_URL")
                if not database_url:
                    raise ValueError("DATABASE_URL environment variable is not set")

                # Configure connection pooling
                self.engine = create_engine(
                    database_url,
                    poolclass=QueuePool,
                    pool_size=10,
                    max_overflow=20,
                    pool_timeout=30,
                    pool_pre_ping=True  # Enable connection health checks
                )
                Base.metadata.create_all(self.engine)
                Session = sessionmaker(bind=self.engine)
                self.session = Session()
                logger.info("Database initialized successfully with connection pooling")
                return
            except Exception as e:
                logger.error(f"Error initializing database (attempt {attempt + 1}/{max_retries}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    raise

    def reconnect(self):
        """Reconnect to database if connection is lost"""
        try:
            self.session.close()
        except:
            pass
        self.initialize_database()

    def execute_with_retry(self, operation):
        """Execute database operation with retry mechanism"""
        max_retries = 3
        retry_delay = 1

        for attempt in range(max_retries):
            try:
                return operation()
            except OperationalError as e:
                if "SSL connection has been closed" in str(e) or "connection" in str(e).lower():
                    logger.warning(f"Database connection error (attempt {attempt + 1}/{max_retries}): {str(e)}")
                    if attempt < max_retries - 1:
                        self.reconnect()
                        time.sleep(retry_delay)
                        retry_delay *= 2
                    else:
                        raise
                else:
                    raise
            except SQLAlchemyError as e:
                logger.error(f"Database error: {str(e)}")
                raise

    def add_file_data(self, filename, records):
        """Add or update file data."""
        def operation():
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
        self.execute_with_retry(operation)


    @functools.lru_cache(maxsize=128)
    def get_file_names(self):
        """Get list of all uploaded files with caching."""
        def operation():
            # Use more efficient query
            result = self.session.execute(
                text("SELECT DISTINCT file_name FROM records")
            )
            return [row[0] for row in result]
        return self.execute_with_retry(operation)

    def get_file_data(self, filename, page=1, per_page=100):
        """Get paginated data for a specific file."""
        def operation():
            offset = (page - 1) * per_page
            records = (self.session.query(Record)
                      .filter_by(file_name=filename)
                      .limit(per_page)
                      .offset(offset)
                      .all())
            total = self.session.query(Record).filter_by(file_name=filename).count()
            return {
                'records': [self._record_to_dict(record, include_id=True) for record in records],
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        return self.execute_with_retry(operation)

    def get_all_records(self):
        """Get all records from all files."""
        def operation():
            records = self.session.query(Record).all()
            return [self._record_to_dict(record, include_id=True) for record in records]
        return self.execute_with_retry(operation)

    def search_records(self, **kwargs):
        """Search records based on given criteria."""
        def operation():
            query = self.session.query(Record)
            for key, value in kwargs.items():
                if value:
                    query = query.filter(getattr(Record, key).ilike(f"%{value}%"))
            results = query.all()
            return [self._record_to_dict(record, include_id=True) for record in results]
        return self.execute_with_retry(operation)

    def update_record(self, record_id, updated_data):
        """Update a specific record by ID."""
        def operation():
            try:
                record = self.session.query(Record).filter_by(id=record_id).first()
                if record:
                    for key, value in updated_data.items():
                        if hasattr(record, key):
                            setattr(record, key, value)
                    self.session.commit()
                    return True
                return False
            except Exception as e:
                self.session.rollback()
                logger.error(f"Error updating record {record_id}: {str(e)}")
                return False
        return self.execute_with_retry(operation)

    def delete_record(self, record_id):
        """Delete a specific record by ID."""
        def operation():
            try:
                record = self.session.query(Record).filter_by(id=record_id).first()
                if record:
                    # This will cascade delete any relations due to ForeignKey constraint
                    self.session.delete(record)
                    self.session.commit()
                    return True
                return False
            except Exception as e:
                self.session.rollback()
                logger.error(f"Error deleting record {record_id}: {str(e)}")
                return False
        return self.execute_with_retry(operation)

    def mark_relation(self, record_id: int, relation_type: RelationType) -> bool:
        """Mark a record as friend or enemy by creating a relation record"""
        def operation():
            try:
                # Get the original record
                record = self.session.query(Record).filter_by(id=record_id).first()
                if not record:
                    logger.warning(f"No record found with ID {record_id}")
                    return False

                # Delete existing relation if any
                self.session.query(RelationRecord).filter_by(record_id=record_id).delete()

                # Create new relation record
                folder = record.file_name.split('/')[0] if '/' in record.file_name else None
                relation = RelationRecord(
                    record_id=record_id,
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
        return self.execute_with_retry(operation)

    def get_relations_by_type(self, relation_type: RelationType, folder: str = None):
        """Get all records marked as friends or enemies, optionally filtered by folder"""
        def operation():
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
        return self.execute_with_retry(operation)

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
            'relation_type': RelationType.NONE.value  # Default to NONE
        }

        # Check if this record has any relations
        relation = self.session.query(RelationRecord).filter_by(record_id=record.id).first()
        if relation:
            result['relation_type'] = relation.relation_type.value

        if include_id:
            result['id'] = record.id
        return result

    def delete_file_data(self, filename):
        """Delete all records associated with a specific file."""
        def operation():
            try:
                # This will cascade delete relations due to ForeignKey constraint
                deleted = self.session.query(Record).filter_by(file_name=filename).delete()
                self.session.commit()
                logger.info(f"Successfully deleted {deleted} records for file: {filename}")
                return True
            except Exception as e:
                self.session.rollback()
                logger.error(f"Error deleting records for file {filename}: {str(e)}")
                raise
        return self.execute_with_retry(operation)

    def add_file_data_with_batch(self, filename, batch_name, records):
        """Add or update file data with batch information."""
        def operation():
            try:
                full_filename = f"{batch_name}/{filename}"
                batch_size = 100
                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    try:
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
                    except Exception as e:
                        self.session.rollback()
                        logger.error(f"Error adding batch: {str(e)}")
                        raise
            except Exception as e:
                self.session.rollback()
                logger.error(f"Error in add_file_data_with_batch: {str(e)}")
                raise
        self.execute_with_retry(operation)

    def delete_all_records(self):
        """Delete all records from the database."""
        def operation():
            try:
                # First delete all relation records due to foreign key constraints
                self.session.query(RelationRecord).delete()
                # Then delete all main records
                self.session.query(Record).delete()
                self.session.commit()
                logger.info("Successfully deleted all records from the database")
                return True
            except Exception as e:
                self.session.rollback()
                logger.error(f"Error deleting all records: {str(e)}")
                raise
        self.execute_with_retry(operation)

    def get_occupation_stats(self, folder=None):
        """Get occupation statistics efficiently using SQL."""
        def operation():
            query = """
                SELECT পেশা, COUNT(*) as count
                FROM records
                WHERE পেশা IS NOT NULL AND পেশা != ''
                AND (CASE WHEN :folder != 'সকল' THEN 
                    SPLIT_PART(file_name, '/', 1) = :folder
                    ELSE TRUE END)
                GROUP BY পেশা
                ORDER BY count DESC
            """
            result = self.session.execute(text(query), {'folder': folder})
            return [(row[0], row[1]) for row in result]
        return self.execute_with_retry(operation)