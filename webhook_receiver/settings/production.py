from yaml import load, SafeLoader
from yaml.scanner import ScannerError

from django.core.exceptions import ImproperlyConfigured
from django.conf import settings

from . import *  # noqa: F403

settings.configure()
# Email configuration
settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'  # Make SMTP explicit
settings.EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST', '')
settings.EMAIL_PORT = int(os.environ.get('DJANGO_EMAIL_PORT', 587))
settings.EMAIL_USE_TLS = os.environ.get('DJANGO_EMAIL_USE_TLS', 'True').lower() == 'true'
settings.EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_HOST_USER', '')
settings.EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD', '')
settings.DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER)

# We inherit all settings from base.py, including the anything set in
# the environment.  However, if the environment contains the variable
# WEBHOOK_RECEIVER_CFG, we open that file and parse it as YAML, and
# anything we find there overrides any values previously set.  Thus,
# if we have conflicting settings in the environment and the config
# file, the config file prevails.
CONFIG_FILE = env.str('WEBHOOK_RECEIVER_CFG', None)  # noqa: F405
if CONFIG_FILE:
    try:
        with open(CONFIG_FILE) as f:
            config_from_yaml = load(f, Loader=SafeLoader)
            vars().update(config_from_yaml)
    except OSError as e:
        raise ImproperlyConfigured(e)
    except (ValueError, TypeError, ScannerError) as e:
        raise ImproperlyConfigured(
            'Unable to update configuration '
            'with contents of %s: %s' % (CONFIG_FILE, e)
        )

# The "make migrate" ("manage.py migrate") functionality needs to
# honour the DB_MIGRATION_ environment variables.
DB_OVERRIDES = dict(
    PASSWORD=env.str('DB_MIGRATION_PASS', default=None),  # noqa: F405
    ENGINE=env.str('DB_MIGRATION_ENGINE', default=None),  # noqa: F405
    USER=env.str('DB_MIGRATION_USER', default=None),  # noqa: F405
    NAME=env.str('DB_MIGRATION_NAME', default=None),  # noqa: F405
    HOST=env.str('DB_MIGRATION_HOST', default=None),  # noqa: F405
    PORT=env.str('DB_MIGRATION_PORT', default=None),  # noqa: F405
    OPTIONS=env.json('DB_MIGRATION_OPTIONS', default=None),  # noqa: F405
)
for override, value in DB_OVERRIDES.items():
    if value:
        DATABASES['default'][override] = value  # noqa: F405

# The one thing we don't allow to be set in production, neither from
# the environment nor from a config file, is DEBUG == True.
if DEBUG:  # noqa: F405
    msg = "Refusing to start with DEBUG enabled in production."
    raise ImproperlyConfigured(msg)
