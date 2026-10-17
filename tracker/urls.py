from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard_alias'),
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('log-food/', views.log_food_view, name='log_food'),
    path('delete-food-log/<int:log_id>/', views.delete_food_log_view, name='delete_food_log'),
    path('update-water/', views.update_water_view, name='update_water'),
    path('foods/', views.foods_list_view, name='foods_list'),
    path('foods/add/', views.add_custom_food_view, name='add_custom_food'),
    path('history/', views.history_view, name='history'),
    path('api/food/<int:food_id>/', views.api_food_detail, name='api_food_detail'),
]
