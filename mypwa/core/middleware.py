# middleware.py
from django.http import HttpResponseForbidden
from django.contrib.auth import logout
import time

class SecurityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Force HTTPS in production
        if not request.is_secure() and not settings.DEBUG:
            return HttpResponseForbidden("HTTPS required")
        
        response = self.get_response(request)
        return response