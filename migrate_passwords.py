import sqlite3
import bcrypt

print("=" * 60)
print("PASSWORD MIGRATION SCRIPT")
print("=" * 60)
print("\nThis script will hash all existing plain-text passwords in the database.")
print("⚠️  WARNING: This is a one-way operation. Make a backup first if needed!\n")

response = input("Do you want to continue? (yes/no): ").strip().lower()

if response != 'yes':
    print("❌ Migration cancelled.")
    exit()

try:
    # Connect to database
    conn = sqlite3.connect("crop_info.db")
    cursor = conn.cursor()
    
    # Migrate user passwords
    print("\n📝 Migrating user passwords...")
    cursor.execute("SELECT username, password FROM users")
    users = cursor.fetchall()
    
    user_count = 0
    for username, password in users:
        # Check if password is already hashed (bcrypt hashes start with $2b$)
        if isinstance(password, bytes) and password.startswith(b'$2b$'):
            print(f"  ⏭️  Skipping {username} (already hashed)")
            continue
        
        # Convert to string if bytes
        if isinstance(password, bytes):
            password = password.decode('utf-8')
        
        # Hash the password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Update in database
        cursor.execute("UPDATE users SET password=? WHERE username=?", (hashed, username))
        print(f"  ✅ Hashed password for user: {username}")
        user_count += 1
    
    # Migrate admin passwords
    print("\n🔐 Migrating admin passwords...")
    cursor.execute("SELECT username, password FROM admin")
    admins = cursor.fetchall()
    
    admin_count = 0
    for username, password in admins:
        # Check if password is already hashed
        if isinstance(password, bytes) and password.startswith(b'$2b$'):
            print(f"  ⏭️  Skipping {username} (already hashed)")
            continue
        
        # Convert to string if bytes
        if isinstance(password, bytes):
            password = password.decode('utf-8')
        
        # Hash the password
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Update in database
        cursor.execute("UPDATE admin SET password=? WHERE username=?", (hashed, username))
        print(f"  ✅ Hashed password for admin: {username}")
        admin_count += 1
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 60)
    print("✨ MIGRATION COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print(f"  👥 Users migrated: {user_count}")
    print(f"  🔐 Admins migrated: {admin_count}")
    print("\n💡 All passwords are now securely hashed!")
    print("🔒 Users can login with their existing passwords.\n")

except Exception as e:
    print(f"\n❌ Error during migration: {str(e)}")
    print("⚠️  Database was not modified.")
