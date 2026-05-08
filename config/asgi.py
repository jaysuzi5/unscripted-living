import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

try:
    from config.otel_config import setup_otel
    setup_otel()
except Exception:
    pass

application = get_asgi_application()
