import logging
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger("apps.exceptions")


def custom_exception_handler(exc, context):
    """Return consistent JSON error payloads across all API endpoints."""
    response = exception_handler(exc, context)

    if response is None:
        logger.exception("Unhandled exception in API view", exc_info=exc)
        return Response(
            {
                "error": {
                    "code": "internal_server_error",
                    "message": "An unexpected server error occurred.",
                    "details": None,
                }
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    error_code = getattr(exc, "default_code", "api_error")
    if isinstance(exc, ValidationError):
        message = "Validation failed."
        details = response.data
    elif isinstance(response.data, dict) and "detail" in response.data:
        message = str(response.data["detail"])
        details = None
    else:
        message = "Request could not be processed."
        details = response.data

    response.data = {
        "error": {
            "code": str(error_code),
            "message": message,
            "details": details,
        }
    }
    return response
