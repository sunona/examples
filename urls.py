# -*- coding: utf-8 -*-
from django.conf.urls.defaults import *

from hotels.flight_views import AccommodationCalculateView
from hotels.views import ChangePeriodView, AddPeriodView


urlpatterns = patterns('hotels.views',
    url(r'^$', 'hotel_list', name='hotel_list'),    
    url(r'^import_rate_code/$', 'import_rate_code', name='import_rate_code'),
    url(r'^page-(?P<page>\d+)/$', 'hotel_list', name='hotel_list'),
    url(r'^set-child-policy-multiple/$', 'set_child_policy_multiple', 
        name='set_child_policy_multiple'),
    url(r'^hotel_supplier_add/(?P<hotel_pk>\d+)/$', 'hotel_supplier_add', name='hotel_supplier_add'),
    url(r'^hotel_supplier_copy/(?P<hotel_supplier_pk>\d+)/$', 'hotel_supplier_copy', name='hotel_supplier_copy'),
    
    url(r'^selected_hs_prices_publicate/$', 'selected_hs_prices_publicate', name='selected_hs_prices_publicate'),

    url(r'^(?P<hotel_supplier_pk>\d+)/edit/$', 'hotel_edit', name='hotel_edit'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-child-policy/$', 
        'set_child_policy', name='set_child_policy'),
    url(r'^(?P<hotel_supplier_pk>\d+)/change-child-policy/$', 
        'change_child_policy', name='change_child_policy'),

    url(r'^(?P<hotel_supplier_pk>\d+)/add-period/$', 'add_period', 
        name='add_period'),
    url(r'^change-period/(?P<period_pk>\d+)/$', ChangePeriodView.as_view(), 
        name='change_period'),
    url(r'^(?P<hotel_supplier_pk>\d+)/add-period-form/$', AddPeriodView.as_view(), 
        name='add_period_form'),
    url(r'^(?P<hotel_supplier_pk>\d+)/add-room-form/$', 'add_room_form', 
        name='add_room_form'),
    url(r'^(?P<hotel_supplier_pk>\d+)/add-meal-form/$', 'add_meal_form', 
        name='add_meal_form'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-checkinout/$', 'set_checkinout', 
        name='set_checkinout'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-agepolicy-form/$', 'set_agepolicy_form', 
        name='set_agepolicy_form'),
    url(r'^(?P<hotel_supplier_pk>\d+)/add-service/$', 'add_service', 
        name='add_service'),
    url(r'^(?P<hotel_supplier_pk>\d+)/add-surch/$', 'add_surch', 
        name='add_surch'),
    url(r'^(?P<hotel_supplier_pk>\d+)/add-service-related/$', 
        'add_service_related', name='add_service_related'),
    url(r'^(?P<hotel_supplier_pk>\d+)/delete-periods/$', 
        'delete_periods', name='delete_periods'),
    url(r'^(?P<hotel_supplier_pk>\d+)/delete-rates/$', 
        'delete_rates', name='delete_rates'),
    url(r'^(?P<hotel_supplier_pk>\d+)/delete-services/$', 
        'delete_services', name='delete_services'),
    url(r'^(?P<hotel_supplier_pk>\d+)/delete-meals/$', 
        'delete_meals', name='delete_meals'),
    url(r'^(?P<hotel_supplier_pk>\d+)/delete-staypays/$', 
        'delete_staypays', name='delete_staypays'),
    url(r'^(?P<hotel_supplier_pk>\d+)/delete-staypay-bonuses/$', 
        'delete_staypay_bonuses', name='delete_staypay_bonuses'),
    url(r'^(?P<hotel_supplier_pk>\d+)/delete-eb-rates/$', 
        'delete_eb_rates', name='delete_eb_rates'),
    url(r'^(?P<hotel_supplier_pk>\d+)/accommodations-autocomplete/$', 
        'accommodations_autocomplete', name='accommodations_autocomplete'),
    url(r'^(?P<room_pk>\d+)/(?P<hotel_supplier_pk>\d+)/accommodations-fill/$', 
        'accommodations_fill', name='accommodations_fill'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-meal/$', 
        'set_meal', name='set_meal'),
    url(r'^(?P<hotel_supplier_pk>\d+)/add-meal/$', 
        'add_meal', name='add_meal'),
    url(r'^(?P<hotel_supplier_pk>\d+)/change-meal/$', 
        'change_meal', name='change_meal'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-rate-cs/$', 
        'set_rate_cs', name='set_rate_cs'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-rate-cs-conditioned/$', 
        'set_rate_cs_conditioned', name='set_rate_cs_conditioned'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-rate-ml/$', 
        'set_rate_ml', name='set_rate_ml'),
    url(r'^(?P<hotel_supplier_pk>\d+)/change-rate-eb/$', 
        'change_rate_eb', name='change_rate_eb'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-rate-eb/$', 
        'set_rate_eb', name='set_rate_eb'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-rate-rb/$', 
        'set_rate_rb', name='set_rate_rb'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-rate-f/$', 
        'set_rate_f', name='set_rate_f'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-stay-pay/$', 
        'set_stay_pay', name='set_stay_pay'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-stay-pay-form/$', 
        'set_stay_pay_form', name='set_stay_pay_form'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-stay-pay-bonus/$', 
        'set_stay_pay_bonus', name='set_stay_pay_bonus'),
    url(r'^(?P<hotel_supplier_pk>\d+)/more-periods/$', 
        'more_periods', name='more_periods'),
    url(r'^(?P<hotel_supplier_pk>\d+)/add-company-room/$', 
        'add_company_room', name='add_company_room'),
    url(r'^(?P<hotel_supplier_pk>\d+)/delete-company-room/$', 
        'delete_company_rooms', name='delete_company_rooms'), 
    url(r'^(?P<hotel_supplier_pk>\d+)/change-company-room/$', 
        'change_company_rooms', name='change_company_rooms'), 
    url(r'^(?P<hotel_supplier_pk>\d+)/publicate-hotel-prices/$', 
        'publicate_hotel_prices', name='publicate_hotel_prices'), 
    url(r'^(?P<hotel_supplier_pk>\d+)/hotel-supplier-history/$', 
        'hotel_supplier_history', name='hotel_supplier_history'), 
    url(r'^(?P<hotel_supplier_pk>\d+)/hotel-supplier-public-version/$', 
        'hotel_supplier_public_version', name='hotel_supplier_public_version'), 

    url(r'^(?P<hotel_supplier_pk>\d+)/add-early-bird/$', 
        'add_early_bird', name='add_early_bird'),
    url(r'^(?P<hotel_supplier_pk>\d+)/add-bird-form/$', 
        'add_bird_form', name='add_bird_form'),
    url(r'^(?P<early_bird_hs_pk>\d+)/delete-early-bird/$', 
        'delete_early_bird', name='delete_early_bird'),
        
    url(r'^(?P<hotel_supplier_pk>\d+)/add-compulsory-service/$', 
        'add_compulsory_service', name='add_compulsory_service'),
    url(r'^(?P<hotel_supplier_pk>\d+)/add-compulsory-service-rate/(?P<service_pk>\d+)$', 
        'add_compulsory_service_rate', name='add_compulsory_service_rate'),
        
    url(r'^(?P<hotel_supplier_pk>\d+)/add-bonus-form/$', 
        'add_bonus_form', name='add_bonus_form'),
        
    url(r'^(?P<hotel_supplier_pk>\d+)/add-restr-earlybird/$', 
        'add_restr_form', {'for_obj': 'EB'}, name='add_restr_earlybird'),
    url(r'^(?P<hotel_supplier_pk>\d+)/del-restr-earlybird/$', 
        'del_all_restr', {'for_obj': 'EB'}, name='del_restr_earlybird'),
        
    url(r'^(?P<hotel_supplier_pk>\d+)/add-restr-bonus/$', 
        'add_restr_form', {'for_obj': 'B'}, name='add_restr_bonus'),
    url(r'^(?P<hotel_supplier_pk>\d+)/del-restr-bonus/$', 
        'del_all_restr', {'for_obj': 'B'}, name='del_restr_bonus'),

    url(r'^(?P<hotel_supplier_pk>\d+)/add-period-commision/$', 
        'add_period_commision', name='add_period_commision'), 
    url(r'^(?P<hotel_supplier_pk>\d+)/set-room-order/$', 
        'set_room_order', name='set_room_order'), 

    url(r'^set-meal-multiple/$', 'set_meal_multiple', name='set_meal_multiple'), 

    url(r'^room/(?P<room_pk>\d+)/(?P<hotel_supplier_pk>\d+)/accommodations/$', 
        'room_accommodations', name='room_accommodations'), 
    url(r'^room/(?P<room_pk>\d+)/(?P<company_pk>\d+)/min_age_and_occupancy_ajax/$', 
        'min_age_and_occupancy_ajax', name='min_age_and_occupancy_ajax'),
                
    url(r'^room/(?P<room_pk>\d+)/(?P<hotel_supplier_pk>\d+)/accommodations-public/$', 
        'room_accommodations_public', name='room_accommodations_public'), 
    url(r'^delete/$', 'delete_hotel_suppliers', name='delete_hotel_suppliers'),
    url(r'^(?P<hotel_supplier_pk>\d+)/in_hotel_edit_check_errors/$', 'in_hotel_edit_check_errors', name='in_hotel_edit_check_errors'),
    url(r'^check_commands/$', 'check_commands', name='check_commands'),
    url(r'^(?P<hotel_supplier_pk>\d+)/transfer_is_must/$', 'transfer_is_must', name='transfer_is_must'),
    url(r'^hotel-choose/$', 'hotel_choose', name='hotel_choose'),
    url(r'^hotel-load/$', 'hotel_load', name='hotel_load'),
)

 
# allotments & cancellation policy
urlpatterns += patterns('',
    url(r'^allotments/', include('allotments.urls')), 
    url(r'^cancellation-policy/', include('cancellation_policy.urls')), 
)


