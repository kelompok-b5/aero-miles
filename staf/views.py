from pyexpat.errors import messages
from django.shortcuts import redirect, render
from django.http import JsonResponse
from aeromiles.db import get_connection
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
import json
from datetime import date
from django.contrib.auth.hashers import check_password, make_password

def dashboard_staf(request):
    '''Menampilkan data dashboard staf dengan statistik klaim missing miles terkait maskapai yang dikelola.'''

    email_staf = request.session.get('email')
    if not email_staf or request.session.get('role') != 'staf':
        return redirect('/auth/login/')

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # =========================================
        # AMBIL DATA PROFIL STAF
        # =========================================
        cursor.execute("""
            SELECT
                p.email,
                p.salutation,
                p.first_mid_name,
                p.last_name,
                p.country_code,
                p.mobile_number,
                p.kewarganegaraan,
                p.tanggal_lahir,
                s.id_staf,
                m.kode_maskapai,
                m.nama_maskapai
            FROM PENGGUNA p
            JOIN STAF s ON p.email = s.email
            JOIN MASKAPAI m ON s.kode_maskapai = m.kode_maskapai
            WHERE p.email = %s
        """, [email_staf])

        row = cursor.fetchone()

        staf_data = {}
        kode_maskapai = None

        if row:

            kode_maskapai = row[9]

            staf_data = {
                'email': row[0],
                'nama_lengkap': f"{row[1]} {row[2]} {row[3]}",
                'country_code': row[4],
                'mobile_number': row[5],
                'telepon': f"{row[4]} {row[5]}" if row[5] else '-',
                'kewarganegaraan': row[6],
                'tanggal_lahir': row[7].strftime('%d %B %Y') if row[7] else '-',
                'id_staf': row[8],
                'kode_maskapai': row[9],
                'nama_maskapai': row[10],
                'maskapai': f"{row[10]} ({row[9]})"
            }

        # =========================================
        # STATISTIK CLAIM
        # =========================================
        cursor.execute("""
            SELECT
                COUNT(CASE WHEN status_penerimaan = 'Menunggu' THEN 1 END) AS menunggu,
                COUNT(CASE WHEN status_penerimaan = 'Disetujui' AND email_staf = %s THEN 1 END) AS disetujui,
                COUNT(CASE WHEN status_penerimaan = 'Ditolak' AND email_staf = %s THEN 1 END) AS ditolak
            FROM CLAIM_MISSING_MILES
            WHERE maskapai = %s
        """, [
            staf_data.get('email'),
            staf_data.get('email'),
            kode_maskapai
        ])

        stats_row = cursor.fetchone()

        stats = {
            'menunggu': stats_row[0] if stats_row else 0,
            'disetujui': stats_row[1] if stats_row else 0,
            'ditolak': stats_row[2] if stats_row else 0,
        }

        context = {
            'staf': staf_data,
            'stats': stats
        }

        return render(
            request,
            'staf/dashboard-staf.html',
            context
        )

    except Exception as e:
        print("ERROR DASHBOARD STAF:", e)
        return render(
            request,
            'staf/dashboard-staf.html',
            {
                'error': str(e)
            }
        )
    finally:
        cursor.close()
        conn.close()

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
    """
    Menampilkan halaman kelola hadiah beserta:
    - daftar hadiah
    - daftar penyedia
    - statistik total hadiah, hadiah aktif, hadiah nonaktif
    """

    if not request.session.get('email') or request.session.get('role') != 'staf':
        return redirect('/auth/login/')
 
    conn = get_connection()
    cursor = conn.cursor()
 
    try:
 
        # ====================================
        # AMBIL DATA HADIAH + PENYEDIA
        # ====================================
        cursor.execute("""
            SELECT
                h.kode_hadiah,
                h.nama,
                h.deskripsi,
                h.miles,
                h.valid_start_date,
                h.program_end,
                p.id,
                COALESCE(m.nama_mitra, maskapai.nama_maskapai) AS nama_penyedia,
                CASE
                    WHEN m.id_penyedia IS NOT NULL THEN 'partner'
                    ELSE 'airline'
                END AS tipe_penyedia
            FROM hadiah h
            JOIN penyedia p ON h.id_penyedia = p.id
            LEFT JOIN mitra m ON p.id = m.id_penyedia
            LEFT JOIN maskapai ON p.id = maskapai.id_penyedia
            ORDER BY h.kode_hadiah ASC
        """)
 
        rows = cursor.fetchall()
 
        hadiah_list = []
        total_hadiah = 0
        total_hadiah_aktif = 0
        today = date.today()
 
        for row in rows:
 
            total_hadiah += 1
            valid_start = row[4]
            program_end = row[5]
            is_aktif = valid_start <= today <= program_end
 
            if is_aktif:
                total_hadiah_aktif += 1
 
            hadiah_list.append({
                'kode':          row[0],
                'nama':          row[1],
                'deskripsi':     row[2] if row[2] else '',
                'miles':         row[3],
                'start':         row[4].strftime('%Y-%m-%d') if row[4] else '',
                'end':           row[5].strftime('%Y-%m-%d') if row[5] else '',
                'penyedia_id':   row[6],
                'penyedia_nama': row[7],
                'penyedia_tipe': row[8],
                'is_aktif':      is_aktif,
            })
 
        # ====================================
        # AMBIL DATA PENYEDIA UNTUK DROPDOWN
        # ====================================
        cursor.execute("""
            SELECT
                p.id,
                COALESCE(m.nama_mitra, maskapai.nama_maskapai) AS nama_penyedia,
                CASE
                    WHEN m.id_penyedia IS NOT NULL THEN 'partner'
                    ELSE 'airline'
                END AS tipe_penyedia
            FROM penyedia p
            LEFT JOIN mitra m ON p.id = m.id_penyedia
            LEFT JOIN maskapai ON p.id = maskapai.id_penyedia
            ORDER BY nama_penyedia ASC
        """)
 
        penyedia_rows = cursor.fetchall()
        penyedia_list = [
            {
                'id':   row[0],
                'nama': row[1],
                'tipe': row[2],
            }
            for row in penyedia_rows
        ]
 
        context = {
            'hadiah_json':           json.dumps(hadiah_list),
            'penyedia_json':         json.dumps(penyedia_list),
            'total_hadiah':          total_hadiah,
            'total_hadiah_aktif':    total_hadiah_aktif,
            'total_hadiah_nonaktif': total_hadiah - total_hadiah_aktif,
        }
 
        return render(request, 'staf/kelola-hadiah.html', context)
 
    except Exception as e:
 
        return render(request, 'staf/kelola-hadiah.html', {'error': str(e)})
 
    finally:
        cursor.close()
        conn.close()
 
 
