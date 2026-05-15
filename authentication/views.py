from django.shortcuts import redirect, render
from django.http import JsonResponse
from aeromiles.db import get_connection
import json

def login_page(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        return handle_login(request, data)

    return render(request, 'authentication/login.html')

def register_page(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        return handle_register(data)
 
    return render(request, 'authentication/register.html')

def handle_login(request, data):
    email = data.get('email').strip()
    password = data.get('password').strip()

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "CALL verifikasi_login(%s, %s)",
            [email, password]
        )

        conn.commit()

        cursor.execute("""
            SELECT email, salutation, first_mid_name, last_name
            FROM PENGGUNA
            WHERE email = %s
        """, [email])

        user = cursor.fetchone()

        cursor.execute("SELECT nomor_member, id_tier FROM MEMBER WHERE email = %s", [email])
        member = cursor.fetchone()

        cursor.execute("SELECT id_staf FROM STAF WHERE email = %s", [email])
        staf = cursor.fetchone()

        if not member and not staf:
            return JsonResponse({'error': 'Akun tidak terdaftar sebagai member atau staf.'}, status=401)

        request.session['email'] = user[0]
        request.session['nama'] = f"{user[1]} {user[2]} {user[3]}"
        request.session['role'] = 'member' if member else 'staf'

        if member:
            # Ambil nama tier
            cursor.execute("SELECT nama FROM TIER WHERE id_tier = %s", [member[1]])
            tier = cursor.fetchone()
            nama_tier = tier[0] if tier else ''

            # Buat singkatan dari first_mid_name dan last_name
            singkatan = (user[2][0] + user[3][0]).upper() if user[2] and user[3] else 'AM'

            request.session['nomor_member'] = member[0]
            request.session['id_tier'] = member[1]
            request.session['nama_tier'] = nama_tier
            request.session['singkatan'] = singkatan
            redirect_url = '/member/dashboard-member/'
        else:
            singkatan = (user[2][0] + user[3][0]).upper() if user[2] and user[3] else 'AM'
            request.session['id_staf'] = staf[0]
            request.session['singkatan'] = singkatan
            redirect_url = '/staf/dashboard-staf/'

        return JsonResponse({'success': True, 'redirect': redirect_url})

    except Exception as e:
        error_msg = str(e).split('\n')[0].strip()
        print(f"ERROR LOGIN: {error_msg}")
        return JsonResponse({'error': error_msg}, status=500)
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

        password = data.get('password')

        # Insert PENGGUNA
        cursor.execute("""
            INSERT INTO PENGGUNA 
            (
                email,
                password,
                salutation,
                first_mid_name,
                last_name,
                country_code,
                mobile_number,
                tanggal_lahir,
                kewarganegaraan
            )
            VALUES
            (
                %s,
                crypt(%s, gen_salt('bf')),
                %s, %s, %s, %s, %s, %s, %s
            )
        """, [
            email,
            password,
            salutation,
            fname,
            lname,
            country_code,
            phone,
            dob,
            nationality
        ])

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