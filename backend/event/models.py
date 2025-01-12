import uuid, random
from django.db import models
from django.utils import timezone
from enum import Enum

from event.managers import EventQuerySet, FlashbackQuerySet
from user.models import User


EVENT_PREVIEW_COUNT_MAX = 3


""" Enums and choices """

class EventStatus(Enum):
    OPENED = 0
    ACTIVATED = 1
    CLOSED = 2

class EventViewersMode(models.IntegerChoices):
    ONLY_MEMBERS = 0, "only_members"
    ALL_FRIENDS = 1, "all_friends"
    MUTUAL_FRIENDS = 2, "mutual_friends"

class FlashbackVisibilityMode(models.IntegerChoices):
    PUBLIC = 0, "public"
    PRIVATE = 1, "private"


class Event(models.Model):
    objects = EventQuerySet.as_manager()

    title = models.CharField(max_length=15)
    emoji = models.CharField(max_length=35)
    start_at = models.DateTimeField()
    end_at = models.DateTimeField()

    # settings for event
    viewers_mode = models.IntegerField(default=EventViewersMode.ONLY_MEMBERS, choices=EventViewersMode.choices)
    mutual_friends_limit = models.DecimalField(max_digits=5, decimal_places=2, default=None, null=True)

    def __str__(self) -> str:
        return f"{self.title} [{self.pk}]"

    @property
    def status(self) -> EventStatus:
        current_time = timezone.now()
        if current_time < self.start_at: return EventStatus.OPENED
        if current_time > self.end_at: return EventStatus.CLOSED
        return EventStatus.ACTIVATED

    @property
    def viewers_generated(self) -> bool:
        return EventViewer.objects.filter(event=self).exists()

    def is_member(self, user: User) -> bool:
        try: EventMember.objects.get(event=self, user=user)
        except EventMember.DoesNotExist: return False
        return True

    def close(self):
        self.end_at = timezone.now()
        self.save()
        self.generate_viewers()

    def on_close(self):
        self.generate_viewers()
        self.generate_preview()

    @property
    def flashbacks(self):
        return Flashback.objects.filter(
            event_member_id__in=(ev.id for ev in EventMember.objects.filter(event=self))
        )

    def get_friends_members(self, user: User) -> models.QuerySet["EventMember"]:
        return self.eventmember_set.filter(
            user__in=[u.get_friend(user).pk for u in user.friendship_set.all()]
        )

    def save(self, *args, **kwargs):
        if self.viewers_mode == EventViewersMode.MUTUAL_FRIENDS.value:
            if self.mutual_friends_limit is None:
                self.mutual_friends_limit = 0.3
        super().save(*args, **kwargs)

    def generate_preview(self):
        flashbacks = self.flashbacks.all()
        if self.viewers_mode != EventViewersMode.ONLY_MEMBERS:
            flashbacks = flashbacks.filter(visibility=FlashbackVisibilityMode.PUBLIC)

        # check the old ones
        for i, ep in enumerate(self.eventpreview_set.order_by("order")):
            if i + 1 >= EVENT_PREVIEW_COUNT_MAX or ep.flashback not in flashbacks:
                ep.delete()
            flashbacks = flashbacks.exclude(pk=ep.flashback.pk)
            ep.order = i + 1
            ep.save()

        # create the new ones
        ep_count = self.eventpreview_set.count()
        for i in range(EVENT_PREVIEW_COUNT_MAX - ep_count):
            if flashbacks.count() == 0:
                break
            random_flashback = random.choice(flashbacks)
            flashbacks = flashbacks.exclude(pk=random_flashback.pk)
            EventPreview.objects.create(event=self, flashback=random_flashback, order=i + 1 + ep_count)

    def generate_viewers(self):
        self._flush_viewers()
        self._generate_all_members_viewers()  # members should be always viewers

        if (self.viewers_mode == EventViewersMode.ALL_FRIENDS.value or
           (self.viewers_mode == EventViewersMode.MUTUAL_FRIENDS.value and self.mutual_friends_limit >= 1)):
            self._generate_all_friends_viewers()  # mode is ALL_FRIENDS or MUTUAL_FRIENDS with mfl over 1

        elif self.viewers_mode == EventViewersMode.MUTUAL_FRIENDS.value:
            self._generate_mutual_members_viewers()  # MUTUAL_FRIENDS

    def _generate_all_members_viewers(self):
        for em in self.eventmember_set.all():
            EventViewer.objects.get_or_create(
                user=em.user, event=self, is_member=False
            )

    def _generate_all_friends_viewers(self):
        for em in self.eventmember_set.all():
            for f in em.user.friends:
                EventViewer.objects.get_or_create(
                    user=f, event=self, is_member=False
                )

    def _generate_mutual_members_viewers(self):
        members_count = len(self.eventmember_set)
        mutual_friends_limit_c = round(members_count * ((self.mutual_friends_limit * 10) / 100))
        user_friends_count = {}
        for em in self.eventmember_set.all():
            for f in em.user.friends:
                mfc = user_friends_count.get(f.pk, 0)
                if mfc is True: continue
                user_friends_count[f.pk] = mfc + 1
                if mfc >= mutual_friends_limit_c:
                    EventViewer.objects.get_or_create(user=f, event=self, is_member=False)
                    user_friends_count[f.pk] = True

    def _flush_viewers(self):
        EventViewer.objects.filter(event=self).delete()


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
        return f"{self.user} -{self.role}-> {self.event}"


def upload_flashback_to(instance, filename):
    extension = filename.split(".")[-1]
    return f"flashback/{uuid.uuid4()}.{extension}"


class Flashback(models.Model):
    objects = FlashbackQuerySet.as_manager()

    event_member = models.ForeignKey(EventMember, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    media = models.ImageField(upload_to=upload_flashback_to, blank=True, null=True)
    visibility = models.IntegerField(default=FlashbackVisibilityMode.PUBLIC, choices=FlashbackVisibilityMode.choices)

    def __str__(self) -> str:
        return f"{self.event_member} flashback [{self.id}]"

    @property
    def user(self) -> User:
        return self.event_member.user

    @property
    def event(self) -> Event:
        return self.event_member.event


class EventPreview(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    flashback = models.ForeignKey(Flashback, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=1)  # 1, 2...EVENT_PREVIEW_COUNT

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["event", "flashback"],
                name="unique_event_preview_event_flashback"
            ),
            models.UniqueConstraint(
                fields=["event", "order"],
                name="unique_event_preview_event_order"
            ),
        ]

    def __str__(self) -> str:
        return f"Preview for event ({self.event}) with flashback ({self.flashback}) as {self.order}"


class EventViewer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    is_member = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "event")

    def __str__(self):
        return f"{self.user} -> [{self.event}]"

    def generate_flashback_viewer(self):
        for user in self.event.eventmember_set.all():
            for flashback in user.flashback_set.all():
                fv, created = FlashbackViewer.objects.get_or_create(event_viewer=self, flashback=flashback)
                if not created and fv.is_seen:
                    fv.is_seen = False
                    fv.save()


class FlashbackViewer(models.Model):
    event_viewer = models.ForeignKey(EventViewer, on_delete=models.CASCADE)
    flashback = models.ForeignKey(Flashback, on_delete=models.CASCADE)
    is_seen = models.BooleanField(default=False)

    class Meta:
        unique_together = ("event_viewer", "flashback")

    def __str__(self):
        return f"[{self.event_viewer}] -> {self.flashback}"

