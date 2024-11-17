from django.db import transaction
from django.conf import settings
from django.core.mail import send_mail
from webhook_receiver.utils import enroll_in_course, lookup_course_id, create_user_via_api, user_exists_via_api
from .models import OmiseOrder as Order, OmiseOrderItem as OrderItem, JSONWebhookData
import logging
import random
import string

logger = logging.getLogger(__name__)

def generate_random_password(length=12):
    """Generate a random password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

def send_welcome_email(email, password):
    """Send an email to the user with their password."""
    subject = 'Welcome to Our Platform'
    message = f"""
    Hello,

    Your account has been created successfully. You can now access your course using the following credentials:

    Email: {email}
    Password: {password}

    Please log in at https://aithaigen.pro/login and change your password after logging in.

    Best regards,
    AIThaiGen Team
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)

def record_omise_order(data):
    """Record or retrieve an Omise order based on the webhook data."""
    logger.info(f"Recording Omise order: {data}")
    # Extract charge data from the webhook payload
    charge = data.get('data', {})
    
    # Extract metadata from the charge
    metadata = charge.get('metadata', {})
    email = metadata.get('email')
    
    # Get basic charge info
    charge_id = charge.get('id')
    status = charge.get('status')
    
    # Get customer info from card data
    card = charge.get('card', {})
    customer_name = card.get('name', '').split(' ', 1)
    first_name = customer_name[0] if customer_name else ''
    last_name = customer_name[1] if len(customer_name) > 1 else ''

    # Create JSONWebhookData instance
    webhook_data = JSONWebhookData(
        content=data,
        headers={},
    )
    webhook_data.save()
    webhook_data.start_processing()
    webhook_data.save()

    return Order.objects.get_or_create(
        id=charge_id,  # Use charge ID as order ID
        defaults={
            'webhook': webhook_data,  # Store the entire webhook data
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'status': Order.NEW if status == 'successful' else Order.ERROR,
        }
    )

def record_order(data):
    """Record or retrieve an Omise order based on the webhook data."""
    return Order.objects.get_or_create(
        id=data.content['id'],
        defaults={
            'webhook': data,
            'email': data.content['customer_email'],
            'first_name': data.content.get('customer_first_name', ''),
            'last_name': data.content.get('customer_last_name', ''),
        }
    )

def process_order(order, data):
    """Process the Omise order and create enrollments."""
    if order.status == Order.PROCESSED:
        logger.warning(f'Order {order.id} has already been processed, ignoring')
        return
    elif order.status == Order.ERROR:
        logger.warning(f'Order {order.id} has previously failed to process, ignoring')
        return

    if order.status == Order.PROCESSING:
        logger.warning(f'Order {order.id} is already being processed, retrying')
    else:
        order.start_processing()
        with transaction.atomic():
            order.save()

    # Process each line item in the order
    for item in data['line_items']:
        process_line_item(order, item)
        logger.debug(f'Successfully processed line item {item} for order {order.id}')

    # Mark the order as processed
    order.finish_processing()
    with transaction.atomic():
        order.save()

    return order

def process_line_item(order, item):
    """Process individual line items for the Omise order."""
    metadata = item.get('metadata', {})
    email = metadata.get('email')
    course_id = metadata.get('courseId')

    if not email or not course_id:
        logger.error(f"Missing email or courseId in metadata for order {order.id}")
        return

    # Check if the user exists
    try:
        user_exists = user_exists_via_api(email)
    except Exception as e:
        logger.error(f"Error checking if user exists for email {email}: {e}")
        order.fail()
        order.save()
        return

    if not user_exists:
        # Generate a random password
        password = generate_random_password()

        # Create the user via Open edX API
        try:
            create_user_via_api(email, password)
            logger.info(f"Created new user with email {email}")
        except Exception as e:
            logger.error(f"Error creating user {email}: {e}")
            order.fail()
            order.save()
            return

        # Send welcome email with password
        try:
            send_welcome_email(email, password)
            logger.info(f"Sent welcome email to {email}")
        except Exception as e:
            logger.error(f"Error sending email to {email}: {e}")
            # Decide whether to continue or fail
            # Here, we'll continue to enroll the user
    else:
        logger.info(f"User with email {email} already exists")

    # Enroll the user in the course
    try:
        enroll_in_course(course_id, email)
        logger.info(f"Enrolled user {email} in course {course_id}")
    except Exception as e:
        logger.error(f"Error enrolling user {email} in course {course_id}: {e}")
        order.fail()
        order.save()
        return

    # Mark the order item as processed
    order_item, created = OrderItem.objects.get_or_create(
        order=order,
        sku=item.get('sku', ''),  # Optional: Retain if needed
        email=email
    )

    if order_item.status == OrderItem.PROCESSED:
        logger.warning(f'Order item {order_item.id} has already been processed, ignoring')
        return
    elif order_item.status == OrderItem.PROCESSING:
        logger.warning(f'Order item {order_item.id} is already being processed, retrying')
    else:
        order_item.start_processing()
        with transaction.atomic():
            order_item.save()

    # Mark the order item as processed
    order_item.finish_processing()
    with transaction.atomic():
        order_item.save()

    return order_item