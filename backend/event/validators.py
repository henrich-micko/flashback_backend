from django.utils import timezone
from rest_framework.serializers import ValidationError
from datetime import datetime


def validate_event_datetimes(start_at: datetime, end_at: datetime) -> None:
    if not timezone.now() < start_at < end_at:
        raise ValidationError({"timing": "Invalid date times"})
