from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

# Register your models here.
from .models import *

admin.site.register(TR)
admin.site.register(SPP)
admin.site.register(ServicesTR)
admin.site.register(OrtrTR)
admin.site.register(HoldPosition)

class HoldPositionInline(admin.TabularInline):
    model = UserHoldPosition


class MyUserAdmin(UserAdmin):
    inlines = (HoldPositionInline,)
#
admin.site.unregister(User)
admin.site.register(User, MyUserAdmin)