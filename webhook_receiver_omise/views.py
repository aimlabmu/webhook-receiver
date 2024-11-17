import logging
import requests

from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

from webhook_receiver.utils import (
    receive_json_webhook,
    hmac_is_valid,
    fail_and_save,
    finish_and_save,
)
from .models import OmiseOrder as Order
from .utils import record_order
from .tasks import process

logger = logging.getLogger(__name__)

# Omise API endpoint for event verification
OMISE_EVENT_URL = "https://api.omise.co/events/{event_id}"

@csrf_exempt
@require_POST
def payment_confirm(request):
    """
    Handle incoming Omise webhook events, verify their authenticity
    by fetching the event via event_id from Omise API, and process relevant events.
    """
    # Load Omise configuration
    conf = settings.WEBHOOK_RECEIVER_SETTINGS['omise']

    try:
        data = receive_json_webhook(request)
        # Need to access the JSON data from the content field
        event_id = data.content.get('id')
    except Exception as e:
        logger.error(f"Failed to parse webhook payload: {e}")
        return HttpResponseBadRequest("Invalid Payload")

    if not event_id:
        logger.error("Webhook payload missing event ID.")
        fail_and_save(data)
        return HttpResponseBadRequest("Missing Event ID")

    logger.info(f"Received webhook for Event ID: {event_id}")

    # Verify the event by fetching it from Omise API
    try:
        response = requests.get(
            OMISE_EVENT_URL.format(event_id=event_id),
            auth=(conf['secret'], '')
        )
        response.raise_for_status()
        verified_event = response.json()
        logger.info(f"Successfully fetched and verified Event ID: {event_id}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to verify event {event_id} with Omise API: {e}")
        return HttpResponse(status=500)
    except ValueError:
        logger.error("Failed to decode JSON response from Omise API.")
        return HttpResponse(status=500)
    logger.info(f"Verified event: {verified_event}")
    # Ensure the fetched event matches the received event
    if verified_event.get('id') != event_id:
        logger.error(f"Event ID mismatch: received {event_id}, verified {verified_event.get('id')}")
        return HttpResponseBadRequest("Event ID Mismatch")
    
    # Handle only specific event types
    event_type = verified_event.get('type')
    logger.info(f"Processing Omise event type: {event_type}")

    SUPPORTED_EVENTS = [
        'charge.complete',
        'charge.failed',
        # Add other relevant event types as needed
    ]

    if event_type not in SUPPORTED_EVENTS:
        logger.info(f"Ignoring unsupported event type: {event_type}")
        return HttpResponse(status=200)  # Acknowledge receipt

    # Save and mark as processed
    finish_and_save(data)

    # Record the order in the database
    order, created = record_order(verified_event)

    # Determine the processing action based on event type
    if event_type == 'charge.complete':
        if order.status == Order.NEW:
            logger.info(f"Scheduling order {order.id} for processing.")
            process.delay(verified_event['data']['object'])
        else:
            logger.info(f"Order {order.id} already processed; no action taken.")
    elif event_type == 'charge.failed':
        logger.warning(f"Charge {order.id} has failed.")
        order.fail()
        order.save()
        # Optionally, notify the user about the failed payment
        # send_failure_email(order.email)
    else:
        logger.info(f"No handler implemented for event type: {event_type}")

    return HttpResponse(status=200)