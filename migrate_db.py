from app import app, db
from sqlalchemy import text

def apply_migrations():
    with app.app_context():
        try:
            print("Running manual migrations...")
            # Fix for Attendance table
            db.session.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS location VARCHAR(255)"))
            
            # Fix for Leaves table (ensuring start_date and end_date exist)
            db.session.execute(text("ALTER TABLE leaves ADD COLUMN IF NOT EXISTS start_date DATE"))
            db.session.execute(text("ALTER TABLE leaves ADD COLUMN IF NOT EXISTS end_date DATE"))
            
            db.session.commit()
            print("Database migration successful! ✅")
        except Exception as e:
            print(f"Migration failed: {e}")

if __name__ == "__main__":
    apply_migrations()