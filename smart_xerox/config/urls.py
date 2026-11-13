from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from orders import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("order/<uuid:order_id>/", views.track_order, name="track_order"),
    path("order/<uuid:order_id>/pay/", views.pay_order, name="pay_order"),
    path("payment/verify/", views.verify_payment, name="verify_payment"),
    path("operator/", views.operator_dashboard, name="operator_dashboard"),
    path("operator/order/<uuid:order_id>/", views.operator_order, name="operator_order"),
    path("receipt/<uuid:order_id>/", views.receipt, name="receipt"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
