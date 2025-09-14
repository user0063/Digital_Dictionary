from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
        path('bookmarks/', views.bookmarks_view, name='bookmarks'),
    path('', views.home_view, name='home'),
      path('bookmark/<int:word_id>/', views.bookmark_word, name='bookmark_word'),
    path('unbookmark/<int:word_id>/', views.unbookmark_word, name='unbookmark_word'),

    path('history/', views.history_view, name='history'),
    
]
