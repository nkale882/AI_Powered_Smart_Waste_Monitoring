from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views


router = DefaultRouter()
urlpatterns = [
    path('', views.home, name='home'),
    path('admin_user/home/', views.admin_home, name='admin_home'),
    path('crew/home/', views.crews_home, name='crew_home'),

    # Auth APIs
    path('api/signup/admin/', views.signup_admin, name='signup_admin'),
    path('api/signup/crew/', views.signup_crew, name='signup_crew'),
    path('api/login/admin/', views.login_admin, name='login_admin'),
    path('api/login/crew/', views.login_crew, name='login_crew'),

    path('api/viewcrews/', views.view_crews, name='view_crews'),
    path('api/detections/', views.detection_list_api, name='detection_list_api'),


]