from pyexpat.errors import messages

from django.shortcuts import redirect, render
from django.http import JsonResponse
from aeromiles.db import get_connection
import json
from django.views.decorators.csrf import csrf_exempt

def redeem_hadiah(request):
    if not request.session.get('email') or request.session.get('role') != 'member':
        return redirect('/auth/login/')
    
    email_member = request.session.get('email')
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT award_miles FROM MEMBER WHERE email = %s
    """, [email_member])
    member = cursor.fetchone()
    award_miles = member[0] if member else 0

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
            # Langsung insert, trigger yang bakal handle validasi & potong miles
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
    if not request.session.get('email') or request.session.get('role') != 'member':
        return redirect('/auth/login/')

    email_member = request.session.get('email')

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
    if not request.session.get('email') or request.session.get('role') != 'member':
        return redirect('/auth/login/')

    email_member = request.session.get('email')

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id_tier, nama, minimal_frekuensi_terbang, minimal_tier_miles
        FROM TIER
        ORDER BY minimal_tier_miles ASC
    """)
    tier_rows = cursor.fetchall()
    tiers = [
        {
            'id_tier': r[0],
            'nama': r[1],
            'minimal_frekuensi_terbang': r[2],
            'minimal_tier_miles': r[3],
        }
        for r in tier_rows
    ]

    cursor.execute("""
        SELECT m.id_tier, m.total_miles
        FROM MEMBER m
        WHERE m.email = %s
    """, [email_member])
    member = cursor.fetchone()
    id_tier_sekarang = member[0]
    total_miles = member[1]

    cursor.close()
    conn.close()

    return render(request, 'member/info-tier.html', {
        'tiers_json': json.dumps(tiers),
        'id_tier_sekarang': id_tier_sekarang,
        'total_miles': total_miles,
    })

# CLAIM MISSING MILES 

def claim_view(request):
    email = request.session['email']
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT award_miles FROM MEMBER WHERE email = %s", (email,))
        member = cur.fetchone()

        # Ambil semua maskapai & bandara untuk dropdown
        cur.execute("SELECT kode_maskapai, nama_maskapai FROM MASKAPAI")
        maskapai_list = cur.fetchall()
        cur.execute("SELECT iata_code, nama, kota FROM BANDARA")
        bandara_list = cur.fetchall()

        # Ambil riwayat klaim member
        filter_status = request.GET.get('status', '')
        if filter_status:
            cur.execute("""
                SELECT id, maskapai, bandara_asal, bandara_tujuan, tanggal_penerbangan,
                       flight_number, kelas_kabin, status_penerimaan, timestamp
                FROM CLAIM_MISSING_MILES
                WHERE email_member = %s AND status_penerimaan = %s
                ORDER BY timestamp DESC
            """, (email, filter_status))
        else:
            cur.execute("""
                SELECT id, maskapai, bandara_asal, bandara_tujuan, tanggal_penerbangan,
                       flight_number, kelas_kabin, status_penerimaan, timestamp
                FROM CLAIM_MISSING_MILES
                WHERE email_member = %s
                ORDER BY timestamp DESC
            """, (email,))
        klaim_list = cur.fetchall()

        return render(request, 'claim-member.html', {
            'member': member,
            'klaim_list': klaim_list,
            'maskapai_list': maskapai_list,
            'bandara_list': bandara_list,
            'filter_status': filter_status,
        })
    finally:
        cur.close()
        conn.close()


def claim_create(request):
    if request.method != 'POST':
        return redirect('member:claim-member')

    email = request.session['email']
    data = (
        email,
        request.POST.get('maskapai'),
        request.POST.get('bandara_asal'),
        request.POST.get('bandara_tujuan'),
        request.POST.get('tanggal_penerbangan'),
        request.POST.get('flight_number'),
        request.POST.get('nomor_tiket'),
        request.POST.get('kelas_kabin'),
        request.POST.get('pnr'),
    )

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO CLAIM_MISSING_MILES
                (email_member, maskapai, bandara_asal, bandara_tujuan,
                 tanggal_penerbangan, flight_number, nomor_tiket, kelas_kabin, pnr)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, data)
        conn.commit()
        messages.success(request, 'Klaim berhasil diajukan! Status: Menunggu verifikasi.')
    except Exception as e:
        conn.rollback()
        # Pesan error dari PostgreSQL
        messages.error(request, f'Gagal mengajukan klaim: {e}')
    finally:
        cur.close()
        conn.close()

    return redirect('member:claim-member')


