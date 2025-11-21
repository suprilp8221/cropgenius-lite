import sqlite3

print("=" * 60)
print("CREATE PREDICTION HISTORY TABLE")
print("=" * 60)

try:
    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()
    
    # Create prediction_history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            nitrogen REAL NOT NULL,
            phosphorus REAL NOT NULL,
            potassium REAL NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            ph REAL NOT NULL,
            rainfall REAL NOT NULL,
            predicted_crop TEXT NOT NULL,
            location TEXT,
            prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    """)
    
    conn.commit()
    print("\n✅ Successfully created 'prediction_history' table!")
    print("\nTable structure:")
    print("  - id (auto-increment)")
    print("  - username")
    print("  - nitrogen, phosphorus, potassium")
    print("  - temperature, humidity, ph, rainfall")
    print("  - predicted_crop")
    print("  - location (optional)")
    print("  - prediction_date (timestamp)")
    
    # Check if table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='prediction_history'")
    result = cursor.fetchone()
    
    if result:
        print("\n✅ Table verified successfully!")
    
    conn.close()
    print("\n" + "=" * 60)
    
except Exception as e:
    print(f"\n❌ Error: {str(e)}")
