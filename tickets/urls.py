from .views import *
from django.urls import path


urlpatterns = [
    path('', private_page, name='private_page'),
    path('commercial', commercial, name='commercial'),
    path('pto', pto, name='pto'),
    path('wait', wait, name='wait'),
    path('all_com_pto_wait', all_com_pto_wait, name='all_com_pto_wait'),
    path('sppdata/<int:trID>/', sppdata, name='sppdata'),
    path('vols/<int:trID>/', vols, name='vols'),
    path('copper/<int:trID>/', copper, name='copper'),
    path('wireless/<int:trID>/', wireless, name='wireless'),
    path('csw/<int:trID>/', csw, name='csw'),
    path('data/<int:trID>/', data, name='data'),
    path('unsaved_data', unsaved_data, name='unsaved_data'),
    path('saved_data/<int:trID>/', saved_data, name='saved_data'),
    path('hotspot/<int:trID>/', hotspot, name='hotspot'),
    path('cks/<int:trID>/', cks, name='cks'),
    path('shpd/<int:trID>/', shpd, name='shpd'),
    path('portvk/<int:trID>/', portvk, name='portvk'),
    path('portvm/<int:trID>/', portvm, name='portvm'),
    path('video/<int:trID>/', video, name='video'),
    path('phone/<int:trID>/', phone, name='phone'),
    path('local/<int:trID>/', local, name='local'),
    path('vgws/<int:trID>/', vgws, name='vgws'),
    path('registration', registration, name='register'),
    path('login/', user_login, name='login'),
    path('logout/', user_logout, name='logout'),
    path('change_password/', change_password, name='change_password'),
    path('ortr/', ortr, name='ortr'),
    path('<int:dID>/', spp_view, name='spp_view'),
    path('<int:dID>/<int:tID>/<int:trID>/', tr_view, name='tr_view'),
    path('itv/<int:trID>/', itv, name='itv'),
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
    path('send/<int:trID>/', send_to_spp, name='send_to_spp'),
    path('contract/<int:trID>/', get_resources, name='get_resources'),
    path('resources/<int:trID>/', resources_formset, name='resources_formset'),
    path('static_formset/', static_formset, name='static_formset'),
    path('forming_head/<int:trID>/', forming_header, name='forming_header'),
    path('chain_head/<int:trID>/', forming_chain_header, name='forming_chain_header'),
    path('head/<int:trID>/', head, name='head'),
    path('project_tr_exist_cl/<int:trID>/', project_tr_exist_cl, name='project_tr_exist_cl'),
    path('pass_serv/<int:trID>/', pass_serv, name='pass_serv'),
    path('pass_video/<int:trID>/', PassVideoFormView.as_view(), name='pass_video'),
    path('pass_turnoff/<int:trID>/', pass_turnoff, name='pass_turnoff'),
    path('change_log_shpd/<int:trID>/', change_log_shpd, name='change_log_shpd'),
    path('change_serv/<int:trID>/', change_serv, name='change_serv'),
    path('change_params_serv/<int:trID>/', change_params_serv, name='change_params_serv'),
    path('params_extend_service/<int:trID>/', params_extend_service, name='params_extend_service'),
    path('job_formset/<int:trID>/', job_formset, name='job_formset'),
    path('contract_id_formset/<int:trID>/', contract_id_formset, name='contract_id_formset'),
    path('search/', search, name='search'),
    path('title/<int:trID>/', title_tr, name='title_tr'),
    path('get_title_tr/', get_title_tr, name='get_title_tr'),
    path('free_ppr/', free_ppr, name='free_ppr'),
    path('ppr/<int:trID>/', ppr, name='ppr'),
    path('create_ppr/<int:trID>/', create_ppr, name='create_ppr'),
    path('ppr_resources/<int:trID>/', add_resources_to_ppr, name='add_resources_to_ppr'),
    path('ppr_result/<int:trID>/', ppr_result, name='ppr_result'),
    path('author_id_formset/<int:trID>/', author_id_formset, name='author_id_formset'),
    path('add_comment/<int:dID>/', add_comment_to_return_ticket, name='add_comment_to_return_ticket'),
    path('export_xls', export_xls, name='export_xls'),
    path('report_time_tracking/', report_time_tracking, name='report_time_tracking'),
    path('send_to_otpm_control/<int:dID>/', send_ticket_to_otpm_control, name='send_ticket_to_otpm_control'),
    path('rtk/<int:trID>/', RtkFormView.as_view(), name='rtk'),
    path('mko/', MkoView.as_view(), name='mko'),
    path('specification/<int:trID>/', CreateSpecificationView.as_view(), name='specification'),
    path('pps/<int:trID>/', PpsFormView.as_view(), name='pps'),
    path('spec_objects/<int:trID>/', spec_objects, name='spec_objects'),
    path('ppr_check/', ppr_check, name='ppr_check'),
    path('perform_ppr_check/<int:id_ppr>/', perform_ppr_check, name='perform_ppr_check'),
    path('rezerv_1g/', rezerv_1g, name='rezerv_1g'),
    path('analysis_switch_ports/<str:search_ip>/', analysis_switch_ports, name='analysis_switch_ports'),
    path('add_rezerv_1g_switch_ports/<str:search_ip>/', add_rezerv_1g_switch_ports, name='add_rezerv_1g_switch_ports'),
    path('remove_rezerv_1g_switch_ports/<str:search_ip>/', remove_rezerv_1g_switch_ports, name='remove_rezerv_1g_switch_ports'),
    path('dwdm/', dwdm, name='dwdm'),
    path('dwdm/submit/', dwdm_submit_form, name='dwdm_submit_form'),
    path('<str:room_name>/', room, name='room'),

    # path('otpm/', OtpmPoolView.as_view(), name='otpm'),
    # #path('otpm/create_spp/<int:dID>/', create_spp, name='create_spp'),
    # path('otpm/create_spp/<int:dID>/', CreateSppView.as_view(), name='create_spp'),
    # #path('otpm/db/<int:dID>-<int:ticket_spp_id>/', spp_view_oattr, name='spp_view_oattr'),
    # path('otpm/db/<int:dID>/', SppView.as_view(), name='spp_view_oattr'),
    # # path('otpm/remove/<int:ticket_spp_id>/', remove_spp_process_oattr, name='remove_spp_process_oattr'),
    # # path('otpm/remove_wait/<int:ticket_spp_id>/', remove_spp_wait_oattr, name='remove_spp_wait_oattr'),
    # # path('otpm/add_spp_wait/<int:ticket_spp_id>/', add_spp_wait_oattr, name='add_spp_wait_oattr'),
]
