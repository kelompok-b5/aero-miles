from pyexpat.errors import messages

from django.shortcuts import redirect, render

from aeromiles.db import get_connection

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
    return render(request, 'staf/laporan-transaksi.html')

def profile_staf(request):
    return render(request, 'staf/profile-staf.html')