from django.contrib import admin
from .models import *

admin.site.register(Session)
admin.site.register(ScriptLog)
admin.site.register(TemperatureLog)