# meal rates
urlpatterns += patterns('hotels.meal_rate_views',
    url(r'^(?P<hotel_supplier_pk>\d+)/edit-meal-prices/$', 
        'edit_meal_prices', name='edit_meal_prices'),
)


# eb rates
urlpatterns += patterns('hotels.eb_rate_views',
    url(r'^(?P<hotel_supplier_pk>\d+)/(?P<type>(EB|RB))/edit-eb-prices/$', 
        'edit_eb_prices', name='edit_eb_prices'),
)
  
    
# room rates
urlpatterns += patterns('hotels.room_rate_views',
    url(r'^(?P<hotel_supplier_pk>\d+)/add-room-prices/$', 
        'add_room_prices', name='add_room_prices'),
    url(r'^(?P<hotel_supplier_pk>\d+)/add-room-prices-apply/$', 
        'add_room_prices_apply', name='add_room_prices_apply'),
    url(r'^(?P<hotel_supplier_pk>\d+)/edit-room-prices/$', 
        'edit_room_prices', name='edit_room_prices'),
    url(r'^(?P<hotel_supplier_pk>\d+)/edit-room-discounts/$', 
        'edit_room_discounts', name='edit_room_discounts'),

    url(r'^room-prices-for-rc/(?P<hs_rate_code_pk>\d+)/$', 
        'view_room_prices_for_rc', name='view_room_prices_for_rc'),

    url(r'^room-prices-for-rc/(?P<hs_rate_code_pk>\d+)/(?P<hotel_supplier_pk>\d+)/$', 
        'view_room_prices_for_rc', name='view_room_prices_for_rc_bird'),

    #as partner see
    url(r'^room-prices-for-rc-public/(?P<hs_rate_code_pk>\d+)/$', 
        'view_room_prices_for_rc_public', name='view_room_prices_for_rc_public'),

    url(r'^room-prices-for-rc-public/(?P<hs_rate_code_pk>\d+)/(?P<hotel_supplier_pk>\d+)/$', 
        'view_room_prices_for_rc_public', name='view_room_prices_for_rc_bird_public'),
    #end as partner see

    url(r'^public-room-prices/(?P<hotel_supplier_pk>\d+)/$', 
        'view_public_room_prices', name='view_public_room_prices'),    

    url(r'^room-prices-shared/(?P<hs_rate_code_pk>\d+)/$', 
        'view_shared_room_prices', name='view_shared_room_prices'),
    url(r'^room-prices-shared/(?P<hs_rate_code_pk>\d+)/(?P<hotel_supplier_pk>\d+)/$', 
        'view_shared_room_prices', name='view_shared_room_prices_bird'),

    url(r'^(?P<hotel_supplier_pk>\d+)/split-period/$', 
        'split_period', name='split_period'),             
)


