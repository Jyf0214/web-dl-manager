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
    """Deletes the oldest 20% of logs from the database."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM logs")
            total_rows = cursor.fetchone()[0]
            
            if total_rows == 0:
                logging.info("No logs to clean up.")
                return

            rows_to_delete = int(total_rows * 0.2)
            
            if rows_to_delete > 0:
                if db_type == 'mysql':
                    cursor.execute(
                        "DELETE FROM logs ORDER BY timestamp ASC LIMIT %s",
                        (rows_to_delete,)
                    )
                elif db_type == 'sqlite':
                    cursor.execute(
                        "DELETE FROM logs WHERE id IN (SELECT id FROM logs ORDER BY timestamp ASC LIMIT ?)",
                        (rows_to_delete,)
                    )
                
                conn.commit()
                logging.info(f"Successfully cleaned up {rows_to_delete} oldest log entries.")
            else:
                logging.info("Not enough log entries to perform a cleanup.")
                
            cursor.close()
    except Exception as e:
        sys.stderr.write(f"Error during log cleanup: {e}\n")
        logging.error(f"Error during log cleanup: {e}")
