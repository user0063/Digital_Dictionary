from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home_view, name='home'),
     path('bookmark/add/<int:word_id>/', views.add_bookmark, name='add_bookmark'),
path('bookmarks/', views.bookmarks_view, name='bookmarks'),
path('remove-bookmark/<int:word_id>/', views.remove_bookmark, name='remove_bookmark'),

    path('history/', views.history_view, name='history'),
    
]
