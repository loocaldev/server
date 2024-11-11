from django.contrib import admin
from .models import Order, OrderItem, Discount

class DiscountAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'status', 'times_used', 'start_date', 'end_date')
    list_filter = ('status', 'discount_type')

# Register your models here.
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Discount, DiscountAdmin)