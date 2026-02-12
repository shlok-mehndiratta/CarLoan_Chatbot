"""Initialize the database with the full schema."""
from backend.db import init_db

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized with full schema")