# calculation
urlpatterns += patterns('hotels.flight_views',
    url(r'^(?P<hotel_supplier_pk>\d+)/flight-calculate/$', 
        'flight_calculate', name='flight_calculate'),   
    
    url(r'^(?P<hotel_supplier_pk>\d+)/accommodation-calculate/$', 
        AccommodationCalculateView.as_view(), name='accommodation_calculate'),
    
    url(r'^(?P<hotel_supplier_pk>\d+)/(?P<hs_rate_code_pk>\d+)/rc-accommodation-calculate/$',
        AccommodationCalculateView.as_view(), name='rc_accommodation_calculate'),
    
    url(r'^(?P<hs_rate_code_pk>\d+)/rc-flight-calculate/$', 
        'rc_flight_calculate', name='rc_flight_calculate'),
)


# rate codes
urlpatterns += patterns('hotels.rate_code_views',
    url(r'^get_ajax_data_hs_rc/(?P<hs_rate_code_pk>\d+)/$','get_ajax_data_hs_rc',name='get_ajax_data_hs_rc'),
    url(r'^get_ajax_data_hs/(?P<hs_pk>\d+)/$','get_ajax_data_hs',name='get_ajax_data_hs'),

    url(r'^selected_hs_connect_rc/$', 'selected_hs_connect_rc', name='selected_hs_connect_rc'),
    url(r'^selected_hsrc_connect_rc/$', 'selected_hsrc_connect_rc', name='selected_hsrc_connect_rc'),
    url(r'^all_shared_hsrc_connect_rc/$', 'all_shared_hsrc_connect_rc', name='all_shared_hsrc_connect_rc'),
    url(r'^(?P<hs_rate_code_pk>\d+)/rate-code-hotel/$', 
        'rate_code_hotel', name='rate_code_hotel'),
    url(r'^(?P<hs_rate_code_pk>\d+)/rate-code-hotel/(?P<hotel_supplier_pk>\d+)/$', 
        'rate_code_hotel', name='rate_code_hotel_bird'),
    url(r'^(?P<hs_rate_code_pk>\d+)/rate-code-hotel-public-version/$', 
        'rate_code_public_version', name='rate_code_public_version'),
    url(r'^(?P<hs_rate_code_pk>\d+)/rate-code-hotel-public-version/(?P<hotel_supplier_pk>\d+)/$', 
        'rate_code_public_version', name='rate_code_public_version_bird'),
    url(r'^(?P<hs_rate_code_pk>\d+)/shared-rate-code-hotel/$', 
        'shared_rate_code_hotel_supplier', name='shared_rate_code_hotel_supplier'),
    url(r'^(?P<hs_rate_code_pk>\d+)/shared-rate-code-hotel/(?P<hotel_supplier_pk>\d+)/$', 
        'shared_rate_code_hotel_supplier', name='shared_rate_code_hotel_supplier_bird'),
    url(r'^(?P<hs_rate_code_pk>\d+)/more-periods-rate/$', 
        'more_periods_for_rate', name='more_periods_for_rate'),
    url(r'^(?P<hotel_supplier_pk>\d+)/set-rate-code/$', 
        'set_rate_code', name='set_rate_code'),
    url(r'^(?P<hotel_supplier_pk>\d+)/connect-to-ratecode/$', 
        'connect_to_ratecode_form', name='connect_to_ratecode_form'),
    url(r'^(?P<hotel_supplier_pk>\d+)/(?P<hs_rate_code_pk>\d+)/connect-to-ratecode-for-shared-prices/$', 
        'connect_to_ratecode_form', name='connect_to_ratecode_for_shared_prices_form', kwargs={'for_shared_prices':1}),
    url(r'^set-rate-code-multiple/$', 
        'set_rate_code_multiple', name='set_rate_code_multiple'),
    url(r'^(?P<hs_rate_code_pk>\d+)/set-rate-code-shared/$', 
        'set_rate_code_for_shared_prices', name='set_rate_code_for_shared_prices'), 
    url(r'^(?P<hotel_supplier_pk>\d+)/check-transfers-rate-code/$', 
        'check_transfers_rate_code', name='check_transfers_rate_code'),           
) 
  

