"""
Test: Supabase PostgreSQL Connection via Peewee ORM
Project: AgenticTravelTech
Description: Verifies connectivity to Supabase hosted PostgreSQL database,
checks SSL handshake, executes version query, and tests table creation.
"""

import os
import sys
from pathlib import Path

# Add root directory to path
root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

import env_loader

from playhouse.db_url import parse as parse_db_url
from playhouse.postgres_ext import PostgresqlExtDatabase
import peewee

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

def run_db_test():
    print("=" * 65)
    print("TEST: SUPABASE POSTGRESQL CONNECTION (PEEWEE ORM)")
    print("=" * 65)

    if not DATABASE_URL:
        print("[!] DATABASE_URL is not set.")
        print("Please paste your Supabase connection string into .env")
        print("Format: postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres")
        print("=" * 65)
        return False

    print(f"Connecting using provided DATABASE_URL...")
    
    try:
        db_config = parse_db_url(DATABASE_URL)
        if "sslmode" not in db_config:
            db_config["sslmode"] = "require"
        db_config["autorollback"] = True

        test_db = PostgresqlExtDatabase(**db_config)
        test_db.connect(reuse_if_open=True)
        print("[+] SSL Handshake & Database Connection: SUCCESSFUL")

        # Execute low-level query
        cursor = test_db.execute_sql("SELECT version();")
        version_info = cursor.fetchone()
        print(f"[+] Engine Version: {version_info[0]}")

        # Test model creation
        class HealthCheck(peewee.Model):
            message = peewee.CharField()
            class Meta:
                database = test_db
                table_name = "_connection_test"

        test_db.create_tables([HealthCheck], safe=True)
        print("[+] Table Creation: SUCCESSFUL")

        # Clean up test table
        HealthCheck.drop_table(safe=True)
        print("[+] Table Cleanup: SUCCESSFUL")

        test_db.close()
        print("=" * 65)
        print("[+] All database tests passed successfully.")
        print("=" * 65)
        return True

    except Exception as e:
        err_msg = str(e)
        print(f"\n[-] Database Connection Error: {err_msg}")
        
        # Diagnostic guidance for Supabase pooler
        if "unexpected eof while reading" in err_msg or "SSL error" in err_msg:
            print("\n[Diagnostic Guide]:")
            print("1. Port 6543 vs 5432:")
            print("   Supabase Connection Pooler typically listens on port 6543 (Transaction Mode).")
            print("   Try changing ':5432/' to ':6543/' in .env.")
            print("2. Project Status in Dashboard:")
            print("   If your project was recently created or was inactive, verify in the Supabase Dashboard")
            print("   (https://supabase.com/dashboard/project/srhpxfhtxhqkpexpttqn) that the project status is 'Active'")
            print("   and not 'Paused' or 'Restoring'.")
            print("3. Password Verification:")
            print("   Confirm that your database password matches 'agentictravelai'.")
        
        print("=" * 65)
        return False

if __name__ == "__main__":
    run_db_test()
