from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('complete-task/<int:task_id>/', views.complete_task, name='complete_task'),
    path('reschedule-tasks/', views.reschedule_tasks, name='reschedule_tasks'),
    path('update-user-role/<int:user_id>/', views.update_user_role, name='update_user_role'),
    path('run-generator/', views.run_generator_view, name='run_generator'),
    path('download-timetable/', views.download_timetable, name='download_timetable'),
    path('download-locations/', views.download_location_sheet, name='download_location_sheet'),
    path('manage-data/', views.manage_data, name='manage_data'),
    path('add/<str:model_name>/', views.add_data, name='add_data'),
    path('edit/<str:model_name>/<int:pk>/', views.edit_data, name='edit_data'),
    path('delete/<str:model_name>/<int:pk>/', views.delete_data, name='delete_data'),
]