# bonuses
urlpatterns += patterns('',
    url(r'^(?P<hotel_supplier_pk>\d+)/bonuses/', 
        include('bonuses.urls')), 
)


# hotel features & description 
urlpatterns += patterns('hotels.views',
    url(r'^(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/hotel_features/$', 'hotel_features', name='hotel_features'),
    url(r'^(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/hotel_features_fancybox/$', 'hotel_features_fancybox', name='hotel_features_fancybox'),
    url(r'^(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/hotel_description/$', 'hotel_description_edit', name='hotel_description_edit'),
    url(r'^hotel_description/(?P<hotel_description_pk>\d+)/delete/$', 'hotel_description_delete', name='hotel_description_delete'),\
    
    # Вспомогательная универсальная функция, может вызываться как и из кода, так и возвращать результат в fancybox
    url(r'^(?P<hotel_supplier_pk>\d+)/get_hotel_description/$', 'hotel_description_get', name='hotel_description_get'),
    url(r'^(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/hotel_description_get_by_company/$', 'hotel_description_get', name='hotel_description_get_by_company'),
)


# room features
urlpatterns += patterns('hotels.views',
    url(r'^(?P<room_pk>\d+)/(?P<company_pk>\d+)/room_features/$', 'room_features', name='room_features'),
    url(r'^(?P<room_pk>\d+)/(?P<company_pk>\d+)/room_features_fancybox/$', 'room_features_fancybox', name='room_features_fancybox'),    
    url(r'^(?P<room_pk>\d+)/(?P<company_pk>\d+)/room_features_fancybox_without_auth/$', 'room_features_fancybox', kwargs={'without_auth':1},name='room_features_fancybox_without_auth'),    
    url(r'^(?P<room_pk>\d+)/(?P<company_pk>\d+)/room_description/$', 'room_description', name='room_description'),
    url(r'^room_description/(?P<room_description_pk>\d+)/delete/$', 'room_description_delete', name='room_description_delete'),    
    url(r'^(?P<room_pk>\d+)/(?P<company_pk>\d+)/room_description_fancybox/$', 'room_description_fancybox', name='room_description_fancybox'),
    url(r'^(?P<room_pk>\d+)/(?P<company_pk>\d+)/room_description_fancybox_without_auth/$', 'room_description_fancybox', kwargs={'without_auth':1}, name='room_description_fancybox_without_auth'),
)


