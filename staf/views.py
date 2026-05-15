from datetime import date

from django.shortcuts import render
from django.http import JsonResponse
from aeromiles.db import get_connection
from django.contrib.auth.hashers import check_password, make_password
import json
from django.views.decorators.csrf import csrf_exempt

def dashboard_staf(request):
    '''Menampilkan data dashboard staf dengan statistik klaim missing miles terkait maskapai yang dikelola.'''

    # sementara hardcoded dulu
    email_staf = request.session.get('email')

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
    return render(request, 'staf/claim-staff.html')

def kelola_hadiah(request):
    """
    Menampilkan halaman kelola hadiah beserta:
    - daftar hadiah
    - daftar penyedia
    - statistik total hadiah, hadiah aktif, hadiah nonaktif
    """
 
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
    return render(request, 'staf/kelola-member.html')

def kelola_mitra(request):
    """
    Menampilkan halaman Kelola Mitra beserta:
    - daftar mitra
    - jumlah hadiah aktif
    - statistik total mitra
    - statistik hadiah aktif
    - statistik mitra baru 30 hari terakhir
    """

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
    return render(request, 'staf/laporan-transaksi.html')

@csrf_exempt
def profile_staf(request):
    """
    Menampilkan data profil staf ke halaman profile-staf.html
    """

    # sementara hardcoded dulu
    email_staf = request.session.get('email')

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