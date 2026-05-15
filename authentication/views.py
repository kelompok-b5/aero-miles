from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password, check_password
from aeromiles.db import get_connection
import json

def login_page(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        action = data.get('action', 'login')

        if action == 'register':
            return handle_register(data)
        else:
            return handle_login(request, data)

    return render(request, 'authentication/login.html')


def handle_login(request, data):
    email = data.get('email')
    password = data.get('password')

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT email, password, salutation, first_mid_name, last_name
            FROM PENGGUNA WHERE email = %s
        """, [email])
        user = cursor.fetchone()

        if not user:
            return JsonResponse({'error': 'Email atau password salah.'}, status=401)

        if not check_password(password, user[1]):
            return JsonResponse({'error': 'Email atau password salah.'}, status=401)

        cursor.execute("SELECT nomor_member, id_tier FROM MEMBER WHERE email = %s", [email])
        member = cursor.fetchone()

        cursor.execute("SELECT id_staf FROM STAF WHERE email = %s", [email])
        staf = cursor.fetchone()

        if not member and not staf:
            return JsonResponse({'error': 'Akun tidak terdaftar sebagai member atau staf.'}, status=401)

        request.session['email'] = user[0]
        request.session['nama'] = f"{user[2]} {user[3]} {user[4]}"
        request.session['role'] = 'member' if member else 'staf'

        if member:
            request.session['nomor_member'] = member[0]
            request.session['id_tier'] = member[1]
            redirect_url = '/member/dashboard-member/'
        else:
            request.session['id_staf'] = staf[0]
            redirect_url = '/staf/dashboard-staf/'

        return JsonResponse({'success': True, 'redirect': redirect_url})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        cursor.close()
        conn.close()


def handle_register(data):
    email       = data.get('email')
    password    = data.get('password')
    salutation  = data.get('salutation')
    fname       = data.get('first_mid_name')
    lname       = data.get('last_name')
    country_code= data.get('country_code')
    phone       = data.get('mobile_number')
    dob         = data.get('tanggal_lahir')
    nationality = data.get('kewarganegaraan')
    role        = data.get('role')
    kode_maskapai = data.get('kode_maskapai')

    conn = get_connection()
    cursor = conn.cursor()
    try:
        # Cek email sudah ada otomatis melalui trigger
        # Validasi maskapai kalau staf
        if role == 'staf':
            cursor.execute("SELECT kode_maskapai FROM MASKAPAI WHERE kode_maskapai = %s", [kode_maskapai])
            if not cursor.fetchone():
                return JsonResponse({'error': 'Kode maskapai tidak valid.'}, status=400)

        hashed = make_password(password)

        # Insert PENGGUNA
        cursor.execute("""
            INSERT INTO PENGGUNA 
            (email, password, salutation, first_mid_name, last_name, country_code, mobile_number, tanggal_lahir, kewarganegaraan)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, [email, hashed, salutation, fname, lname, country_code, phone, dob, nationality])

        if role == 'member':
            cursor.execute("""
                INSERT INTO MEMBER (email, tanggal_bergabung, id_tier)
                VALUES (%s, CURRENT_DATE, 'T001')
            """, [email])
        elif role == 'staf':
            cursor.execute("""
                INSERT INTO STAF (email, kode_maskapai)
                VALUES (%s, %s)
            """, [email, kode_maskapai])

        conn.commit()
        return JsonResponse({'success': True, 'message': 'Registrasi berhasil! Silakan login.'})

    except Exception as e:
        conn.rollback()
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        cursor.close()
        conn.close()


def logout_view(request):
    request.session.flush()
    return redirect('/auth/login/')