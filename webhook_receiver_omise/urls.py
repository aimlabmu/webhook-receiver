from django.urls import path
from . import views

urlpatterns = [
    path('payment/confirm/', views.payment_confirm, name='omise_payment_confirm'),
]