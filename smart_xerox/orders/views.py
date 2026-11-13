import hashlib
import hmac
import io
import os
import qrcode
import razorpay

from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.files.base import ContentFile
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from .models import PrintOrder

MAX_UPLOAD_BYTES = 10 * 1024 * 1024

def calculate_amount(page_count, copies, print_type, sides):
    units = (page_count + 1) // 2 if sides == "double" else page_count
    rates = {
        ("bw", "single"): Decimal("2.00"),
        ("bw", "double"): Decimal("3.00"),
        ("color", "single"): Decimal("5.00"),
        ("color", "double"): Decimal("8.00"),
    }
    return units * copies * rates[(print_type, sides)]

def home(request):
    if request.method == "POST":
        uploaded = request.FILES.get("document")
        try:
            copies = int(request.POST.get("copies", "1"))
            print_type = request.POST.get("print_type", "bw")
            sides = request.POST.get("sides", "single")
            if not 1 <= copies <= 100:
                raise ValueError("Copies must be between 1 and 100.")
            if print_type not in ("bw", "color") or sides not in ("single", "double"):
                raise ValueError("Please choose valid printing options.")
            if not uploaded:
                raise ValueError("Please choose a PDF file.")
            if uploaded.size > MAX_UPLOAD_BYTES:
                raise ValueError("PDF must be 10 MB or smaller.")
            if not uploaded.name.lower().endswith(".pdf"):
                raise ValueError("Only PDF files are accepted.")
            reader = PdfReader(uploaded, strict=False)
            if reader.is_encrypted:
                raise ValueError("Password-protected PDFs are not supported.")
            page_count = len(reader.pages)
            if page_count < 1:
                raise ValueError("The PDF has no pages.")
            amount = calculate_amount(page_count, copies, print_type, sides)
            order = PrintOrder.objects.create(
                document=uploaded,
                original_filename=os.path.basename(uploaded.name)[:255],
                page_count=page_count,
                copies=copies,
                print_type=print_type,
                sides=sides,
                total_amount=amount,
            )
            return redirect("track_order", order_id=order.order_id)
        except (ValueError, TypeError) as exc:
            messages.error(request, str(exc))
        except Exception:
            messages.error(request, "We could not read this PDF. Please try another valid PDF.")
    return render(request, "orders/home.html")

def track_order(request, order_id):
    order = get_object_or_404(PrintOrder, order_id=order_id)
    return render(request, "orders/track.html", {"order": order, "demo_payment": settings.DEMO_PAYMENT})

def create_qr_for_order(order, request):
    track_url = request.build_absolute_uri(reverse("operator_order", args=[order.order_id]))
    image = qrcode.make(track_url)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    order.qr_code.save(f"{order.order_id}.png", ContentFile(buffer.getvalue()), save=False)

def pay_order(request, order_id):
    order = get_object_or_404(PrintOrder, order_id=order_id)
    if order.status != "pending_payment":
        return redirect("track_order", order_id=order.order_id)

    if settings.DEMO_PAYMENT:
        return render(request, "orders/demo_payment.html", {"order": order})

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        messages.error(request, "Razorpay keys are not configured. Set them in your .env file.")
        return redirect("track_order", order_id=order.order_id)

    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
    payment_order = client.order.create({
        "amount": int(order.total_amount * 100),
        "currency": "INR",
        "receipt": str(order.order_id),
    })
    request.session["razorpay_order_id"] = payment_order["id"]
    request.session["print_order_id"] = str(order.order_id)
    return render(request, "orders/razorpay_checkout.html", {
        "order": order,
        "razorpay_order_id": payment_order["id"],
        "razorpay_key": settings.RAZORPAY_KEY_ID,
    })

@require_POST
def verify_payment(request):
    order_id = request.POST.get("order_id")
    order = get_object_or_404(PrintOrder, order_id=order_id)
    if order.status != "pending_payment":
        return redirect("track_order", order_id=order.order_id)

    if settings.DEMO_PAYMENT:
        # Local demonstration only. This is not a real payment.
        order.status = "paid"
        order.payment_id = "DEMO-" + str(order.order_id)
        create_qr_for_order(order, request)
        order.save()
        return redirect("track_order", order_id=order.order_id)

    razorpay_order_id = request.POST.get("razorpay_order_id", "")
    razorpay_payment_id = request.POST.get("razorpay_payment_id", "")
    signature = request.POST.get("razorpay_signature", "")
    expected_order_id = request.session.get("razorpay_order_id")
    expected_print_order_id = request.session.get("print_order_id")

    if (not razorpay_order_id or not razorpay_payment_id or not signature
            or razorpay_order_id != expected_order_id
            or expected_print_order_id != str(order.order_id)):
        return HttpResponseForbidden("Invalid payment verification details.")

    message = f"{razorpay_order_id}|{razorpay_payment_id}".encode()
    expected_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(), message, hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        return HttpResponseForbidden("Payment signature verification failed.")

    order.status = "paid"
    order.payment_id = razorpay_payment_id
    create_qr_for_order(order, request)
    order.save()
    request.session.pop("razorpay_order_id", None)
    request.session.pop("print_order_id", None)
    return redirect("track_order", order_id=order.order_id)

@staff_member_required
def operator_dashboard(request):
    orders = PrintOrder.objects.exclude(status="cancelled").order_by("-created_at")
    return render(request, "orders/operator_dashboard.html", {"orders": orders})

@staff_member_required
def operator_order(request, order_id):
    order = get_object_or_404(PrintOrder, order_id=order_id)
    if request.method == "POST":
        new_status = request.POST.get("status")
        allowed = {"printing", "completed"}
        if order.status == "paid" and new_status == "printing":
            order.status = "printing"
            order.save()
            messages.success(request, "Order marked as printing.")
        elif order.status == "printing" and new_status == "completed":
            order.status = "completed"
            order.save()
            messages.success(request, "Order marked as completed.")
        else:
            messages.error(request, "That status change is not allowed.")
        return redirect("operator_order", order_id=order.order_id)
    return render(request, "orders/operator_order.html", {"order": order})

@staff_member_required
def receipt(request, order_id):
    order = get_object_or_404(PrintOrder, order_id=order_id)
    if order.status not in ("paid", "printing", "completed"):
        return HttpResponseForbidden("Receipt is available after payment verification.")
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    pdf.setTitle("Smart Xerox Receipt")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(55, 790, "SMART XEROX - PAYMENT RECEIPT")
    pdf.setFont("Helvetica", 11)
    lines = [
        f"Order ID: {order.order_id}",
        f"File: {order.original_filename}",
        f"Pages: {order.page_count}",
        f"Copies: {order.copies}",
        f"Print type: {order.get_print_type_display()}",
        f"Printing mode: {order.get_sides_display()}",
        f"Total: Rs. {order.total_amount}",
        f"Status: {order.get_status_display()}",
        f"Payment ID: {order.payment_id}",
        f"Created: {order.created_at:%d-%m-%Y %I:%M %p}",
    ]
    y = 750
    for line in lines:
        pdf.drawString(55, y, line)
        y -= 28
    pdf.drawString(55, y - 15, "Thank you for using Smart Xerox!")
    pdf.save()
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="receipt-{order.order_id}.pdf"'
    return response
