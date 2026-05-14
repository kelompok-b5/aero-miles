from django.urls import path
from . import views

urlpatterns = [
    path('redeem-hadiah/', views.redeem_hadiah, name='redeem-hadiah'),
    path('beli-package/', views.beli_package, name='beli-package'),
    path('info-tier/', views.info_tier, name='info-tier'),
    path('transfer-miles/', views.transfer_miles, name='transfer-miles'),
    path('claim-member/', views.claim_member, name='claim-member'),
    path('profil/', views.profil, name='profil'),
    path('dashboard-member/', views.dashboard_member, name='dashboard-member'),
    path('identitas/', views.identitas, name='identitas'),
]