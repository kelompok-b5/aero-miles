from django.shortcuts import render
from django.http import JsonResponse
from aeromiles.db import get_connection
from django.contrib.auth.hashers import check_password, make_password
import json
from django.views.decorators.csrf import csrf_exempt

def redeem_hadiah(request):
    # Hardcode dulu, nanti diganti session login
    email_member = request.session.get('email')

    conn = get_connection()
    cursor = conn.cursor()
    
    # Ambil award_miles member
    cursor.execute("""
        SELECT award_miles FROM MEMBER WHERE email = %s
    """, [email_member])
    member = cursor.fetchone()
    award_miles = member[0] if member else 0
    
    # Ambil katalog hadiah yang masih valid
    cursor.execute("""
        SELECT h.kode_hadiah, h.nama, h.miles, h.deskripsi,
               h.valid_start_date, h.program_end, p.id,
               m.nama_mitra
        FROM HADIAH h
        JOIN PENYEDIA p ON h.id_penyedia = p.id
        LEFT JOIN MITRA m ON m.id_penyedia = p.id
        WHERE h.program_end >= CURRENT_DATE
          AND h.valid_start_date <= CURRENT_DATE
        ORDER BY h.kode_hadiah
    """)
    hadiah_rows = cursor.fetchall()
    hadiah = [
        {
            'kode': r[0],
            'nama': r[1],
            'miles': r[2],
            'desc': r[3],
            'start': str(r[4]),
            'end': str(r[5]),
            'id_penyedia': r[6],
            'penyedia': r[7] or '-',
        }
        for r in hadiah_rows
    ]

    # Ambil riwayat redeem member
    cursor.execute("""
        SELECT h.nama, r.timestamp, h.miles
        FROM REDEEM r
        JOIN HADIAH h ON r.kode_hadiah = h.kode_hadiah
        WHERE r.email_member = %s
        ORDER BY r.timestamp DESC
    """, [email_member])
    riwayat_rows = cursor.fetchall()
    riwayat = [
        {
            'nama': r[0],
            'timestamp': str(r[1])[:16],
            'miles': r[2],
        }
        for r in riwayat_rows
    ]

    cursor.close()
    conn.close()

    return render(request, 'member/redeem-hadiah.html', {
        'award_miles': award_miles,
        'hadiah_json': json.dumps(hadiah),
        'riwayat_json': json.dumps(riwayat),
    })

@csrf_exempt
def redeem_hadiah_post(request):
    if request.method == 'POST':
        email_member = request.session.get('email')
        data = json.loads(request.body)
        kode_hadiah = data.get('kode_hadiah')

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Langsung insert — trigger yang handle validasi & potong miles
            cursor.execute("""
                INSERT INTO REDEEM (email_member, kode_hadiah)
                VALUES (%s, %s)
            """, [email_member, kode_hadiah])

            # Ambil sisa miles setelah trigger jalan
            cursor.execute("SELECT award_miles FROM MEMBER WHERE email = %s", [email_member])
            sisa_miles = cursor.fetchone()[0]

            conn.commit()
            return JsonResponse({'success': True, 'sisa_miles': sisa_miles})

        except Exception as e:
            conn.rollback()
            # Pesan error dari trigger (RAISE EXCEPTION) akan masuk sini
            return JsonResponse({'error': str(e)}, status=400)
        finally:
            cursor.close()
            conn.close()

@csrf_exempt
def beli_package(request):
    email_member = request.session.get('email')  # ambil dari session

    conn = get_connection()
    cursor = conn.cursor()

    # Ambil award_miles member
    cursor.execute("SELECT award_miles FROM MEMBER WHERE email = %s", [email_member])
    member = cursor.fetchone()
    award_miles = member[0] if member else 0

    # Ambil katalog package
    cursor.execute("""
        SELECT id, jumlah_award_miles, harga_paket
        FROM AWARD_MILES_PACKAGE
        ORDER BY harga_paket
    """)
    package_rows = cursor.fetchall()
    packages = [
        {
            'id': r[0],
            'jumlah_award_miles': r[1],
            'harga_paket': float(r[2]),
        }
        for r in package_rows
    ]

    # Ambil riwayat pembelian member
    cursor.execute("""
        SELECT m.id_award_miles_package, a.jumlah_award_miles, a.harga_paket, m.timestamp
        FROM MEMBER_AWARD_MILES_PACKAGE m
        JOIN AWARD_MILES_PACKAGE a ON m.id_award_miles_package = a.id
        WHERE m.email_member = %s
        ORDER BY m.timestamp DESC
    """, [email_member])
    riwayat_rows = cursor.fetchall()
    riwayat = [
        {
            'id': r[0],
            'jumlah_award_miles': r[1],
            'harga_paket': float(r[2]),
            'timestamp': str(r[3])[:19],
        }
        for r in riwayat_rows
    ]

    cursor.close()
    conn.close()

    return render(request, 'member/beli-package.html', {
        'award_miles': award_miles,
        'packages_json': json.dumps(packages),
        'riwayat_json': json.dumps(riwayat),
    })


