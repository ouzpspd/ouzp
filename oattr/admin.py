from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from .models import OtpmSpp, OtpmTR, HoldPosition, UserHoldPosition

admin.site.register(OtpmSpp)
admin.site.register(OtpmTR)

admin.site.register(HoldPosition)


class HoldPositionInline(admin.TabularInline):
    model = UserHoldPosition


class MyUserAdmin(UserAdmin):
    inlines = (HoldPositionInline,)
#
admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)