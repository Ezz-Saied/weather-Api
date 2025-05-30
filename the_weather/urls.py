
from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('weather.urls')),
    path('hardware/add_device/', lambda request: HttpResponse(''), name='add_device'),
    path('hardware/list_devices/', lambda request: HttpResponse(''), name='list_devices'),
]
