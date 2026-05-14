from django.shortcuts import render
from django.http import JsonResponse
from aeromiles.db import get_connection
import json
from django.views.decorators.csrf import csrf_exempt

def redeem_hadiah(request):
    # Hardcode dulu, nanti diganti session login
    email_member = 'andika.pratama@mail.com'
    
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
        email_member = 'andika.pratama@mail.com'
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

def beli_package(request):
    return render(request, 'member/beli-package.html')

def info_tier(request):
    return render(request, 'member/info-tier.html')

def transfer_miles(request):
    return render(request, 'member/transfer-miles.html')

def claim_member(request):
    return render(request, 'member/claim-member.html')

def profil(request):
    return render(request, 'member/profil.html')

def dashboard_member(request):
    return render(request, 'member/dashboard-member.html')

def identitas(request):
    return render(request, 'member/identitas.html')