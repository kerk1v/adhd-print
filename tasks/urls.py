from django.urls import path
from . import views

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('tasks/', views.task_list, name='task_list'),
    path('tasks/create/', views.task_create, name='task_create'),
    path('tasks/create/modal/', views.task_create_modal, name='task_create_modal'),
    path('tasks/create/<int:parent_id>/', views.task_create, name='task_create'),
    path('tasks/edit/<int:task_id>/', views.task_edit, name='task_edit'),
    path(
        'tasks/edit/modal/<int:task_id>/',
        views.task_edit_modal,
        name='task_edit_modal'),
    path('tasks/delete/<int:task_id>/', views.task_delete, name='task_delete'),
    path(
        'tasks/delete/modal/<int:task_id>/',
        views.task_delete_modal,
        name='task_delete_modal'),
    path(
        'tasks/toggle/<int:task_id>/',
        views.task_toggle_done,
        name='task_toggle_done'),
    path('tasks/print/<int:task_id>/', views.task_print, name='task_print'),
    path('tasks/api/task/<int:task_id>/', views.task_api, name='task_api'),
    path('tasks/generate-escpos-graphics/', views.generate_escpos_graphics, name='generate_escpos_graphics'),
    path('profile/', views.user_profile, name='user_profile'),
    path('users/api/profile/', views.user_profile_api, name='user_profile_api'),
    path('profile/save-printer-settings/', views.save_printer_settings, name='save_printer_settings'),
    path('profile/test-printer/', views.test_printer_connection, name='test_printer_connection'),
    path('tasks/today/', views.todays_tasks, name='todays_tasks'),
    path('tasks/today/print/', views.print_todays_tasks, name='print_todays_tasks'),
]
