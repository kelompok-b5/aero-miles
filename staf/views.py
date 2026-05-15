from pyexpat.errors import messages

from django.shortcuts import redirect, render
from django.http import JsonResponse
from aeromiles.db import get_connection
from django.views.decorators.csrf import csrf_exempt
import json
from django.contrib import messages

def dashboard_staf(request):
    return render(request, 'staf/dashboard-staf.html')

def claim_staff(request):
    if not request.session.get('email') or request.session.get('role') != 'staf':
        return redirect('/auth/login/')
    
    conn = get_connection()
    cur = conn.cursor()
    try:
        filter_status   = request.GET.get('status', '')
        filter_maskapai = request.GET.get('maskapai', '')
        filter_dari     = request.GET.get('dari', '')
        filter_sampai   = request.GET.get('sampai', '')

        query = """
            SELECT c.id, p.first_mid_name || ' ' || p.last_name AS nama_member,
                   c.email_member, c.maskapai, c.bandara_asal, c.bandara_tujuan,
                   c.tanggal_penerbangan, c.flight_number, c.kelas_kabin,
                   c.timestamp, c.status_penerimaan, c.email_staf
            FROM CLAIM_MISSING_MILES c
            JOIN PENGGUNA p ON p.email = c.email_member
            WHERE 1=1
        """
        params = []
        if filter_status:
            query += " AND c.status_penerimaan = %s"
            params.append(filter_status)
        if filter_maskapai:
            query += " AND c.maskapai = %s"
            params.append(filter_maskapai)
        if filter_dari:
            query += " AND c.timestamp::date >= %s"
            params.append(filter_dari)
        if filter_sampai:
            query += " AND c.timestamp::date <= %s"
            params.append(filter_sampai)
        query += " ORDER BY c.timestamp DESC"

        cur.execute(query, params)
        klaim_list = cur.fetchall()

        cur.execute("SELECT kode_maskapai, nama_maskapai FROM MASKAPAI")
        maskapai_list = cur.fetchall()

        return render(request, 'staf/claim-staff.html', {
            'klaim_list': klaim_list,
            'maskapai_list': maskapai_list,
        })
    finally:
        cur.close()
        conn.close()


