import os
import django
from django.conf import settings

settings.configure(
  EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
  EMAIL_HOST=os.env.get('DJANGO_EMAIL_HOST'),
  EMAIL_PORT=os.env.get('DJANGO_EMAIL_PORT'),
  EMAIL_USE_TLS=True,
  EMAIL_HOST_USER=os.env.get('DJANGO_EMAIL_HOST_USER'),
  EMAIL_HOST_PASSWORD=os.env.get('DJANGO_EMAIL_HOST_PASSWORD'))

django.setup()
