from django.shortcuts import redirect, render
from django.http import JsonResponse
from aeromiles.db import get_connection
import json

def login_page(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Cek di PENGGUNA
            cursor.execute("""
                SELECT email, password, salutation, first_mid_name, last_name
                FROM PENGGUNA WHERE email = %s AND password = %s
            """, [email, password])
            user = cursor.fetchone()

            if not user:
                return JsonResponse({'error': 'Email atau password salah.'}, status=401)

            # Cek role: member atau staf?
            cursor.execute("SELECT nomor_member, id_tier FROM MEMBER WHERE email = %s", [email])
            member = cursor.fetchone()

            cursor.execute("SELECT id_staf FROM STAF WHERE email = %s", [email])
            staf = cursor.fetchone()

            if not member and not staf:
                return JsonResponse({'error': 'Akun tidak terdaftar sebagai member atau staf.'}, status=401)

            # Simpan ke Django session
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

    return render(request, 'authentication/login.html')

def logout_view(request):
    request.session.flush()
    return redirect('/auth/login/')