def claim_edit(request, klaim_id):
    if request.method != 'POST':
        return redirect('member:claim-member')

    email = request.session['email']
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id FROM CLAIM_MISSING_MILES
            WHERE id = %s AND email_member = %s AND status_penerimaan = 'Menunggu'
        """, (klaim_id, email))
        if not cur.fetchone():
            messages.error(request, 'Klaim tidak dapat diedit.')
            return redirect('member:claim-member')

        cur.execute("""
            UPDATE CLAIM_MISSING_MILES SET
                maskapai = %s, bandara_asal = %s, bandara_tujuan = %s,
                tanggal_penerbangan = %s, flight_number = %s,
                nomor_tiket = %s, kelas_kabin = %s, pnr = %s
            WHERE id = %s AND email_member = %s
        """, (
            request.POST.get('maskapai'),
            request.POST.get('bandara_asal'),
            request.POST.get('bandara_tujuan'),
            request.POST.get('tanggal_penerbangan'),
            request.POST.get('flight_number'),
            request.POST.get('nomor_tiket'),
            request.POST.get('kelas_kabin'),
            request.POST.get('pnr'),
            klaim_id, email
        ))
        conn.commit()
        messages.success(request, f'Klaim CLM-{str(klaim_id).zfill(4)} berhasil diperbarui.')
    except Exception as e:
        conn.rollback()
        messages.error(request, f'Gagal memperbarui klaim: {e}')
    finally:
        cur.close()
        conn.close()

    return redirect('member:claim-member')
r
def claim_delete(request, klaim_id):
    if request.method != 'POST':
        return redirect('member:claim-member')

    email = request.session['email']
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM CLAIM_MISSING_MILES
            WHERE id = %s AND email_member = %s AND status_penerimaan = 'Menunggu'
        """, (klaim_id, email))
        conn.commit()
        messages.success(request, f'Klaim CLM-{str(klaim_id).zfill(4)} berhasil dibatalkan.')
    except Exception as e:
        conn.rollback()
        messages.error(request, f'Gagal membatalkan klaim: {e}')
    finally:
        cur.close()
        conn.close()

    return redirect('member:claim-member')


# TRANSFER MILES 
def transfer_view(request):
    email = request.session['email']
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT award_miles FROM MEMBER WHERE email = %s", (email,))
        member = cur.fetchone()

        cur.execute("""
            SELECT t.timestamp,
                   CASE WHEN t.email_member_1 = %s
                        THEN p2.first_mid_name || ' ' || p2.last_name
                        ELSE p1.first_mid_name || ' ' || p1.last_name END AS nama_lawan,
                   CASE WHEN t.email_member_1 = %s
                        THEN t.email_member_2
                        ELSE t.email_member_1 END AS email_lawan,
                   t.jumlah,
                   t.catatan,
                   CASE WHEN t.email_member_1 = %s THEN 'Kirim' ELSE 'Terima' END AS tipe
            FROM TRANSFER t
            JOIN PENGGUNA p1 ON p1.email = t.email_member_1
            JOIN PENGGUNA p2 ON p2.email = t.email_member_2
            WHERE t.email_member_1 = %s OR t.email_member_2 = %s
            ORDER BY t.timestamp DESC
        """, (email, email, email, email, email))
        riwayat = cur.fetchall()

        return render(request, 'transfer.html', {
            'member': member,
            'riwayat': riwayat,
        })
    finally:
        cur.close()
        conn.close()

def transfer_create(request):
    if request.method != 'POST':
        return redirect('member:transfer-miles')

    email_pengirim = request.session['email']
    email_penerima = request.POST.get('email_penerima', '').strip()
    jumlah = request.POST.get('jumlah_miles')
    catatan = request.POST.get('catatan', '')

    conn = get_connection()
    cur = conn.cursor()
    try:
        # Trigger validasi_dan_catat_transfer akan otomatis jalan
        cur.execute("""
            INSERT INTO TRANSFER (email_member_1, email_member_2, jumlah, catatan)
            VALUES (%s, %s, %s, %s)
        """, (email_pengirim, email_penerima, jumlah, catatan))
        conn.commit()

        # Ambil pesan SUKSES dari trigger lewat conn.notices
        pesan = conn.notices[-1].strip() if conn.notices else 'Transfer berhasil.'
        messages.success(request, pesan)
    except Exception as e:
        conn.rollback()
      
        messages.error(request, str(e).split('\n')[0])
    finally:
        cur.close()
        conn.close()

    return redirect('member:transfer-miles')

def profil(request):
    return render(request, 'member/profil.html')

def dashboard_member(request):
    return render(request, 'member/dashboard-member.html')

def identitas(request):
    return render(request, 'member/identitas.html')