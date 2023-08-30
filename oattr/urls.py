from . import views
from django.urls import path


urlpatterns = [
    path('', views.OtpmPoolView.as_view(), name='otpm'),
    path('create_spp/<int:dID>/', views.CreateSppView.as_view(), name='create_spp'),
    path('db/<int:dID>/send/', views.SendSppFormView.as_view(), name='send_spp'),
    path('db/<int:dID>/', views.SppView.as_view(), name='spp_view_oattr'),
    path('copper/<int:trID>/', views.CopperFormView.as_view(), name='otpm_copper'),
    path('create_project_otu/<int:trID>/', views.CreateProjectOtuView.as_view(), name='create_project_otu'),
    path('add_tr/<int:dID>/<int:tID>/<int:trID>/', views.CreateTrView.as_view(), name='add_tr_oattr'),
    path('data/<int:trID>/', views.data, name='otpm_data'),
    #path('tentura/', views.tentura, name='tentura'),
    path('save_spp/', views.save_spp, name='save_spp'),
    path('saved_data/<int:trID>/', views.saved_data_oattr, name='saved_data_oattr'),
    #path('service/<int:trID>/', views.ServiceFormView.as_view(), name='otpm_service'),
]