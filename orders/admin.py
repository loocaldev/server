from django.contrib import admin
from .models import Order, OrderItem, Discount, OrderStatusChangeLog

class OrderAdmin(admin.ModelAdmin):
    list_display = ('custom_order_id', 'payment_status', 'shipping_status', 'general_status', 'updated_at')
    list_filter = ('payment_status', 'shipping_status', 'general_status')
    search_fields = ('custom_order_id', 'email', 'phone')
    readonly_fields = ('general_status',)  # El estado general se calcula automáticamente
    actions = ['mark_as_paid', 'mark_as_shipped']

    def mark_as_paid(self, request, queryset):
        """
        Acción personalizada para marcar las órdenes seleccionadas como pagadas.
        """
        for order in queryset:
            old_status = order.payment_status
            order.payment_status = 'paid'
            order.update_general_status()
            OrderStatusChangeLog.objects.create(
                order=order,
                previous_status=old_status,
                new_status='paid',
                field_changed='payment_status',
            )
        self.message_user(request, "Las órdenes seleccionadas fueron marcadas como pagadas.")
    mark_as_paid.short_description = "Marcar como pagadas"

    def mark_as_shipped(self, request, queryset):
        """
        Acción personalizada para marcar las órdenes seleccionadas como despachadas.
        """
        for order in queryset:
            old_status = order.shipping_status
            order.shipping_status = 'in_transit'
            order.update_general_status()
            OrderStatusChangeLog.objects.create(
                order=order,
                previous_status=old_status,
                new_status='in_transit',
                field_changed='shipping_status',
            )
        self.message_user(request, "Las órdenes seleccionadas fueron marcadas como en tránsito.")
    mark_as_shipped.short_description = "Marcar como en tránsito"
    
    def save_model(self, request, obj, form, change):
        if change:  # Si es una actualización
            original_obj = Order.objects.get(pk=obj.pk)
            if original_obj.payment_status != obj.payment_status:
                OrderStatusChangeLog.objects.create(
                    order=obj,
                    previous_status=original_obj.payment_status,
                    new_status=obj.payment_status,
                    field_changed='payment_status'
                )
            if original_obj.shipping_status != obj.shipping_status:
                OrderStatusChangeLog.objects.create(
                    order=obj,
                    previous_status=original_obj.shipping_status,
                    new_status=obj.shipping_status,
                    field_changed='shipping_status'
                )
        super().save_model(request, obj, form, change)


class OrderStatusChangeLogAdmin(admin.ModelAdmin):
    list_display = ('order', 'field_changed', 'previous_status', 'new_status', 'timestamp')
    list_filter = ('field_changed', 'new_status')
    search_fields = ('order__custom_order_id', 'previous_status', 'new_status')


class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'unit_price', 'subtotal')
    search_fields = ('order__custom_order_id', 'product__name')

class DiscountAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'status', 'times_used', 'start_date', 'end_date')
    list_filter = ('status', 'discount_type')

# Register your models here.
admin.site.register(Order)
admin.site.register(OrderItem)
admin.site.register(Discount, DiscountAdmin)
admin.site.register(OrderStatusChangeLog, OrderStatusChangeLogAdmin)