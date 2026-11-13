import uuid
from django.db import models

class PrintOrder(models.Model):
    PRINT_TYPE_CHOICES = [("bw", "Black & White"), ("color", "Colour")]
    SIDES_CHOICES = [("single", "Single-sided"), ("double", "Double-sided")]
    STATUS_CHOICES = [
        ("pending_payment", "Pending payment"),
        ("paid", "Paid"),
        ("printing", "Printing"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    order_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    document = models.FileField(upload_to="print_documents/")
    original_filename = models.CharField(max_length=255)
    page_count = models.PositiveIntegerField()
    copies = models.PositiveIntegerField()
    print_type = models.CharField(max_length=10, choices=PRINT_TYPE_CHOICES)
    sides = models.CharField(max_length=10, choices=SIDES_CHOICES)
    total_amount = models.DecimalField(max_digits=8, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending_payment")
    payment_id = models.CharField(max_length=100, blank=True)
    qr_code = models.ImageField(upload_to="qr_codes/", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.order_id} - Rs.{self.total_amount}"
