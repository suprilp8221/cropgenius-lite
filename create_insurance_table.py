import sqlite3

# Connect to database
conn = sqlite3.connect('crop_info.db')
cursor = conn.cursor()

# Create insurance_schemes table
cursor.execute('''
CREATE TABLE IF NOT EXISTS insurance_schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_name TEXT NOT NULL,
    scheme_type TEXT NOT NULL,
    coverage_type TEXT NOT NULL,
    base_premium_rate REAL NOT NULL,
    subsidy_percentage REAL NOT NULL,
    max_sum_insured REAL NOT NULL,
    description TEXT,
    eligibility TEXT
)
''')

# Insert popular Indian crop insurance schemes
schemes_data = [
    (
        'PMFBY - Pradhan Mantri Fasal Bima Yojana',
        'Government',
        'Comprehensive',
        2.0,  # 2% for Kharif
        50.0,  # 50% subsidy
        200000,
        'Comprehensive crop insurance covering yield losses due to non-preventable natural risks',
        'All farmers including sharecroppers and tenant farmers'
    ),
    (
        'PMFBY - Rabi Crops',
        'Government',
        'Comprehensive',
        1.5,  # 1.5% for Rabi
        50.0,
        200000,
        'PMFBY scheme for Rabi season crops with lower premium rates',
        'All farmers growing Rabi crops'
    ),
    (
        'Weather Based Crop Insurance',
        'Government',
        'Weather Index',
        3.0,
        40.0,
        150000,
        'Insurance based on weather parameters like rainfall, temperature, humidity',
        'Farmers in areas prone to weather variability'
    ),
    (
        'Private Comprehensive Cover',
        'Private',
        'Comprehensive',
        5.0,
        0.0,
        500000,
        'Full coverage including pre-sowing to post-harvest losses',
        'All farmers, no subsidy available'
    ),
    (
        'Coconut Palm Insurance',
        'Specialized',
        'Tree Insurance',
        4.0,
        25.0,
        100000,
        'Special insurance for coconut and palm tree growers',
        'Coconut and palm farmers'
    ),
    (
        'Horticulture Crop Insurance',
        'Specialized',
        'Comprehensive',
        3.5,
        35.0,
        250000,
        'Coverage for fruits, vegetables, and flower crops',
        'Horticulture farmers'
    )
]

cursor.executemany('''
INSERT INTO insurance_schemes 
(scheme_name, scheme_type, coverage_type, base_premium_rate, subsidy_percentage, 
 max_sum_insured, description, eligibility)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
''', schemes_data)

conn.commit()
print("✓ Insurance schemes table created successfully!")
print(f"✓ Inserted {len(schemes_data)} insurance schemes")

# Display the schemes
cursor.execute("SELECT * FROM insurance_schemes")
schemes = cursor.fetchall()
print("\n📋 Available Insurance Schemes:")
for scheme in schemes:
    print(f"  {scheme[1]} - Premium: {scheme[4]}%, Subsidy: {scheme[5]}%")

conn.close()
