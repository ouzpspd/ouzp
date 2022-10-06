from .views import *
from django.urls import path


urlpatterns = [
    path('', private_page, name='private_page'),
    path('commercial', commercial, name='commercial'),
    path('pto', pto, name='pto'),
    path('wait', wait, name='wait'),
    path('all_com_pto_wait', all_com_pto_wait, name='all_com_pto_wait'),
    #path('inputtr', inputtr, name='inputtr'),
    path('sppdata', sppdata, name='sppdata'),
    path('vols', vols, name='vols'),
    path('copper', copper, name='copper'),
    path('wireless', wireless, name='wireless'),
    path('csw', csw, name='csw'),
    path('data', data, name='data'),
    path('unsaved_data', unsaved_data, name='unsaved_data'),
    path('saved_data', saved_data, name='saved_data'),
    path('hotspot', hotspot, name='hotspot'),
    path('cks', cks, name='cks'),
    path('shpd', shpd, name='shpd'),
    path('portvk', portvk, name='portvk'),
    path('portvm', portvm, name='portvm'),
    path('video', video, name='video'),
    path('phone', phone, name='phone'),
    path('local', local, name='local'),
    path('lvs', lvs, name='lvs'),
    path('sks', sks, name='sks'),
    path('vgws', vgws, name='vgws'),
    path('registration', registration, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('change_password/', change_password, name='change_password'),
    path('login_for_service/', login_for_service, name='login_for_service'),
    path('ortr', ortr, name='ortr'),
    path('<int:dID>/', spp_view, name='spp_view'),
    path('<int:dID>/<int:tID>/<int:trID>/', tr_view, name='tr_view'),
    path('itv', itv, name='itv'),
    path('get_link_tr', get_link_tr, name='get_link_tr'),
    path('proj/<int:dID>/<int:tID>/<int:trID>/', project_tr, name='project_tr'),
    path('add_spp/<int:dID>/', add_spp, name='add_spp'),
    path('db/<int:dID>-<int:ticket_spp_id>/', spp_view_save, name='spp_view_save'),
    path('db/<int:dID>-<int:ticket_spp_id>/<int:trID>/', edit_tr, name='edit_tr'),
    path('dbtr/<int:dID>-<int:ticket_spp_id>/<int:trID>/', tr_view_save, name='tr_view_save'),
    path('remove/<int:ticket_spp_id>/', remove_spp_process, name='remove_spp_process'),
    path('remove_wait/<int:ticket_spp_id>/', remove_spp_wait, name='remove_spp_wait'),
    path('add_spp_wait/<int:ticket_spp_id>/', add_spp_wait, name='add_spp_wait'),
    path('add_tr/<int:dID>/<int:tID>/<int:trID>/', add_tr, name='add_tr'),
    path('manually_tr/<int:dID>/<int:tID>/<int:trID>/', manually_tr, name='manually_tr'),
    path('send/', send_to_spp, name='send_to_spp'),
    path('contract/', get_resources, name='get_resources'),
    path('resources/', resources_formset, name='resources_formset'),
    path('static_formset/', static_formset, name='static_formset'),
    path('forming_head/', forming_header, name='forming_header'),
    path('chain_head/', forming_chain_header, name='forming_chain_header'),
    path('head/', head, name='head'),
    path('add_tr_exist_cl/<int:dID>/<int:tID>/<int:trID>/', add_tr_exist_cl, name='add_tr_exist_cl'),
    path('project_tr_exist_cl/', project_tr_exist_cl, name='project_tr_exist_cl'),
    path('pass_serv', pass_serv, name='pass_serv'),
    path('pass_turnoff/', pass_turnoff, name='pass_turnoff'),
    path('change_log_shpd', change_log_shpd, name='change_log_shpd'),
    path('change_serv', change_serv, name='change_serv'),
    path('change_params_serv', change_params_serv, name='change_params_serv'),
    path('params_extend_service', params_extend_service, name='params_extend_service'),
    path('job_formset/', job_formset, name='job_formset'),
    path('contract_id_formset/', contract_id_formset, name='contract_id_formset'),
    path('search/', search, name='search'),
    path('title/', title_tr, name='title_tr'),
    path('get_title_tr/', get_title_tr, name='get_title_tr'),
    path('add_tr_not_required/<int:dID>/<int:tID>/<int:trID>/', add_tr_not_required, name='add_tr_not_required'),
]
