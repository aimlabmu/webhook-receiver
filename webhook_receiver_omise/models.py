from django.db import models
from django_fsm import FSMIntegerField
from webhook_receiver.models import Order, OrderItem, JSONWebhookData
import logging

logger = logging.getLogger(__name__)

class STATE:
    NEW = 0
    PROCESSING = 1
    PROCESSED = 2
    ERROR = -1

    CHOICES = (
        (NEW, 'New'),
        (PROCESSING, 'Processing'),
        (PROCESSED, 'Processed'),
        (ERROR, 'Error'),
    )

class OmiseOrder(Order):
    webhook = models.ForeignKey(
        JSONWebhookData,
        on_delete=models.SET_NULL,
        null=True
    )

    class Meta:
        app_label = 'webhook_receiver_omise'

class OmiseOrderItem(OrderItem):
    order = models.ForeignKey(
        OmiseOrder,
        on_delete=models.PROTECT
    )

    course_id = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField()

    class Meta:
        app_label = 'webhook_receiver_omise'
        constraints = [
            models.UniqueConstraint(fields=['order', 'course_id', 'email'],
                                    name='unique_omise_order_courseid_email')
        ]