#!/usr/bin/env python
"""
Test Neon Database Connection using DATABASE_URL
Save as: backend/test_neon_connection.py
Run: python test_neon_connection.py
"""

import os
from urllib.parse import urlparse
from dotenv import load_dotenv

load_dotenv()

def test_connection():
    """Test connection to Neon database using DATABASE_URL"""

    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not set in .env")
        return False

    # Parse URL
    result = urlparse(database_url)
    db_name = result.path[1:]  # remove leading /
    db_user = result.username
    db_password = result.password
    db_host = result.hostname
    db_port = result.port

    print("=" * 60)
    print("Testing Neon Database Connection")
    print("=" * 60)

    print(f"\n📋 Configuration:")
    print(f"   DB_NAME: {db_name}")
    print(f"   DB_USER: {db_user}")
    print(f"   DB_HOST: {db_host}")
    print(f"   DB_PORT: {db_port}")
    print(f"   DB_PASSWORD: {'*' * len(db_password) if db_password else '❌ NOT SET'}")

    try:
        import psycopg2

        print("\n🔌 Attempting to connect...")

        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            sslmode='require',
            connect_timeout=10
        )

        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        db_version = cursor.fetchone()[0]

        print("\n✅ SUCCESS! Connected to Neon Database")
        print(f"\n📊 Database Info: {db_version}")

        cursor.close()
        conn.close()

        return True

    except psycopg2.OperationalError as e:
        print("\n❌ CONNECTION FAILED!")
        print(f"\nError: {e}")
        return False

    except ImportError:
        print("\n❌ psycopg2 not installed!")
        print("Run: pip install psycopg2-binary")
        return False

if __name__ == '__main__':
    test_connection()