@csrf_exempt
def beli_package_post(request):
    if request.method == 'POST':
        email_member = request.session.get('email')
        data = json.loads(request.body)
        id_package = data.get('id_package')

        conn = get_connection()
        cursor = conn.cursor()
        try:
            # Insert ke MEMBER_AWARD_MILES_PACKAGE
            # trigger sync_miles_after_package otomatis nambah award_miles
            cursor.execute("""
                INSERT INTO MEMBER_AWARD_MILES_PACKAGE (id_award_miles_package, email_member)
                VALUES (%s, %s)
            """, [id_package, email_member])

            # Ambil sisa miles setelah trigger jalan
            cursor.execute("SELECT award_miles FROM MEMBER WHERE email = %s", [email_member])
            award_miles_baru = cursor.fetchone()[0]

            conn.commit()
            return JsonResponse({'success': True, 'award_miles': award_miles_baru})

        except Exception as e:
            conn.rollback()
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            cursor.close()
            conn.close()

def info_tier(request):
    return render(request, 'member/info-tier.html')

def transfer_miles(request):
    return render(request, 'member/transfer-miles.html')

def claim_member(request):
    return render(request, 'member/claim-member.html')

@csrf_exempt
def profil(request):
    """
    Menampilkan data detail profil pada form halaman profil.html menggunakan Raw SQL.
    """
    # Simulasi email dari session login
    email_member = request.session.get('email')

    conn = get_connection() # Menggunakan connection bawaan Django
    cursor = conn.cursor()
    
    try:
        # Query menggabungkan data personal (PENGGUNA) dan data keanggotaan (MEMBER)
        cursor.execute("""
            SELECT 
                p.email, 
                p.salutation, 
                p.first_mid_name, 
                p.last_name, 
                p.kewarganegaraan, 
                p.country_code,
                p.mobile_number, 
                p.tanggal_lahir, 
                m.nomor_member,
                m.tanggal_bergabung
            FROM PENGGUNA p
            JOIN MEMBER m ON p.email = m.email
            WHERE p.email = %s
        """, [email_member])
        
        row = cursor.fetchone()
        
        member_data = {}
        if row:
            member_data = {
                'email':            row[0],
                'salutation':       row[1],
                'first_mid_name':   row[2],
                'last_name':        row[3],
                'kewarganegaraan':  row[4],
                'country_code':     row[5],
                'mobile_number':    row[6],
                # Mengubah object date menjadi string format YYYY-MM-DD agar dibaca oleh <input type="date">
                'tanggal_lahir':    row[7].strftime('%Y-%m-%d') if row[7] else '',
                'nomor_member':     row[8],
                'tanggal_bergabung': row[9].strftime('%Y-%m-%d') if row[9] else '',
            }
        
        context = {
            'member': member_data
        }
        return render(request, 'member/profil.html', context)

    except Exception as e:
        print(f"=== ERROR: {e}")
        return render(request, 'member/profil.html', {'error': str(e)})
    
    finally:
        cursor.close()
        conn.close()

@csrf_exempt
def update_profil(request):

    email_member = request.session.get('email')

    conn = get_connection()
    cursor = conn.cursor()

    try:

        salutation = request.POST.get('salutation')
        first_mid_name = request.POST.get('first_mid_name')
        last_name = request.POST.get('last_name')
        kewarganegaraan = request.POST.get('kewarganegaraan')
        country_code = request.POST.get('country_code')
        mobile_number = request.POST.get('mobile_number')
        tanggal_lahir = request.POST.get('tanggal_lahir')

        # =========================
        # AMBIL DATA LAMA
        # =========================
        cursor.execute("""
            SELECT
                salutation,
                first_mid_name,
                last_name,
                kewarganegaraan,
                country_code,
                mobile_number,
                tanggal_lahir
            FROM PENGGUNA
            WHERE email = %s
        """, [email_member])

        old_data = cursor.fetchone()

        if old_data:

            old_tanggal_lahir = (
                old_data[6].strftime('%Y-%m-%d')
                if old_data[6]
                else ''
            )

            # =========================
            # CEK APAKAH ADA PERUBAHAN
            # =========================
            if (
                old_data[0] == salutation and
                old_data[1] == first_mid_name and
                old_data[2] == last_name and
                old_data[3] == kewarganegaraan and
                old_data[4] == country_code and
                old_data[5] == mobile_number and
                old_tanggal_lahir == tanggal_lahir
            ):

                return JsonResponse({
                    'success': False,
                    'message': 'Tidak ada perubahan data'
                })

        # =========================
        # UPDATE DATA
        # =========================
        cursor.execute("""
            UPDATE PENGGUNA
            SET
                salutation = %s,
                first_mid_name = %s,
                last_name = %s,
                kewarganegaraan = %s,
                country_code = %s,
                mobile_number = %s,
                tanggal_lahir = %s
            WHERE email = %s
        """, [
            salutation,
            first_mid_name,
            last_name,
            kewarganegaraan,
            country_code,
            mobile_number,
            tanggal_lahir,
            email_member
        ])

        conn.commit()

        return JsonResponse({
            'success': True,
            'message': 'Profil berhasil diperbarui'
        })

    except Exception as e:

        conn.rollback()

        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

    finally:
        cursor.close()

