from django.contrib import admin
from django.urls import path, include
from dictionary.views import create_admin_user
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dictionary.urls')),
     path("create-admin/", create_admin_user),
]
