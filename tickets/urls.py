from .views import *
from django.urls import path


urlpatterns = [
    path('', private_page, name='private_page'),
    path('index', index, name='index'),
    path('commercial', commercial, name='commercial'),
    path('pto', pto, name='pto'),
    path('wait', wait, name='wait'),
    path('all_com_pto_wait', all_com_pto_wait, name='all_com_pto_wait'),
    path('tr/<int:ticket_tr>-<int:ticket_id>/', get_tr, name='get_tr'),
    #path('cfg_ports', cfg_ports, name='cfg_ports'),
    #path('ports', ports, name='ports'),
    #path('datatr', datatr, name='datatr'),
    #path('inputtr', inputtr, name='inputtr'),
    path('sppdata', sppdata, name='sppdata'),
    path('vols', vols, name='vols'),
    path('copper', copper, name='copper'),
    path('wireless', wireless, name='wireless'),
    path('csw', csw, name='csw'),
    path('data', data, name='data'),
    path('unsaved_data', unsaved_data, name='unsaved_data'),
    path('saved_data', saved_data, name='saved_data'),
    path('flush', flush_session, name='flush'),
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
    path('register', register, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('login_for_service/', login_for_service, name='login_for_service'),
    path('ortr', ortr, name='ortr'),
    path('<int:dID>/', spp_view, name='spp_view'),
    path('<int:dID>/<int:tID>/<int:trID>/', tr_view, name='tr_view'),
    path('itv', itv, name='itv'),
    path('trtr', trtr, name='trtr'),
    path('sppjson/', spp_json, name='spp-json-view'),
    path('spinner/', tr_spin, name='tr_spin'),
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
    path('show_resources/', show_resources, name='show_resources'),
    path('chain/', get_chain, name='get_chain'),
    path('show-chains/', show_chains, name='show_chains'),
    path('test/', test_formset, name='test_formset'),
    path('forming_head/', forming_header, name='forming_header'),
    path('chain_head/', forming_chain_header, name='forming_chain_header'),
    path('head/', head, name='head'),
    path('no_data/', no_data, name='no_data'),
    path('passage/', passage, name='passage'),
    path('add_tr_exist_cl/<int:dID>/<int:tID>/<int:trID>/', add_tr_exist_cl, name='add_tr_exist_cl'),
    path('project_tr_exist_cl/', project_tr_exist_cl, name='project_tr_exist_cl'),
    path('pass_serv/', pass_serv, name='pass_serv'),
    path('exist_cl_data/', exist_cl_data, name='exist_cl_data'),
    path('add_serv_with_install_csw/', add_serv_with_install_csw, name='add_serv_with_install_csw'),
    path('change_serv/', change_serv, name='change_serv'),
    path('change_params_serv/', change_params_serv, name='change_params_serv'),

    #path('send/<int:dID>/<int:tID>/<int:trID>/', send_to_spp, name='send_to_spp'),
]
