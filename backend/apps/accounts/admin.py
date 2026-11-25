from django.contrib import admin

from .models import PasswordResetCode, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "name", "is_guest", "is_active", "is_blocked", "date_joined")
    list_filter = ("is_guest", "is_active", "is_blocked")
    search_fields = ("email", "name")


admin.site.register(PasswordResetCode)
