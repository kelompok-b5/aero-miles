from django.urls import path
from . import views

urlpatterns = [
    path('dashboard-staf/', views.dashboard_staf, name='dashboard-staf'),
    path('claim-staff/', views.claim_staff, name='claim-staff'),
    path('kelola-hadiah/', views.kelola_hadiah, name='kelola-hadiah'),
    path('kelola-hadiah/tambah/', views.tambah_hadiah, name='tambah-hadiah'),
    path('kelola-hadiah/edit/', views.edit_hadiah, name='edit-hadiah'),
    path('kelola-hadiah/hapus/', views.hapus_hadiah, name='hapus-hadiah'),
    path('kelola-member/', views.kelola_member, name='kelola-member'),
    path('kelola-mitra/', views.kelola_mitra, name='kelola-mitra'),
    path('kelola-mitra/tambah/', views.tambah_mitra, name='tambah-mitra'),   
    path('kelola-mitra/edit/', views.edit_mitra, name='edit-mitra'),        
    path('kelola-mitra/hapus/', views.hapus_mitra, name='hapus-mitra'),  
    path('laporan-transaksi/', views.laporan_transaksi, name='laporan-transaksi'),
    path('profile-staf/', views.profile_staf, name='profile-staf'),
    path('profile-staf/update/', views.update_profile_staf, name='update-profile-staf'),
    path('profile-staf/ubah-password/', views.ubah_password_staf, name='ubah-password-staf'),
]