from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # New URLs for cascading filters
    path('get_streams/', views.get_streams, name='get_streams'),
    path('get_semesters_and_divisions/', views.get_semesters_and_divisions, name='get_semesters_and_divisions'),
    
    # New URLs for manual timetable management
    path('manage/timetable/', views.manage_timetable, name='manage_timetable'),
    
    # URLs for the timetable generator
    path('run-generator/', views.run_generator_view, name='run_generator'),
    
    # URLs for downloading data
    path('download-timetable/', views.download_timetable, name='download_timetable'),
    path('download-locations/', views.download_location_sheet, name='download_location_sheet'),
    
    # URLs for the new data management structure
    path('manage-data/', views.manage_data, name='manage_data'),
    path('manage/professors/', views.manage_professor_list, name='manage_professor_list'),
    path('manage/streams/', views.manage_stream_list, name='manage_stream_list'),
    path('manage/locations/', views.manage_location_list, name='manage_location_list'),
    path('manage/subjects/', views.manage_subject_list, name='manage_subject_list'),
    path('manage/departments/', views.manage_department_list, name='manage_department_list'),
    path('manage/timeslots/', views.manage_timeslot_list, name='manage_timeslot_list'),
    path('manage/users/', views.manage_user_list, name='manage_user_list'),
    
    # Re-routed URLs for CRUD operations
    path('add/<str:model_name>/', views.add_data, name='add_data'),
    path('edit/<str:model_name>/<int:pk>/', views.edit_data, name='edit_data'),
    path('delete/<str:model_name>/<int:pk>/', views.delete_data, name='delete_data'),
    
    # URL for user role management
    path('update-user-role/<int:user_id>/', views.update_user_role, name='update_user_role'),
    
    # API endpoints for the manual timetable management module
    path('api/get_timetable_setup/', views.get_timetable_setup, name='api_get_timetable_setup'),
    path('api/get_timetable_data/', views.get_timetable_data, name='api_get_timetable_data'),
    path('api/get_subjects/', views.get_subjects, name='api_get_subjects'),
    path('api/get_professors/', views.get_professors, name='api_get_professors'),
    path('api/get_locations/', views.get_locations, name='api_get_locations'),
    path('api/save_timetable_entry/', views.save_timetable_entry, name='api_save_timetable_entry'),
    path('api/delete_timetable_entry/', views.delete_timetable_entry, name='api_delete_timetable_entry'),
]