import os
import django
from django.conf import settings

settings.configure(
  EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',
  EMAIL_HOST=os.environ.get('DJANGO_EMAIL_HOST', ''),
  EMAIL_PORT=int(os.environ.get('DJANGO_EMAIL_PORT', 587)),
  EMAIL_USE_TLS=True,
  EMAIL_HOST_USER=os.environ.get('DJANGO_EMAIL_HOST_USER', ''),
  EMAIL_HOST_PASSWORDos.environ.get('DJANGO_EMAIL_HOST_PASSWORD', ''),
  DEFAULT_FROM_EMAIL=os.environ.get('DJANGO_EMAIL_HOST_USER', '')
)

django.setup()
