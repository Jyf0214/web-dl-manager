import logging
import datetime
from .database import get_db_connection, db_type
import sys

class MySQLLogHandler(logging.Handler):
    def emit(self, record):
        # Safeguard against infinite recursion if DB logging fails
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # Use current_timestamp() for DATETIME column
                # The 'timestamp' column in MySQL is DATETIME, which doesn't store timezone info.
                # Python's record.created is a float timestamp, so convert it to a datetime object
                # and then format it for MySQL, or let MySQL handle the default.
                # Here, we'll let the database handle the default timestamp.
                if db_type == 'mysql':
                    cursor.execute(
                        """
                        INSERT INTO logs (level, logger_name, message, pathname, lineno)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            record.levelname,
                            record.name,
                            self.format(record), # Use formatted message
                            record.pathname,
                            record.lineno
                        )
                    )
                elif db_type == 'sqlite':
                    cursor.execute(
                        """
                        INSERT INTO logs (level, logger_name, message, pathname, lineno)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            record.levelname,
                            record.name,
                            self.format(record), # Use formatted message
                            record.pathname,
                            record.lineno
                        )
                    )
                conn.commit()
                cursor.close()
        except Exception as e:
            # If we can't log to DB, print to stderr to ensure visibility
            db_type_str = "MySQL" if db_type == 'mysql' else "SQLite" if db_type == 'sqlite' else "Unknown"
            sys.stderr.write(f"Failed to log to {db_type_str}: {e}\n")
            sys.stderr.write(f"Original log record: {self.format(record)}\n")

# Maximum log table size in MB
MAX_LOG_TABLE_SIZE_MB = 500
MAX_LOG_TABLE_SIZE_BYTES = MAX_LOG_TABLE_SIZE_MB * 1024 * 1024

def cleanup_old_logs():
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            if db_type == 'mysql':
                # Get current table size in bytes
                cursor.execute(f"""
                    SELECT data_length + index_length
                    FROM information_schema.tables
                    WHERE table_schema = DATABASE() AND table_name = 'logs';
                """)
                result = cursor.fetchone()
                current_size_bytes = result[0] if result else 0
                
                if current_size_bytes > MAX_LOG_TABLE_SIZE_BYTES:
                    logger.warning(f"Log table size ({current_size_bytes / (1024*1024):.2f}MB) exceeds limit ({MAX_LOG_TABLE_SIZE_MB}MB). Cleaning up old logs...")
                    
                    # Calculate how many rows to delete.
                    # This is a rough estimation and might need fine-tuning based on average log entry size.
                    # For simplicity, we'll delete a percentage of the oldest logs.
                    # Or, even better, delete until the size is below the threshold.
                    
                    # Find the 'id' of the log entry that is roughly at the point where we want to truncate
                    # This is a more robust way to delete by size, though still an approximation.
                    # A more precise method would involve iterating and checking size.
                    # For now, let's target deleting a chunk (e.g., 20% of the table)
                    
                    cursor.execute("SELECT COUNT(*) FROM logs")
                    total_rows = cursor.fetchone()[0]
                    
                    if total_rows > 0:
                        rows_to_delete = int(total_rows * 0.2) # Delete 20% of the oldest logs
                        if rows_to_delete > 0:
                            cursor.execute(f"""
                                DELETE FROM logs
                                ORDER BY timestamp ASC
                                LIMIT %s;
                            """, (rows_to_delete,))
                            conn.commit()
                            logger.info(f"Cleaned up {rows_to_delete} oldest log entries.")
                            
            elif db_type == 'sqlite':
                # For SQLite, we'll use a simpler approach based on row count
                cursor.execute("SELECT COUNT(*) FROM logs")
                total_rows = cursor.fetchone()[0]
                
                # If we have more than 10000 rows, delete the oldest 20%
                if total_rows > 10000:
                    logger.warning(f"Log table has {total_rows} rows. Cleaning up old logs...")
                    rows_to_delete = int(total_rows * 0.2) # Delete 20% of the oldest logs
                    if rows_to_delete > 0:
                        cursor.execute("""
                            DELETE FROM logs
                            WHERE id IN (
                                SELECT id FROM logs
                                ORDER BY timestamp ASC
                                LIMIT ?
                            )
                        """, (rows_to_delete,))
                        conn.commit()
                        logger.info(f"Cleaned up {rows_to_delete} oldest log entries.")
                        
            cursor.close()
    except Exception as e:
        sys.stderr.write(f"Error during log cleanup: {e}\n")
