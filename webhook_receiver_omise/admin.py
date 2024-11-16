from django.contrib import admin
from .models import OmiseOrder, OmiseOrderItem

admin.site.register(OmiseOrder)
admin.site.register(OmiseOrderItem)