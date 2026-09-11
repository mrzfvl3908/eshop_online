from django.urls import path
from . import views

app_name = 'accounts_app'

urlpatterns = [
    path('login/', views.user_login, name='login'),
]