@csrf_exempt
def tambah_hadiah(request):
 
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method tidak diizinkan'}, status=405)
 
    conn = get_connection()
    cursor = conn.cursor()
 
    try:
 
        data        = json.loads(request.body)
        nama        = data.get('nama')
        deskripsi   = data.get('deskripsi', '')
        miles       = data.get('miles')
        start       = data.get('start')
        end         = data.get('end')
        id_penyedia = data.get('id_penyedia')
 
        # ====================================
        # VALIDASI INPUT
        # ====================================
        if not nama or not miles or not start or not end or not id_penyedia:
            return JsonResponse({'success': False, 'message': 'Semua field wajib diisi'}, status=400)
 
        # Validasi tanggal: start tidak boleh lebih dari end
        if start > end:
            return JsonResponse({
                'success': False,
                'message': 'Tanggal mulai tidak boleh lebih dari tanggal berakhir'
            }, status=400)
 
        # ====================================
        # CEK PENYEDIA EXIST
        # ====================================
        cursor.execute("SELECT 1 FROM penyedia WHERE id = %s", [id_penyedia])
        if not cursor.fetchone():
            return JsonResponse({'success': False, 'message': 'Penyedia tidak ditemukan'}, status=404)
 
        # ====================================
        # INSERT HADIAH
        # ====================================

        cursor.execute("""
            INSERT INTO hadiah (nama, deskripsi, miles, valid_start_date, program_end, id_penyedia)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING kode_hadiah
        """, [nama, deskripsi, miles, start, end, id_penyedia])
 
        kode_hadiah = cursor.fetchone()[0]
 
        # Ambil nama penyedia untuk response
        cursor.execute("""
            SELECT COALESCE(m.nama_mitra, maskapai.nama_maskapai),
                   CASE WHEN m.id_penyedia IS NOT NULL THEN 'partner' ELSE 'airline' END
            FROM penyedia p
            LEFT JOIN mitra m ON p.id = m.id_penyedia
            LEFT JOIN maskapai ON p.id = maskapai.id_penyedia
            WHERE p.id = %s
        """, [id_penyedia])
 
        penyedia_row  = cursor.fetchone()
        penyedia_nama = penyedia_row[0] if penyedia_row else '-'
        penyedia_tipe = penyedia_row[1] if penyedia_row else 'airline'
 
        conn.commit()
 
        return JsonResponse({
            'success': True,
            'message': 'Hadiah berhasil ditambahkan',
            'data': {
                'kode':          kode_hadiah,
                'nama':          nama,
                'deskripsi':     deskripsi,
                'miles':         miles,
                'start':         start,
                'end':           end,
                'penyedia_id':   id_penyedia,
                'penyedia_nama': penyedia_nama,
                'penyedia_tipe': penyedia_tipe,
                'is_aktif':      start <= date.today().isoformat() <= end,
            }
        })
 
    except Exception as e:
        conn.rollback()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
 
    finally:
        cursor.close()
        conn.close()
 
 
