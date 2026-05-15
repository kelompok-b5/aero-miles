from django.urls import path
from . import views

app_name = 'member' 

urlpatterns = [
    path('redeem-hadiah/', views.redeem_hadiah, name='redeem-hadiah'),
    path('redeem-hadiah/post/', views.redeem_hadiah_post, name='redeem-hadiah-post'),
    path('beli-package/', views.beli_package, name='beli-package'),
    path('beli-package/post/', views.beli_package_post, name='beli-package-post'), 
    path('info-tier/', views.info_tier, name='info-tier'),
    path('transfer-miles/', views.transfer_miles, name='transfer-miles'),
    path('transfer-miles/create/',  views.transfer_create,      name='transfer-create'),    
    path('claim-member/', views.claim_member, name='claim-member'),        
    path('claim-member/create/', views.claim_create, name='claim-create'),        
    path('claim-member/edit/<int:klaim_id>/', views.claim_edit, name='claim-edit'),      
    path('claim-member/delete/<int:klaim_id>/', views.claim_delete, name='claim-delete'),   
    path('profil/', views.profil, name='profil'),
    path('profil/update/', views.update_profil, name='update_profil'),
    path('profil/ubah-password/', views.ubah_password, name='ubah_password'),
    path('dashboard-member/', views.dashboard_member, name='dashboard-member'),
    path('identitas/', views.identitas, name='identitas'),
    path('validate-member-email/', views.validate_member_email, name='validate-member-email'),
    path('identitas/create/', views.identitas_create, name='identitas-create'),
    path('identitas/edit/<str:nomor>/', views.identitas_edit, name='identitas-edit'),
    path('identitas/delete/<str:nomor>/', views.identitas_delete, name='identitas-delete'),
]