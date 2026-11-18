import json
import logging
from django.conf import settings
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import BaseModel, ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.exceptions import APIException

logger = logging.getLogger("apps.ai_assistant")


class GeminiUnavailableError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "AI assistant is temporarily unavailable. Core ticket operations continue normally."
    default_code = "ai_service_unavailable"


class GeminiQuotaExceededError(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "AI assistant quota reached. Please try again shortly."
    default_code = "ai_quota_exceeded"


def generate_structured_json(*, system_instruction: str, prompt: str, response_schema: type[BaseModel]) -> BaseModel:
    """Call Google Gemini API server-side and validate structured JSON output with Pydantic."""
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key:
        raise GeminiUnavailableError("GEMINI_API_KEY is not configured on the backend.")

    model_name = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
    timeout_ms = int(getattr(settings, "GEMINI_TIMEOUT_SECONDS", 20)) * 1000

    try:
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=timeout_ms),
        )
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=response_schema,
            ),
        )
        raw_text = (response.text or "").strip()
        if not raw_text:
            raise GeminiUnavailableError("AI service returned an empty response.")

        parsed_dict = json.loads(raw_text)
        return response_schema.model_validate(parsed_dict)

    except GeminiUnavailableError:
        raise
    except genai_errors.APIError as exc:
        logger.warning("Gemini API error (%s): %s", getattr(exc, "code", "unknown"), exc)
        if getattr(exc, "code", None) == 429:
            raise GeminiQuotaExceededError() from exc
        raise GeminiUnavailableError("Unable to reach Gemini AI service at this time.") from exc
    except (json.JSONDecodeError, PydanticValidationError) as exc:
        logger.warning("Gemini returned invalid structured payload: %s", exc)
        raise GeminiUnavailableError("AI service returned an invalid response structure.") from exc
    except Exception as exc:
        logger.exception("Unexpected error during Gemini API call: %s", exc)
        raise GeminiUnavailableError("AI assistant encountered an unexpected error.") from exc
