from django.contrib import admin
from .models import PrintOrder

@admin.register(PrintOrder)
class PrintOrderAdmin(admin.ModelAdmin):
    list_display = ("order_id", "original_filename", "page_count", "copies",
                    "print_type", "sides", "total_amount", "status", "created_at")
    list_filter = ("status", "print_type", "sides", "created_at")
    search_fields = ("order_id", "original_filename", "payment_id")
    readonly_fields = ("order_id", "created_at", "updated_at", "payment_id", "qr_code")
