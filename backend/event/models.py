import uuid
from django.db import models
from django.utils import timezone
from enum import Enum

from user.models import User


class EventStatus(Enum):
    OPENED = 0
    ACTIVATED = 1
    CLOSED = 2


class Event(models.Model):
    title = models.CharField(max_length=15)
    emoji = models.CharField(max_length=35)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    def __str__(self) -> str:
        return f"{self.title} [{self.pk}]"

    @property
    def status(self) -> EventStatus:
        current_time = timezone.now()
        if current_time < self.start_at: return EventStatus.OPENED
        if current_time > self.end_at: return EventStatus.CLOSED
        return EventStatus.ACTIVATED

    def is_member(self, user: User) -> bool:
        try: EventMember.objects.get(event=self, user=user)
        except EventMember.DoesNotExist: return False
        return True

    def close(self):
        self.end_at = timezone.now()
        self.save()

    @property
    def flashbacks(self):
        return Flashback.objects.filter(
            event_member_id__in=(ev.id for ev in EventMember.objects.filter(event=self))
        )


class EventMemberRole(models.IntegerChoices):
    HOST = 0, "host"
    GUEST = 1, "guest"


class EventMember(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.IntegerField(default=EventMemberRole.GUEST, choices=EventMemberRole.choices)

    class Meta:
        unique_together = ("event", "user")

    def __str__(self) -> str:
        return f"{self.user} -{EventMemberRole.choices[0][1]}-> {self.event}"


def upload_flashback_to(instance, filename):
    extension = filename.split(".")[-1]
    return f"flashback/{uuid.uuid4()}.{extension}"


class Flashback(models.Model):
    event_member = models.ForeignKey(EventMember, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    media = models.ImageField(upload_to=upload_flashback_to, blank=True, null=True)

    def __str__(self) -> str:
        return f"{self.event_member} flashback [{self.id}]"

    @property
    def user(self) -> User:
        return self.event_member.user

    @property
    def event(self) -> Event:
        return self.event_member.event
