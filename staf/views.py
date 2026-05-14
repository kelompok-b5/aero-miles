from django.shortcuts import render

def dashboard_staf(request):
    return render(request, 'staf/dashboard-staf.html')

def claim_staff(request):
    return render(request, 'staf/claim-staff.html')

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