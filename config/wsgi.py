import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    from config.otel_config import init_otel_logging
    init_otel_logging()
except Exception:
    pass

application = get_wsgi_application()
