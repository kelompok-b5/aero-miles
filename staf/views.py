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


# HELPER

def _get_lowest_tier_id(cur):
    """Ambil id_tier terendah berdasarkan minimal_tier_miles."""
    cur.execute("""
        SELECT id_tier FROM TIER
        ORDER BY minimal_tier_miles ASC
        LIMIT 1
    """)
    row = cur.fetchone()
    return row[0] if row else None
 
 
def _generate_nomor_member(cur):
    """Generate nomor member berikutnya dalam format M0001, M0002, ..."""
    cur.execute("""
        SELECT nomor_member FROM MEMBER
        ORDER BY nomor_member DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    if row:
        last_num = int(row[0][1:])  # strip 'M', ambil angkanya
        return f"M{(last_num + 1):04d}"
    return "M0001"

# Kelola Member (CRUD) 

def kelola_member(request):

    if not request.session.get('email') or request.session.get('role') != 'staf':
        return redirect('/auth/login/')
 
    search_query = request.GET.get('search', '').strip()
    filter_tier  = request.GET.get('tier', '').strip()
 
    conn = get_connection()
    cur = conn.cursor()
    try:
        sql = """
            SELECT
                m.email,
                m.nomor_member,
                p.salutation,
                p.first_mid_name,
                p.last_name,
                t.id_tier,
                t.nama        AS nama_tier,
                m.total_miles,
                m.award_miles,
                m.tanggal_bergabung
            FROM MEMBER m
            JOIN PENGGUNA p ON m.email = p.email
            JOIN TIER     t ON m.id_tier = t.id_tier
            WHERE 1=1
        """
        params = []
 
        if search_query:
            sql += """
                AND (
                    LOWER(p.first_mid_name || ' ' || p.last_name) LIKE LOWER(%s)
                    OR LOWER(m.email)        LIKE LOWER(%s)
                    OR LOWER(m.nomor_member) LIKE LOWER(%s)
                )
            """
            like = f"%{search_query}%"
            params.extend([like, like, like])
 
        if filter_tier:
            sql += " AND m.id_tier = %s"
            params.append(filter_tier)
 
        sql += " ORDER BY m.nomor_member ASC"
        cur.execute(sql, params)
        columns = [col[0] for col in cur.description]
        members = [dict(zip(columns, row)) for row in cur.fetchall()]
 
        # Dropdown filter tier
        cur.execute("SELECT id_tier, nama FROM TIER ORDER BY minimal_tier_miles ASC")
        tiers = cur.fetchall()
 
    finally:
        cur.close()
        conn.close()
 
    return render(request, 'staf/kelola-member.html', {
        'members': members,
        'tiers': tiers,
        'search_query': search_query,
        'filter_tier': filter_tier,
    })
 
 
def member_create(request):

    if request.method != 'POST':
        return redirect('staf:kelola-member')
    if not request.session.get('email') or request.session.get('role') != 'staf':
        return redirect('/auth/login/')
 
    email           = request.POST.get('email', '').strip().lower()
    password        = request.POST.get('password', '').strip()
    salutation      = request.POST.get('salutation', '').strip()
    first_mid_name  = request.POST.get('first_mid_name', '').strip()
    last_name       = request.POST.get('last_name', '').strip()
    country_code    = request.POST.get('country_code', '').strip()
    mobile_number   = request.POST.get('mobile_number', '').strip()
    tanggal_lahir   = request.POST.get('tanggal_lahir', '').strip()
    kewarganegaraan = request.POST.get('kewarganegaraan', '').strip()
 
    if not all([email, password, salutation, first_mid_name, last_name,
                country_code, mobile_number, tanggal_lahir, kewarganegaraan]):
        messages.error(request, 'Semua field wajib diisi.')
        return redirect('staf:kelola-member')
 
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Cek duplikasi email — trigger di DB juga cek ini,
        # tapi kita cek duluan biar pesan error lebih bersih
        cur.execute(
            "SELECT 1 FROM PENGGUNA WHERE LOWER(email) = LOWER(%s)",
            [email]
        )
        if cur.fetchone():
            messages.error(request, f'Email "{email}" sudah terdaftar, silakan gunakan email lain.')
            return redirect('staf:kelola-member')
 
        hashed_pw    = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        nomor_member = _generate_nomor_member(cur)
        id_tier_awal = _get_lowest_tier_id(cur)
 
        cur.execute("""
            INSERT INTO PENGGUNA
                (email, password, salutation, first_mid_name, last_name,
                 country_code, mobile_number, tanggal_lahir, kewarganegaraan)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, [email, hashed_pw, salutation, first_mid_name, last_name,
              country_code, mobile_number, tanggal_lahir, kewarganegaraan])
 
        cur.execute("""
            INSERT INTO MEMBER
                (email, nomor_member, tanggal_bergabung, id_tier, award_miles, total_miles)
            VALUES (%s, %s, CURRENT_DATE, %s, 0, 0)
        """, [email, nomor_member, id_tier_awal])
 
        conn.commit()
        messages.success(request, f'Member {first_mid_name} {last_name} berhasil ditambahkan ({nomor_member}).')
    except Exception as e:
        conn.rollback()
        messages.error(request, f'Gagal menambahkan member: {e}')
    finally:
        cur.close()
        conn.close()
 
    return redirect('staf:kelola-member')
 
 
