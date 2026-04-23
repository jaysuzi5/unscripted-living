import json
import logging
import time
import traceback
import uuid

logger = logging.getLogger('unscripted')

SKIP_PATHS = ('/static/', '/media/', '/health', '/favicon.ico')


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(p) for p in SKIP_PATHS):
            return self.get_response(request)

        transaction_id = str(uuid.uuid4())
        request.transaction_id = transaction_id
        start_time = time.time()

        user_context = self._get_user_context(request)

        logger.info(json.dumps({
            'event': 'request',
            'transaction_id': transaction_id,
            'method': request.method,
            'path': request.path,
            'user': user_context,
        }))

        try:
            response = self.get_response(request)
            elapsed = round((time.time() - start_time) * 1000, 2)
            logger.info(json.dumps({
                'event': 'response',
                'transaction_id': transaction_id,
                'status_code': response.status_code,
                'elapsed_ms': elapsed,
                'user': user_context,
            }))
            return response
        except Exception as e:
            elapsed = round((time.time() - start_time) * 1000, 2)
            logger.error(json.dumps({
                'event': 'exception',
                'transaction_id': transaction_id,
                'error': str(e),
                'elapsed_ms': elapsed,
                'stack_trace': traceback.format_exc(),
                'user': user_context,
            }))
            raise

    def _get_user_context(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            return {
                'user_id': user.id,
                'username': user.get_username(),
                'is_authenticated': True,
            }
        return {'user_id': None, 'username': None, 'is_authenticated': False}
