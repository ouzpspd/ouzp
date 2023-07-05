from .views import *
from django.urls import path


urlpatterns = [
    path('', OtpmPoolView.as_view(), name='otpm'),
    #path('otpm/create_spp/<int:dID>/', create_spp, name='create_spp'),
    path('create_spp/<int:dID>/', CreateSppView.as_view(), name='create_spp'),
    #path('otpm/db/<int:dID>-<int:ticket_spp_id>/', spp_view_oattr, name='spp_view_oattr'),
    path('db/<int:dID>/', SppView.as_view(), name='spp_view_oattr'),
    # path('otpm/remove/<int:ticket_spp_id>/', remove_spp_process_oattr, name='remove_spp_process_oattr'),
    # path('otpm/remove_wait/<int:ticket_spp_id>/', remove_spp_wait_oattr, name='remove_spp_wait_oattr'),
    # path('otpm/add_spp_wait/<int:ticket_spp_id>/', add_spp_wait_oattr, name='add_spp_wait_oattr'),
    path('copper/', copper_view, name='otpm_copper'),
]