@csrf_exempt
def edit_hadiah(request):
 
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method tidak diizinkan'}, status=405)
 
    conn = get_connection()
    cursor = conn.cursor()
 
    try:
 
        data        = json.loads(request.body)
        kode        = data.get('kode')
        nama        = data.get('nama')
        deskripsi   = data.get('deskripsi', '')
        miles       = data.get('miles')
        start       = data.get('start')
        end         = data.get('end')
        id_penyedia = data.get('id_penyedia')
 
        # ====================================
        # VALIDASI INPUT
        # ====================================
        if not kode or not nama or not miles or not start or not end or not id_penyedia:
            return JsonResponse({'success': False, 'message': 'Data tidak lengkap'}, status=400)
 
        if start > end:
            return JsonResponse({
                'success': False,
                'message': 'Tanggal mulai tidak boleh lebih dari tanggal berakhir'
            }, status=400)
 
        # ====================================
        # CEK HADIAH EXIST
        # ====================================
        cursor.execute("SELECT 1 FROM hadiah WHERE kode_hadiah = %s", [kode])
        if not cursor.fetchone():
            return JsonResponse({'success': False, 'message': 'Hadiah tidak ditemukan'}, status=404)
 
        # ====================================
        # UPDATE HADIAH
        # ====================================
        cursor.execute("""
            UPDATE hadiah
            SET
                nama             = %s,
                deskripsi        = %s,
                miles            = %s,
                valid_start_date = %s,
                program_end      = %s,
                id_penyedia      = %s
            WHERE kode_hadiah = %s
        """, [nama, deskripsi, miles, start, end, id_penyedia, kode])
 
        conn.commit()
 
        return JsonResponse({'success': True, 'message': 'Hadiah berhasil diperbarui'})
 
    except Exception as e:
        conn.rollback()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
 
    finally:
        cursor.close()
        conn.close()
 
 