def member_edit(request, email):
    """UPDATE — staf edit data profil + tier member."""
    if request.method != 'POST':
        return redirect('staf:kelola-member')
    if not request.session.get('email') or request.session.get('role') != 'staf':
        return redirect('/auth/login/')
 
    salutation      = request.POST.get('salutation', '').strip()
    first_mid_name  = request.POST.get('first_mid_name', '').strip()
    last_name       = request.POST.get('last_name', '').strip()
    country_code    = request.POST.get('country_code', '').strip()
    mobile_number   = request.POST.get('mobile_number', '').strip()
    tanggal_lahir   = request.POST.get('tanggal_lahir', '').strip()
    kewarganegaraan = request.POST.get('kewarganegaraan', '').strip()
    id_tier         = request.POST.get('id_tier', '').strip()
 
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Update data profil di PENGGUNA (email tidak bisa diubah)
        cur.execute("""
            UPDATE PENGGUNA
            SET salutation      = %s,
                first_mid_name  = %s,
                last_name       = %s,
                country_code    = %s,
                mobile_number   = %s,
                tanggal_lahir   = %s,
                kewarganegaraan = %s
            WHERE email = %s
        """, [salutation, first_mid_name, last_name, country_code,
              mobile_number, tanggal_lahir, kewarganegaraan, email])
 
        # Update tier jika dikirim
        if id_tier:
            cur.execute(
                "UPDATE MEMBER SET id_tier = %s WHERE email = %s",
                [id_tier, email]
            )
 
        conn.commit()
        messages.success(request, 'Data member berhasil diperbarui.')
    except Exception as e:
        conn.rollback()
        messages.error(request, f'Gagal memperbarui member: {e}')
    finally:
        cur.close()
        conn.close()
 
    return redirect('staf:kelola-member')
 
 
def member_delete(request, email):
    """DELETE — hapus member beserta semua data terkait."""
    if request.method != 'POST':
        return redirect('staf:kelola-member')
    if not request.session.get('email') or request.session.get('role') != 'staf':
        return redirect('/auth/login/')
 
    conn = get_connection()
    cur = conn.cursor()
    try:
        # Hapus child tables dulu (urutan sesuai FK),
        # sebelum hapus MEMBER dan PENGGUNA
        cur.execute("DELETE FROM IDENTITAS               WHERE email_member = %s", [email])
        cur.execute("DELETE FROM REDEEM                  WHERE email_member = %s", [email])
        cur.execute("DELETE FROM MEMBER_AWARD_MILES_PACKAGE WHERE email_member = %s", [email])
        cur.execute("""
            DELETE FROM TRANSFER
            WHERE email_member_1 = %s OR email_member_2 = %s
        """, [email, email])
        cur.execute("""
            DELETE FROM CLAIM_MISSING_MILES WHERE email_member = %s
        """, [email])
        cur.execute("DELETE FROM MEMBER   WHERE email = %s", [email])
        cur.execute("DELETE FROM PENGGUNA WHERE email = %s", [email])
 
        conn.commit()
        messages.success(request, 'Member beserta seluruh data terkait berhasil dihapus.')
    except Exception as e:
        conn.rollback()
        messages.error(request, f'Gagal menghapus member: {e}')
    finally:
        cur.close()
        conn.close()
 
    return redirect('staf:kelola-member')

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