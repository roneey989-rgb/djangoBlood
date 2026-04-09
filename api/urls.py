from django.urls import path
from .views import *

urlpatterns = [
    path('status/',serv_status),
    path('signup/', signup),
    path('login/', login),
    path('set-role/', set_role),
    path('create-donor/', create_donor),
    path('create_appointment/', create_appointment),
    path('search_blood/', search_blood),
    path('create_request/', create_request),
    path('create_doctor/',create_doctor),
    path('check_appointment/', check_appointment),
    path('add_verification/', add_verification),
    path('create_hospital/', create_hospital),
    path('check_verification/', check_verification),
    path('add_blood_packet/', add_blood_packet),
    path('add_blood_usage/',add_blood_usage),
    path('hospital_stock/',hospital_blood_stock),
    path('hospital_usage/',hospital_usage_table),
    path('hospital_find/',hospital_find_blood),
    path('ai-health/', ai_health),
    path('get_notifications/',get_notifications),
]