@csrf_exempt
def hapus_hadiah(request):
 
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Method tidak diizinkan'}, status=405)
 
    conn = get_connection()
    cursor = conn.cursor()
 
    try:
 
        data = json.loads(request.body)
        kode = data.get('kode')
 
        if not kode:
            return JsonResponse({'success': False, 'message': 'Kode hadiah wajib diisi'}, status=400)
 
        # ====================================
        # CEK HADIAH EXIST
        # ====================================
        cursor.execute("""
            SELECT nama, program_end FROM hadiah WHERE kode_hadiah = %s
        """, [kode])
 
        row = cursor.fetchone()
        if not row:
            return JsonResponse({'success': False, 'message': 'Hadiah tidak ditemukan'}, status=404)
 
        nama_hadiah = row[0]
        program_end = row[1]
 
        # ====================================
        # VALIDASI: hanya hadiah nonaktif yang boleh dihapus
        # ====================================
        if program_end >= date.today():
            return JsonResponse({
                'success': False,
                'message': 'Hanya hadiah yang sudah tidak berlaku yang dapat dihapus'
            }, status=400)
 
        # ====================================
        # DELETE HADIAH
        # ====================================
        cursor.execute("DELETE FROM hadiah WHERE kode_hadiah = %s", [kode])
 
        conn.commit()
 
        return JsonResponse({
            'success': True,
            'message': f'Hadiah {nama_hadiah} berhasil dihapus'
        })
 
    except Exception as e:
        conn.rollback()
        return JsonResponse({'success': False, 'message': str(e)}, status=500)
 
    finally:
        cursor.close()
        conn.close()

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
                p.country_code,
                p.mobile_number,
                p.tanggal_lahir,
                p.kewarganegaraan,
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
 
        # Hitung stats untuk hero
        members_active_count  = sum(1 for m in members if (m['total_miles'] or 0) > 0)
        members_diamond_count = sum(1 for m in members if m['nama_tier'] == 'Diamond')
 
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
        'members_active_count': members_active_count,
        'members_diamond_count': members_diamond_count,
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
    """
    Menampilkan halaman Kelola Mitra beserta:
    - daftar mitra
    - jumlah hadiah aktif
    - statistik total mitra
    - statistik hadiah aktif
    - statistik mitra baru 30 hari terakhir
    """

    if not request.session.get('email') or request.session.get('role') != 'staf':
        return redirect('/auth/login/')
    
    conn = get_connection()
    cursor = conn.cursor()

    try:

        # =========================
        # AMBIL DATA MITRA
        # =========================
        cursor.execute("""
            SELECT
                m.id_penyedia,
                m.email_mitra,
                m.nama_mitra,
                m.tanggal_kerja_sama,
                COUNT(
                    CASE
                        WHEN h.program_end >= CURRENT_DATE
                        THEN h.kode_hadiah
                    END
                ) AS jumlah_hadiah
            FROM MITRA m
            LEFT JOIN HADIAH h
                ON m.id_penyedia = h.id_penyedia
            GROUP BY
                m.id_penyedia,
                m.email_mitra,
                m.nama_mitra,
                m.tanggal_kerja_sama
            ORDER BY m.id_penyedia ASC
        """)

        rows = cursor.fetchall()

        mitra_list = []

        total_hadiah = 0
        total_mitra_baru = 0

        for row in rows:

            jumlah_hadiah = row[4]

            total_hadiah += jumlah_hadiah

            # cek mitra baru (30 hari terakhir)
            cursor.execute("""
                SELECT
                    CASE
                        WHEN %s >= CURRENT_DATE - INTERVAL '30 days'
                        THEN TRUE
                        ELSE FALSE
                    END
            """, [row[3]])

            is_baru = cursor.fetchone()[0]

            if is_baru:
                total_mitra_baru += 1

            mitra_list.append({
                'id': row[0],
                'email': row[1],
                'nama': row[2],
                'tgl': row[3].strftime('%Y-%m-%d')
                    if row[3] else '',
                'hadiah': jumlah_hadiah
            })

        context = {
            'mitra_json': json.dumps(mitra_list),
            'total_mitra': len(mitra_list),
            'total_hadiah': total_hadiah,
            'total_mitra_baru': total_mitra_baru
        }

        return render(
            request,
            'staf/kelola-mitra.html',
            context
        )

    except Exception as e:

        return render(
            request,
            'staf/kelola-mitra.html',
            {
                'error': str(e)
            }
        )

    finally:
        cursor.close()
        conn.close()


