from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('add_favorite/<int:city_id>/', views.add_favorite, name='add_favorite'),
    path('remove_favorite/<int:city_id>/', views.remove_favorite, name='remove_favorite'),
    path('profile/', views.user_profile, name='profile'),
]
