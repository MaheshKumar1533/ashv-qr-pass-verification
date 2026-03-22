from django.contrib import admin
from .models import GatePass, checkin, event
# Register your models here.
admin.site.register(GatePass)
admin.site.register(checkin)
admin.site.register(event)
