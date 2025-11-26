import psycopg2
from django.conf import settings
import sys

def cleanup_test_db():
    # Get database settings from Django
    db_settings = settings.DATABASES['default']
    
    # Connect to the default 'postgres' database to drop the test database
    conn = psycopg2.connect(
        dbname='postgres',
        user=db_settings['USER'],
        password=db_settings['PASSWORD'],
        host=db_settings['HOST'],
        port=db_settings['PORT']
    )
    conn.autocommit = True
    
    try:
        with conn.cursor() as cur:
            # Terminate all connections to the test database
            print("Terminating active connections to test_neondb...")
            cur.execute("""
                SELECT pg_terminate_backend(pg_stat_activity.pid)
                FROM pg_stat_activity
                WHERE pg_stat_activity.datname = 'test_neondb'
                AND pid <> pg_backend_pid();
            """)
            print(f"Terminated {cur.rowcount} connections.")
            
            # Drop the test database
            print("Dropping test database...")
            cur.execute("DROP DATABASE IF EXISTS test_neondb")
            print("Test database dropped successfully.")
            
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        conn.close()
    
    return True

if __name__ == "__main__":
    try:
        # Configure Django settings
        import os
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'FitnessTrackerApp_backend.settings')
        import django
        django.setup()
        
        if cleanup_test_db():
            print("Cleanup completed successfully.")
            sys.exit(0)
        else:
            print("Cleanup failed.")
            sys.exit(1)
            
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)