@csrf_exempt
def ubah_password(request):

    email_member = request.session.get('email')

    conn = get_connection()
    cursor = conn.cursor()

    try:

        data = json.loads(request.body)

        password_lama = data.get('password_lama')
        password_baru = data.get('password_baru')

        # ambil hash password sekarang
        cursor.execute("""
            SELECT password
            FROM PENGGUNA
            WHERE email = %s
        """, [email_member])

        row = cursor.fetchone()

        if not row:
            return JsonResponse({
                'success': False,
                'message': 'User tidak ditemukan'
            }, status=404)

        hashed_password = row[0]

        # verify password lama
        if not check_password(password_lama, hashed_password):

            return JsonResponse({
                'success': False,
                'message': 'Password lama salah'
            }, status=400)

        # hash password baru
        new_hashed_password = make_password(password_baru)

        # update DB
        cursor.execute("""
            UPDATE PENGGUNA
            SET password = %s
            WHERE email = %s
        """, [
            new_hashed_password,
            email_member
        ])

        conn.commit()

        return JsonResponse({
            'success': True,
            'message': 'Password berhasil diubah'
        })

    except Exception as e:

        conn.rollback()

        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

    finally:
        cursor.close()
        conn.close()

def dashboard_member(request):
    email_member = request.session.get('email')

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            SELECT 
                p.email,
                p.first_mid_name,
                p.last_name,
                p.salutation,
                p.kewarganegaraan,
                p.tanggal_lahir,
                m.tanggal_bergabung,
                m.award_miles,
                m.total_miles,
                m.nomor_member,
                m.id_tier,
                t.nama AS nama_tier
            FROM PENGGUNA p
            JOIN MEMBER m ON p.email = m.email
            JOIN tier t ON m.id_tier = t.id_tier
            WHERE p.email = %s
        """, [email_member])

        member_row = cursor.fetchone()

        member_data = {}
        if member_row:
            member_data = {
                'email':          member_row[0],
                'first_mid_name': member_row[1],
                'last_name':      member_row[2],
                'salutation':     member_row[3],
                # nama_lengkap digabung: salutation + first_mid_name + last_name
                'nama_lengkap':   f"{member_row[3]} {member_row[1]} {member_row[2]}",
                'kewarganegaraan': member_row[4],
                'tgl_lahir':      str(member_row[5]),
                'tgl_bergabung':  str(member_row[6]),
                'award_miles':    member_row[7],
                'total_miles':    member_row[8],
                'nomor_member':   member_row[9],
                'id_tier':        member_row[10],
                'nama_tier':      member_row[11]
            }

        # Query transaksi — pakai lowercase karena PostgreSQL
        # fold identifier ke lowercase kecuali dibuat dengan quotes
        cursor.execute("""
            SELECT 'redeem' AS type, h.nama, r.timestamp, -h.miles AS amount
            FROM redeem r
            JOIN hadiah h ON r.kode_hadiah = h.kode_hadiah
            WHERE r.email_member = %s

            UNION ALL

            SELECT 'package' AS type, 'Pembelian Paket Miles' AS nama, m.timestamp, a.jumlah_award_miles AS amount
            FROM member_award_miles_package m
            JOIN award_miles_package a ON m.id_award_miles_package = a.id
            WHERE m.email_member = %s

            ORDER BY timestamp DESC
            LIMIT 5
        """, [email_member, email_member])

        tx_rows = cursor.fetchall()
        transactions = [
            {
                'type':   r[0],
                'label':  f"{r[1]} ({str(r[2])[:16]})",
                'time':   str(r[2])[:16],
                'amount': r[3],
            }
            for r in tx_rows
        ]

        context = {
            'member':            member_data,
            'transactions_json': json.dumps(transactions),
        }
        return render(request, 'member/dashboard-member.html', context)

    except Exception as e:
        print("=== ERROR:", e)  # tambah ini supaya error kelihatan
        context = {'error': str(e)}
        return render(request, 'member/dashboard-member.html', context)
    finally:
        cursor.close()
        conn.close()

def identitas(request):
    return render(request, 'member/identitas.html')