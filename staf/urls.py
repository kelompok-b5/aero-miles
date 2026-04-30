from django.urls import path
from . import views

urlpatterns = [
    path('dashboard-staf/', views.dashboard_staf, name='dashboard-staf'),
    path('claim-staff/', views.claim_staff, name='claim-staff'),
    path('kelola-hadiah/', views.kelola_hadiah, name='kelola-hadiah'),
    path('kelola-member/', views.kelola_member, name='kelola-member'),
    path('kelola-mitra/', views.kelola_mitra, name='kelola-mitra'),
    path('laporan-transaksi/', views.laporan_transaksi, name='laporan-transaksi'),
    path('login/', views.login, name='login-staf'),
    path('profile-staf/', views.profile_staf, name='profile-staf'),
]