@csrf_exempt
def tambah_mitra(request):

    if request.method != 'POST':

        return JsonResponse({
            'success': False,
            'message': 'Method tidak diizinkan'
        }, status=405)

    conn = get_connection()
    cursor = conn.cursor()

    try:

        data = json.loads(request.body)

        email = data.get('email')
        nama = data.get('nama')
        tanggal = data.get('tgl')

        # =========================
        # VALIDASI INPUT
        # =========================
        if not email or not nama or not tanggal:

            return JsonResponse({
                'success': False,
                'message': 'Semua field wajib diisi'
            }, status=400)

        # =========================
        # CEK EMAIL DUPLIKAT
        # =========================
        cursor.execute("""
            SELECT 1
            FROM MITRA
            WHERE LOWER(email_mitra) = LOWER(%s)
        """, [email])

        if cursor.fetchone():

            return JsonResponse({
                'success': False,
                'message': 'Email mitra sudah terdaftar'
            }, status=400)

        # =========================
        # INSERT PENYEDIA
        # =========================

        cursor.execute("""
            SELECT setval('penyedia_id_seq', (SELECT MAX(id) FROM penyedia))
        """)

        cursor.execute("""
            INSERT INTO PENYEDIA
            DEFAULT VALUES
            RETURNING id
        """)

        id_penyedia = cursor.fetchone()[0]

        # =========================
        # INSERT MITRA
        # =========================
        cursor.execute("""
            INSERT INTO MITRA (
                email_mitra,
                id_penyedia,
                nama_mitra,
                tanggal_kerja_sama
            )
            VALUES (%s, %s, %s, %s)
        """, [
            email,
            id_penyedia,
            nama,
            tanggal
        ])

        conn.commit()

        return JsonResponse({
            'success': True,
            'message': 'Mitra berhasil ditambahkan',
            'data': {
                'id': id_penyedia,
                'email': email,
                'nama': nama,
                'tgl': tanggal,
                'hadiah': 0
            }
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


@csrf_exempt
def edit_mitra(request):

    if request.method != 'POST':

        return JsonResponse({
            'success': False,
            'message': 'Method tidak diizinkan'
        }, status=405)

    conn = get_connection()
    cursor = conn.cursor()

    try:

        data = json.loads(request.body)

        id_penyedia = data.get('id')
        nama = data.get('nama')
        tanggal = data.get('tgl')

        # =========================
        # VALIDASI INPUT
        # =========================
        if not id_penyedia or not nama or not tanggal:

            return JsonResponse({
                'success': False,
                'message': 'Data tidak lengkap'
            }, status=400)

        # =========================
        # CEK MITRA EXIST
        # =========================
        cursor.execute("""
            SELECT 1
            FROM MITRA
            WHERE id_penyedia = %s
        """, [id_penyedia])

        if not cursor.fetchone():

            return JsonResponse({
                'success': False,
                'message': 'Mitra tidak ditemukan'
            }, status=404)

        # =========================
        # UPDATE MITRA
        # =========================
        cursor.execute("""
            UPDATE MITRA
            SET
                nama_mitra = %s,
                tanggal_kerja_sama = %s
            WHERE id_penyedia = %s
        """, [
            nama,
            tanggal,
            id_penyedia
        ])

        conn.commit()

        return JsonResponse({
            'success': True,
            'message': 'Mitra berhasil diperbarui'
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


@csrf_exempt
def hapus_mitra(request):

    if request.method != 'POST':

        return JsonResponse({
            'success': False,
            'message': 'Method tidak diizinkan'
        }, status=405)

    conn = get_connection()
    cursor = conn.cursor()

    try:

        data = json.loads(request.body)

        id_penyedia = data.get('id')

        if not id_penyedia:

            return JsonResponse({
                'success': False,
                'message': 'ID Penyedia wajib diisi'
            }, status=400)

        # =========================
        # CEK MITRA EXIST
        # =========================
        cursor.execute("""
            SELECT nama_mitra
            FROM MITRA
            WHERE id_penyedia = %s
        """, [id_penyedia])

        row = cursor.fetchone()

        if not row:

            return JsonResponse({
                'success': False,
                'message': 'Mitra tidak ditemukan'
            }, status=404)

        nama_mitra = row[0]

        # =========================
        # HAPUS MITRA
        # =========================
        cursor.execute("""
            DELETE FROM MITRA
            WHERE id_penyedia = %s
        """, [id_penyedia])

        # =========================
        # HAPUS PENYEDIA
        # =========================
        cursor.execute("""
            DELETE FROM PENYEDIA
            WHERE id = %s
        """, [id_penyedia])

        conn.commit()

        return JsonResponse({
            'success': True,
            'message': f'Mitra {nama_mitra} berhasil dihapus'
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

def laporan_transaksi(request):
    if not request.session.get('email') or request.session.get('role') != 'staf':
        return redirect('/auth/login/')

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

@csrf_exempt
def profile_staf(request):
    """
    Menampilkan data profil staf ke halaman profile-staf.html
    """

    email_staf = request.session.get('email')
    if not email_staf or request.session.get('role') != 'staf':
        return redirect('/auth/login/')

    conn = get_connection()
    cursor = conn.cursor()

    try:

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
                s.id_staf,
                s.kode_maskapai,
                m.nama_maskapai
            FROM PENGGUNA p
            JOIN STAF s
                ON p.email = s.email
            JOIN MASKAPAI m
                ON s.kode_maskapai = m.kode_maskapai
            WHERE p.email = %s
        """, [email_staf])

        row = cursor.fetchone()

        staf_data = {}

        if row:

            staf_data = {
                'email': row[0],
                'salutation': row[1],
                'first_mid_name': row[2],
                'last_name': row[3],
                'kewarganegaraan': row[4],
                'country_code': row[5],
                'mobile_number': row[6],
                'tanggal_lahir': (
                    row[7].strftime('%Y-%m-%d')
                    if row[7] else ''
                ),
                'id_staf': row[8],
                'kode_maskapai': row[9],
                'nama_maskapai': row[10]
            }

        # dropdown maskapai
        cursor.execute("""
            SELECT
                kode_maskapai,
                nama_maskapai
            FROM MASKAPAI
            ORDER BY nama_maskapai
        """)

        maskapai_rows = cursor.fetchall()

        daftar_maskapai = [
            {
                'kode_maskapai': m[0],
                'nama_maskapai': m[1]
            }
            for m in maskapai_rows
        ]

        context = {
            'staf': staf_data,
            'maskapai_list': daftar_maskapai
        }

        return render(
            request,
            'staf/profile-staf.html',
            context
        )

    except Exception as e:

        print("ERROR PROFILE STAF:", e)

        return render(
            request,
            'staf/profile-staf.html',
            {
                'error': str(e)
            }
        )

    finally:
        cursor.close()
        conn.close()

@csrf_exempt
def update_profile_staf(request):

    email_staf = request.session.get('email')

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
        kode_maskapai = request.POST.get('kode_maskapai')

        # =========================
        # AMBIL DATA LAMA
        # =========================
        cursor.execute("""
            SELECT
                p.salutation,
                p.first_mid_name,
                p.last_name,
                p.kewarganegaraan,
                p.country_code,
                p.mobile_number,
                p.tanggal_lahir,
                s.kode_maskapai
            FROM PENGGUNA p
            JOIN STAF s
                ON p.email = s.email
            WHERE p.email = %s
        """, [email_staf])

        old_data = cursor.fetchone()

        if old_data:

            old_tanggal_lahir = (
                old_data[6].strftime('%Y-%m-%d')
                if old_data[6]
                else ''
            )

            if (
                old_data[0] == salutation and
                old_data[1] == first_mid_name and
                old_data[2] == last_name and
                old_data[3] == kewarganegaraan and
                old_data[4] == country_code and
                old_data[5] == mobile_number and
                old_tanggal_lahir == tanggal_lahir and
                old_data[7] == kode_maskapai
            ):

                return JsonResponse({
                    'success': False,
                    'message': 'Tidak ada perubahan data'
                })

        # =========================
        # UPDATE PENGGUNA
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
            email_staf
        ])

        # =========================
        # UPDATE STAF
        # =========================
        cursor.execute("""
            UPDATE STAF
            SET kode_maskapai = %s
            WHERE email = %s
        """, [
            kode_maskapai,
            email_staf
        ])

        conn.commit()

        return JsonResponse({
            'success': True,
            'message': 'Profil staf berhasil diperbarui'
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

@csrf_exempt
def ubah_password_staf(request):

    email_staf = request.session.get('email')

    conn = get_connection()
    cursor = conn.cursor()

    try:

        data = json.loads(request.body)

        password_lama = data.get('password_lama')
        password_baru = data.get('password_baru')

        # ambil password lama
        cursor.execute("""
            SELECT password
            FROM PENGGUNA
            WHERE email = %s
        """, [email_staf])

        row = cursor.fetchone()

        if not row:

            return JsonResponse({
                'success': False,
                'message': 'User tidak ditemukan'
            }, status=404)

        hashed_password = row[0]

        # cek password lama
        if not check_password(
            password_lama,
            hashed_password
        ):

            return JsonResponse({
                'success': False,
                'message': 'Password lama salah'
            }, status=400)

        # hash password baru
        new_hashed_password = make_password(
            password_baru
        )

        # update password
        cursor.execute("""
            UPDATE PENGGUNA
            SET password = %s
            WHERE email = %s
        """, [
            new_hashed_password,
            email_staf
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