# restaurant & bar features
urlpatterns += patterns('hotels.views',
    url(r'^(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/restaurant_and_bar/$', 'restaurant_and_bar', name='restaurant_and_bar'),
    url(r'^(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/add_restaurant_and_bar/$', 'add_restaurant_and_bar', name='add_restaurant_and_bar'),
    url(r'^(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/(?P<restaurant_and_bar_pk>\d+)/restaurant_and_bar_features/$', 'restaurant_and_bar_features', name='restaurant_and_bar_features'),
    url(r'^restaurant_and_bar/(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/(?P<restaurant_and_bar_pk>\d+)/delete/$', 'restaurant_and_bar_delete', name='restaurant_and_bar_delete'),
)


# hotel & room photos
urlpatterns += patterns('hotels.views',
    url(r'^(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/hotel_photo/$', 'hotel_photo', name='hotel_photo'),
    url(r'^hotel_photo/(?P<hotel_photo_pk>\d+)/delete/$', 'hotel_photo_delete', name='hotel_photo_delete'),    
    url(r'^(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/(?P<hotel_photo_pk>\d+)/hotel_photo_description/$', 'hotel_photo_description', name='hotel_photo_description'),
    url(r'^hotel_photo_description/(?P<hotel_photo_description_pk>\d+)/delete/$', 'hotel_photo_description_delete', name='hotel_photo_description_delete'), 
    url(r'^hotel_photo_fancybox/(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/$', 'hotel_photo_fancybox', name='hotel_photo_fancybox'),
    url(r'^show_popular_hotels_ajax/$', 'show_popular_hotels_ajax', name='show_popular_hotels_ajax'),
    url(r'^show_popular_hotels_ajax/start/$', 'show_popular_hotels_ajax', 
            {'start': True}, name='show_popular_hotels_ajax_start'),
    )
  
# hotel & room video
urlpatterns += patterns('hotels.views',
    url(r'^(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/hotel_video/$', 'hotel_video', name='hotel_video'),
    url(r'^hotel_video/(?P<hotel_video_pk>\d+)/delete/$', 'hotel_video_delete', name='hotel_video_delete'),    
    url(r'^(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/(?P<hotel_video_pk>\d+)/hotel_video_description/$', 'hotel_video_description', name='hotel_video_description'),
    url(r'^hotel_video_description/(?P<hotel_video_description_pk>\d+)/delete/$', 'hotel_video_description_delete', name='hotel_video_description_delete'), 
    )

# hotel files
urlpatterns += patterns('hotels.views',
    url(r'^(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/hotel_file/$', 'hotel_file', name='hotel_file'),
    url(r'^hotel_file/(?P<hotel_file_pk>\d+)/delete/$', 'hotel_file_delete', name='hotel_file_delete'),    
    url(r'^(?P<hotel_pk>\d+)/(?P<company_pk>\d+)/(?P<hotel_file_pk>\d+)/hotel_file_description/$', 'hotel_file_description', name='hotel_file_description'),
    url(r'^hotel_file_description/(?P<hotel_file_description_pk>\d+)/delete/$', 'hotel_file_description_delete', name='hotel_file_description_delete'), 
    )
    

