from django.conf import settings

TRANSACTIONAL_MIDDLEWARE = getattr(settings, 'TRANSACTIONAL_MIDDLEWARE', [])