def claim_proses(request, klaim_id):
    if not request.session.get('email') or request.session.get('role') != 'staf':
        return redirect('/auth/login/')

    if request.method != 'POST':
        return redirect('staf:claim-staff')

    email_staf = request.session.get('email')
    status_baru = request.POST.get('status')

    if status_baru not in ('Disetujui', 'Ditolak'):
        messages.error(request, 'Status tidak valid.')
        return redirect('staf:claim-staff')

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            UPDATE CLAIM_MISSING_MILES
            SET status_penerimaan = %s, email_staf = %s
            WHERE id = %s AND status_penerimaan = 'Menunggu'
        """, (status_baru, email_staf, klaim_id))
        conn.commit()

        if conn.notices:
            messages.success(request, conn.notices[-1].strip())

    except Exception as e:
        conn.rollback()
        messages.error(request, str(e).split('\n')[0])
    finally:
        cur.close()
        conn.close()

    return redirect('staf:claim-staff')

def kelola_hadiah(request):
    return render(request, 'staf/kelola-hadiah.html')

def kelola_member(request):
    return render(request, 'staf/kelola-member.html')

def kelola_mitra(request):
    return render(request, 'staf/kelola-mitra.html')

def laporan_transaksi(request):
    conn = get_connection()
    cursor = conn.cursor()

    # 1. TRANSFER
    cursor.execute("""
        SELECT 
            'Transfer' as tipe,
            t.email_member_1 as email,
            CONCAT(p.salutation, ' ', p.first_mid_name, ' ', p.last_name) as nama,
            t.jumlah,
            t.timestamp,
            t.email_member_1,
            t.email_member_2,
            t.timestamp as pk_ts
        FROM TRANSFER t
        JOIN PENGGUNA p ON t.email_member_1 = p.email
        ORDER BY t.timestamp DESC
    """)
    transfer_rows = cursor.fetchall()

    # 2. REDEEM
    cursor.execute("""
        SELECT
            'Redeem' as tipe,
            r.email_member as email,
            CONCAT(p.salutation, ' ', p.first_mid_name, ' ', p.last_name) as nama,
            h.miles,
            r.timestamp,
            r.kode_hadiah
        FROM REDEEM r
        JOIN PENGGUNA p ON r.email_member = p.email
        JOIN HADIAH h ON r.kode_hadiah = h.kode_hadiah
        ORDER BY r.timestamp DESC
    """)
    redeem_rows = cursor.fetchall()

    # 3. PACKAGE
    cursor.execute("""
        SELECT
            'Package' as tipe,
            m.email_member as email,
            CONCAT(p.salutation, ' ', p.first_mid_name, ' ', p.last_name) as nama,
            a.jumlah_award_miles,
            m.timestamp,
            m.id_award_miles_package
        FROM MEMBER_AWARD_MILES_PACKAGE m
        JOIN PENGGUNA p ON m.email_member = p.email
        JOIN AWARD_MILES_PACKAGE a ON m.id_award_miles_package = a.id
        ORDER BY m.timestamp DESC
    """)
    package_rows = cursor.fetchall()

    # 4. KLAIM DISETUJUI
    cursor.execute("""
        SELECT
            'Klaim' as tipe,
            c.email_member as email,
            CONCAT(p.salutation, ' ', p.first_mid_name, ' ', p.last_name) as nama,
            1000 as miles,
            c.timestamp,
            c.id
        FROM CLAIM_MISSING_MILES c
        JOIN PENGGUNA p ON c.email_member = p.email
        WHERE c.status_penerimaan = 'Disetujui'
        ORDER BY c.timestamp DESC
    """)
    klaim_rows = cursor.fetchall()

    # Gabung semua transaksi
    transaksi = []
    for r in transfer_rows:
        transaksi.append({
            'tipe': 'Transfer',
            'email': r[1],
            'nama': r[2],
            'miles': -r[3],  # negatif karena pengirim
            'waktu': str(r[4])[:16],
            'hapusable': True,
            'pk': {'email_member_1': r[5], 'email_member_2': r[6], 'timestamp': str(r[7])},
        })
    for r in redeem_rows:
        transaksi.append({
            'tipe': 'Redeem',
            'email': r[1],
            'nama': r[2],
            'miles': -r[3],
            'waktu': str(r[4])[:16],
            'hapusable': True,
            'pk': {'email_member': r[1], 'kode_hadiah': r[5], 'timestamp': str(r[4])},
        })
    for r in package_rows:
        transaksi.append({
            'tipe': 'Package',
            'email': r[1],
            'nama': r[2],
            'miles': r[3],
            'waktu': str(r[4])[:16],
            'hapusable': True,
            'pk': {'email_member': r[1], 'id_package': r[5], 'timestamp': str(r[4])},
        })
    for r in klaim_rows:
        transaksi.append({
            'tipe': 'Klaim',
            'email': r[1],
            'nama': r[2],
            'miles': r[3],
            'waktu': str(r[4])[:16],
            'hapusable': False,  # klaim disetujui tidak bisa dihapus
            'pk': {'id': r[5]},
        })

    # Sort semua by waktu DESC
    transaksi.sort(key=lambda x: x['waktu'], reverse=True)

    # STATS
    # Total miles beredar = sum award_miles semua member
    cursor.execute("SELECT COALESCE(SUM(award_miles), 0) FROM MEMBER")
    total_miles_beredar = cursor.fetchone()[0]

    # Total redeem bulan ini
    cursor.execute("""
        SELECT COALESCE(SUM(h.miles), 0)
        FROM REDEEM r
        JOIN HADIAH h ON r.kode_hadiah = h.kode_hadiah
        WHERE DATE_TRUNC('month', r.timestamp) = DATE_TRUNC('month', CURRENT_DATE)
    """)
    total_redeem_bulan_ini = cursor.fetchone()[0]

    # Total klaim disetujui (miles)
    cursor.execute("""
        SELECT COUNT(*) * 1000
        FROM CLAIM_MISSING_MILES
        WHERE status_penerimaan = 'Disetujui'
    """)
    total_klaim = cursor.fetchone()[0]

    # Panggil stored procedure sp_top5_member_total_miles
    # dan tangkap RAISE NOTICE-nya
    conn.notices = []  # reset notices
    cursor.execute("CALL sp_top5_member_total_miles()")
    sp_notice = conn.notices[-1].strip() if conn.notices else ''
    sp_notice = sp_notice.replace('NOTICE:  ', '').strip()  # hapus prefix NOTICE
    if sp_notice:
        messages.info(request, sp_notice)

    # TOP MEMBER: total miles
    cursor.execute("""
        SELECT 
            m.email,
            CONCAT(p.salutation, ' ', p.first_mid_name, ' ', p.last_name) as nama,
            m.total_miles,
            (SELECT COUNT(*) FROM TRANSFER WHERE email_member_1 = m.email OR email_member_2 = m.email)
            + (SELECT COUNT(*) FROM REDEEM WHERE email_member = m.email)
            + (SELECT COUNT(*) FROM MEMBER_AWARD_MILES_PACKAGE WHERE email_member = m.email) as jumlah_transaksi
        FROM MEMBER m
        JOIN PENGGUNA p ON m.email = p.email
        ORDER BY m.total_miles DESC
        LIMIT 5
    """)
    top_miles = [
        {'email': r[0], 'nama': r[1], 'total_miles': r[2], 'jumlah_transaksi': r[3]}
        for r in cursor.fetchall()
    ]

    # TOP MEMBER: total redeem
    cursor.execute("""
        SELECT
            r.email_member,
            CONCAT(p.salutation, ' ', p.first_mid_name, ' ', p.last_name) as nama,
            SUM(h.miles) as total_redeem
        FROM REDEEM r
        JOIN PENGGUNA p ON r.email_member = p.email
        JOIN HADIAH h ON r.kode_hadiah = h.kode_hadiah
        GROUP BY r.email_member, p.salutation, p.first_mid_name, p.last_name
        ORDER BY total_redeem DESC
        LIMIT 5
    """)
    top_redeem = [
        {'email': r[0], 'nama': r[1], 'total_redeem': r[2]}
        for r in cursor.fetchall()
    ]

    # TOP MEMBER: total transfer
    cursor.execute("""
        SELECT
            t.email_member_1,
            CONCAT(p.salutation, ' ', p.first_mid_name, ' ', p.last_name) as nama,
            SUM(t.jumlah) as total_transfer
        FROM TRANSFER t
        JOIN PENGGUNA p ON t.email_member_1 = p.email
        GROUP BY t.email_member_1, p.salutation, p.first_mid_name, p.last_name
        ORDER BY total_transfer DESC
        LIMIT 5
    """)
    top_transfer = [
        {'email': r[0], 'nama': r[1], 'total_transfer': r[2]}
        for r in cursor.fetchall()
    ]

    cursor.close()
    conn.close()

    return render(request, 'staf/laporan-transaksi.html', {
        'transaksi_json': json.dumps(transaksi),
        'top_miles_json': json.dumps(top_miles),
        'top_redeem_json': json.dumps(top_redeem),
        'top_transfer_json': json.dumps(top_transfer),
        'stat_miles': total_miles_beredar,
        'stat_redeem': total_redeem_bulan_ini,
        'stat_klaim': total_klaim,
        'sp_notice': sp_notice,
    })


@csrf_exempt
def hapus_transaksi(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        tipe = data.get('tipe')
        pk = data.get('pk')

        conn = get_connection()
        cursor = conn.cursor()
        try:
            if tipe == 'Transfer':
                cursor.execute("""
                    DELETE FROM TRANSFER
                    WHERE email_member_1 = %s AND email_member_2 = %s AND timestamp = %s
                """, [pk['email_member_1'], pk['email_member_2'], pk['timestamp']])
            elif tipe == 'Redeem':
                cursor.execute("""
                    DELETE FROM REDEEM
                    WHERE email_member = %s AND kode_hadiah = %s AND timestamp = %s
                """, [pk['email_member'], pk['kode_hadiah'], pk['timestamp']])
            elif tipe == 'Package':
                cursor.execute("""
                    DELETE FROM MEMBER_AWARD_MILES_PACKAGE
                    WHERE email_member = %s AND id_award_miles_package = %s AND timestamp = %s
                """, [pk['email_member'], pk['id_package'], pk['timestamp']])

            conn.commit()
            return JsonResponse({'success': True})
        except Exception as e:
            conn.rollback()
            return JsonResponse({'error': str(e)}, status=500)
        finally:
            cursor.close()
            conn.close()

def profile_staf(request):
    return render(request, 'staf/profile-staf.html')