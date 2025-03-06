from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class UserAdminForm(forms.ModelForm):
    class Meta:
        model = User
        fields = '__all__'

class CustomUserAdmin(UserAdmin):
    form = UserAdminForm
    list_display = ('uuid', 'email', 'name', 'balance', 'is_staff')
    search_fields = ('email', 'name')
    ordering = ('email',)

admin.site.register(User)
