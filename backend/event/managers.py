from django.db import models
from event.status import EventStatus


class EventQuerySet(models.QuerySet):
    def filter_by_status(self, status: EventStatus) -> models.QuerySet:
        print([
            instance.id for instance in self.all() if instance.status == status
        ])

        return self.filter(id__in=[
            instance.id for instance in self.all() if instance.status.value == status
        ])


class FlashbackQuerySet(models.QuerySet):
    def first_unseen(self):
        return self.filter(seen=False).order_by("created_at").first()