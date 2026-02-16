from app import app, db
from sqlalchemy import text

def apply_migrations():
    with app.app_context():
        try:
            print("Running manual migrations...")
            
            # --- ATTENDANCE TABLE FIXES ---
            # 1. Ensure 'location' (clock-in) exists
            db.session.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS location VARCHAR(255)"))
            
            # 2. Add 'location_out' for clock-out tracking
            db.session.execute(text("ALTER TABLE attendance ADD COLUMN IF NOT EXISTS location_out VARCHAR(255)"))
            
            # 3. CONVERT TIME TO TIMESTAMP (Crucial for PostgreSQL/Render)
            # This allows the H:M:S duration math to work without crashing.
            # Using 'USING' handles the data conversion from old format.
            print("Upgrading clock columns to support seconds and dates...")
            db.session.execute(text("""
                ALTER TABLE attendance 
                ALTER COLUMN clock_in TYPE TIMESTAMP WITH TIME ZONE USING (CURRENT_DATE + clock_in),
                ALTER COLUMN clock_out TYPE TIMESTAMP WITH TIME ZONE USING (CURRENT_DATE + clock_out)
            """))
            
            # --- LEAVES TABLE FIXES ---
            print("Checking Leaves table columns...")
            db.session.execute(text("ALTER TABLE leaves ADD COLUMN IF NOT EXISTS start_date DATE"))
            db.session.execute(text("ALTER TABLE leaves ADD COLUMN IF NOT EXISTS end_date DATE"))
            
            db.session.commit()
            print("Database migration successful! ✅")
            
        except Exception as e:
            db.session.rollback()
            print(f"Migration failed: {e}")
            print("Note: If the error says 'column already exists', you can ignore it.")

if __name__ == "__main__":
    apply_migrations()