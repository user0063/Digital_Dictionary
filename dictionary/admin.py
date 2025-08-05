# dictionary/admin.py

from django.contrib import admin
from .models import CustomUser, Word, History, Bookmark
from django.contrib.auth.admin import UserAdmin
from django.forms import ModelForm
from django import forms

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'name', 'is_staff', 'is_superuser']
    fieldsets = (
        (None, {'fields': ('email', 'name', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'fields': ('email', 'name', 'password1', 'password2'),
        }),
    )
    ordering = ('email',)
    search_fields = ('email', 'name')
    filter_horizontal = ()

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Word)
admin.site.register(History)
admin.site.register(Bookmark)