# search urls 
urlpatterns += patterns('hotels.search', 
     url(r'^replace_country_catalog_ajax/$', 'replace_country_catalog_ajax', name='replace_country_catalog_ajax'),
    url(r'^delete_best_hotel/(?P<popular_hotel_pk>\d+)/$', 'work_with_popular_hotels',kwargs={'ajax_delete_best_hotel':5}, name='delete_best_hotel'), 
    url(r'^make-best-hotel/(?P<popular_hotel_pk>\d+)/$', 'work_with_popular_hotels',kwargs={'ajax_make_best_hotel':4}, name='make_best_hotel'), 
    url(r'^ajax_cascade_list/$', 'work_with_popular_hotels',kwargs={'ajax':3}, name='ajax_cascade_list'),    
    url(r'^popular_hotel_add/$', 'work_with_popular_hotels',kwargs={'add':2}, name='popular_hotel_add'),  
    url(r'^popular_hotel_delete/(?P<popular_hotel_pk>\d+)/delete/$', 'work_with_popular_hotels',kwargs={'delete':1}, name='popular_hotel_delete'),          
    url(r'^hotels-search/$', 'hotels_search', name='hotels_search'),   
    url(r'^hotels_search_ajax_autocomplete/$', 'hotels_search_ajax_autocomplete', name='hotels_search_ajax_autocomplete'),  
    url(r'^hotels_search_ajax_price/$', 'hotels_search_ajax_price',name="hotels_search_ajax_price"),     
    url(r'^hotel_search_ajax_rooms/$', 'hotels_search_ajax_rooms',name="hotels_search_ajax_rooms"), 
    url(r'^hotel_search_ajax_rooms_short/$', 'hotels_search_ajax_rooms_short',name="hotels_search_ajax_rooms_short"), 
    url(r'^(?P<country_link>\w+)/(?P<resort_title_en>\w+)/(?P<hotel_title>\w+)/$','hotels_search',kwargs={'direct_link': True},name='hotels_search_direct_link'),       
    url(r'^rate_code_request/$', 'rate_code_request', name='rate_code_request'),
)

    
urlpatterns += patterns('',
    url(r'^promo-discount/', include('bonuses.discount_urls')), 
)



urlpatterns += patterns('',
    url(r'^validity-terms/', 
        include('validity_terms.urls')), 
)


#temporary urls for sync hotel db
urlpatterns += patterns('hotels.views',
    url(r'^stat_country/$', 'stat_country', name='stat_country'),
    url(r'^sync_hotels/$', 'sync_hotels', name='sync_hotels'),
    url(r'^hotel_sync/$', 'hotel_sync', name='hotel_sync'),
    url(r'^check_hotel_ajax/$', 'check_hotel_ajax', name='check_hotel_ajax'),  
    url(r'^hotel_sync_links/$', 'hotel_sync_links', name='hotel_sync_links'), 
    url(r'^sync_hotels_booking/$', 'sync_hotels_booking', name='sync_hotels_booking'),
    url(r'^sync_hotels/hotel_list_for_sync/(?P<country_link>.+?)$', 'hotel_list_for_sync', name='hotel_list_for_sync'),
    url(r'^sync_hotels_booking/hotel_list_for_sync_booking/(?P<country_link>.+?)/(?P<public_status>.+?)$', 'hotel_list_for_sync_booking', name='hotel_list_for_sync_booking'),
    url(r'^fill_hotel_select/$', 'fill_hotel_select', name='fill_hotel_select'),
    url(r'^get_hotel_by_id/$', 'get_hotel_by_id', name='get_hotel_by_id'),
    url(r'^sync_hotel_ajax_operations/$', 'sync_hotel_ajax_operations', name='sync_hotel_ajax_operations'),
    url(r'^sync_hotels_list/$', 'sync_hotels_list', name='sync_hotels_list'),
    url(r'^get_hotel_in_work_ajax/$', 'get_hotel_in_work_ajax', name='get_hotel_in_work_ajax'), 
    url(r'^hotel_select_reload/$', 'hotel_select_reload', name='hotel_select_reload'),
    url(r'^cron_operations/$', 'cron_operations', name='cron_operations') 
)



