import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aeromiles.settings')
django.setup()

from aeromiles.db import get_connection
from django.contrib.auth.hashers import make_password

conn = get_connection()
cursor = conn.cursor()

try:
    cursor.execute("SELECT email, password FROM PENGGUNA")
    users = cursor.fetchall()
    
    for email, plain_password in users:
        hashed = make_password(plain_password)
        cursor.execute(
            "UPDATE PENGGUNA SET password = %s WHERE email = %s",
            [hashed, email]
        )
    
    conn.commit()
    print(f"✅ Berhasil update {len(users)} password.")

except Exception as e:
    conn.rollback()
    print(f"❌ Error: {e}")

finally:
    cursor.close()
    conn.close()