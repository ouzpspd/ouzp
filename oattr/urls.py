from . import views
from django.urls import path


urlpatterns = [
    path('', views.OtpmPoolView.as_view(), name='otpm'),
    #path('otpm/create_spp/<int:dID>/', create_spp, name='create_spp'),
    path('create_spp/<int:dID>/', views.CreateSppView.as_view(), name='create_spp'),
    #path('otpm/db/<int:dID>-<int:ticket_spp_id>/', spp_view_oattr, name='spp_view_oattr'),
    path('db/<int:dID>/send/', views.SendSppFormView.as_view(), name='send_spp'),
    path('db/<int:dID>/', views.SppView.as_view(), name='spp_view_oattr'),
    # path('otpm/remove/<int:ticket_spp_id>/', remove_spp_process_oattr, name='remove_spp_process_oattr'),
    # path('otpm/remove_wait/<int:ticket_spp_id>/', remove_spp_wait_oattr, name='remove_spp_wait_oattr'),
    # path('otpm/add_spp_wait/<int:ticket_spp_id>/', add_spp_wait_oattr, name='add_spp_wait_oattr'),
    #path('copper/', views.copper_view, name='otpm_copper'),


    path('copper/', views.CopperFormView.as_view(), name='otpm_copper'),
    path('create_project_otu/<int:trID>/', views.create_project_otu, name='create_project_otu'),
    path('add_tr/<int:dID>/<int:tID>/<int:trID>/', views.add_tr_oattr, name='add_tr_oattr'),
    path('data/', views.data, name='otpm_data'),
    path('save_spp/', views.save_spp, name='save_spp'),
    path('saved_data/', views.saved_data_oattr, name='saved_data_oattr'),

]