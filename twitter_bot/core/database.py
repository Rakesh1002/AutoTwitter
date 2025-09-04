#!/usr/bin/env python3
"""
Database Manager
Handles database connections, migrations, and operations
"""

import logging
from typing import Optional, Dict, Any, Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import StaticPool
import time
from datetime import datetime

logger = logging.getLogger(__name__)

# Base for all models
Base = declarative_base()

class Database:
    """Database connection and session manager"""
    
    def __init__(self, database_url: str, echo: bool = False, pool_size: int = 10):
        """Initialize database connection"""
        self.database_url = database_url
        self.echo = echo
        
        # Special handling for SQLite
        if database_url.startswith('sqlite'):
            # SQLite-specific engine configuration
            self.engine = create_engine(
                database_url,
                echo=echo,
                poolclass=StaticPool,
                connect_args={
                    'check_same_thread': False,
                    'timeout': 20
                }
            )
        else:
            # PostgreSQL/other database configuration
            self.engine = create_engine(
                database_url,
                echo=echo,
                pool_size=pool_size,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600
            )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        self._connection_test()
        logger.info(f"Database initialized: {self._get_db_type()}")
    
    def _connection_test(self):
        """Test database connection"""
        try:
            with self.engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            logger.info("Database connection test successful")
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            raise
    
    def _get_db_type(self) -> str:
        """Get database type from URL"""
        if self.database_url.startswith('sqlite'):
            return "SQLite"
        elif self.database_url.startswith('postgresql'):
            return "PostgreSQL"
        elif self.database_url.startswith('mysql'):
            return "MySQL"
        else:
            return "Unknown"
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise
    
    def get_table_info(self) -> Dict[str, Any]:
        """Get information about database tables"""
        inspector = inspect(self.engine)
        tables = inspector.get_table_names()
        
        table_info = {}
        for table_name in tables:
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            
            table_info[table_name] = {
                'columns': len(columns),
                'column_names': [col['name'] for col in columns],
                'indexes': len(indexes),
                'index_names': [idx['name'] for idx in indexes]
            }
        
        return table_info
    
    def backup_database(self, backup_path: str) -> bool:
        """Backup database (SQLite only)"""
        if not self.database_url.startswith('sqlite'):
            logger.error("Backup only supported for SQLite databases")
            return False
        
        try:
            import shutil
            import sqlite3
            
            # Extract database path from URL
            db_path = self.database_url.replace('sqlite:///', '')
            
            # Create backup
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backed up to: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def get_connection_info(self) -> Dict[str, Any]:
        """Get database connection information"""
        return {
            'database_type': self._get_db_type(),
            'database_url': self.database_url,
            'echo_enabled': self.echo,
            'pool_size': getattr(self.engine.pool, 'size', 'N/A'),
            'connection_count': getattr(self.engine.pool, 'checkedout', 'N/A')
        }
    
    def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                # Simple query to test connection
                result = conn.execute("SELECT 1")
                result.fetchone()
                
                response_time = time.time() - start_time
                
                return {
                    'status': 'healthy',
                    'response_time_ms': round(response_time * 1000, 2),
                    'timestamp': datetime.utcnow().isoformat(),
                    'database_type': self._get_db_type()
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'database_type': self._get_db_type()
            }
    
    def execute_migration(self, migration_sql: str) -> bool:
        """Execute a database migration"""
        try:
            with self.engine.connect() as conn:
                # Execute migration in a transaction
                trans = conn.begin()
                try:
                    conn.execute(migration_sql)
                    trans.commit()
                    logger.info("Migration executed successfully")
                    return True
                except Exception as e:
                    trans.rollback()
                    logger.error(f"Migration failed: {e}")
                    raise
                    
        except Exception as e:
            logger.error(f"Migration execution error: {e}")
            return False
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get database performance statistics"""
        try:
            stats = {}
            
            # Get table sizes (SQLite only)
            if self.database_url.startswith('sqlite'):
                with self.get_session() as session:
                    # Get table row counts
                    table_info = self.get_table_info()
                    for table_name in table_info.keys():
                        try:
                            result = session.execute(f"SELECT COUNT(*) FROM {table_name}")
                            count = result.scalar()
                            stats[f"{table_name}_rows"] = count
                        except Exception as e:
                            logger.warning(f"Could not get row count for {table_name}: {e}")
            
            # Connection pool stats
            pool = self.engine.pool
            stats.update({
                'pool_checked_in': getattr(pool, 'checkedin', 'N/A'),
                'pool_checked_out': getattr(pool, 'checkedout', 'N/A'),
                'pool_overflow': getattr(pool, 'overflow', 'N/A'),
                'pool_invalid': getattr(pool, 'invalidated', 'N/A')
            })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting performance stats: {e}")
            return {'error': str(e)}
    
    def close(self):
        """Close database connections"""
        try:
            self.engine.dispose()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database: {e}")

# Global database instance
_database_instance: Optional[Database] = None

def get_database(database_url: Optional[str] = None, 
                echo: bool = False, 
                pool_size: int = 10,
                force_reload: bool = False) -> Database:
    """Get global database instance"""
    global _database_instance
    
    if _database_instance is None or force_reload:
        if not database_url:
            raise ValueError("Database URL must be provided for first initialization")
        _database_instance = Database(database_url, echo, pool_size)
    
    return _database_instance

# Convenience function for session management
@contextmanager
def session_scope(database: Optional[Database] = None) -> Generator[Session, None, None]:
    """Provide a transactional scope around a series of operations"""
    if database is None:
        database = get_database()
    
    with database.get_session() as session:
        yield session
