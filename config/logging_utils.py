import json
import logging
import socket
from datetime import datetime, timezone

logger = logging.getLogger('unscripted')


def log_event(request=None, event='', level='INFO', service='unscripted-living', **fields):
    payload = {
        'event': event,
        'service': service,
        'hostname': socket.gethostname(),
        'timestamp': datetime.now(timezone.utc).isoformat(),
        **fields,
    }
    if request is not None:
        payload['transaction_id'] = getattr(request, 'transaction_id', None)
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            payload['user_id'] = user.id
            payload['username'] = user.get_username()

    getattr(logger, level.lower())(json.dumps(payload))
