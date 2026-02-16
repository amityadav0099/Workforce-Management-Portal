from app import app, db
from sqlalchemy import text

def apply_migrations():
    with app.app_context():
        try:
            print("Running manual migrations...")
            
            # 1. Ensure location columns exist
            db.session.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS location VARCHAR(255)"))
            db.session.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS location_out VARCHAR(255)"))
            
            # 2. Upgrade clock columns to TIMESTAMP WITH TIME ZONE
            # We use concatenation (||) to merge CURRENT_DATE and the time value safely
            print("Upgrading clock columns to support seconds and dates...")
            db.session.execute(text("""
                ALTER TABLE attendance 
                ALTER COLUMN clock_in TYPE TIMESTAMP WITH TIME ZONE 
                USING (CURRENT_DATE + clock_in::time),
                ALTER COLUMN clock_out TYPE TIMESTAMP WITH TIME ZONE 
                USING (CURRENT_DATE + clock_out::time);
            """))
            
            # 3. Fix Leaves table
            print("Checking Leaves table columns...")
            db.session.execute(text("ALTER TABLE leaves ADD COLUMN IF NOT EXISTS start_date DATE"))
            db.session.execute(text("ALTER TABLE leaves ADD COLUMN IF NOT EXISTS end_date DATE"))
            
            db.session.commit()
            print("Database migration successful! ✅")
            
        except Exception as e:
            db.session.rollback()
            print(f"Migration failed: {e}")
            print("HINT: Ensure 'pytz' is in requirements.txt before running.")

if __name__ == "__main__":
    apply_migrations()