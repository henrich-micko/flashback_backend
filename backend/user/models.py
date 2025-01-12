from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone

from user.manager import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    objects = UserManager()

    username = models.CharField(max_length=10, unique=True)
    email = models.EmailField(unique=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    profile = models.CharField(max_length=255)
    about = models.CharField(max_length=255, default=None, null=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return f"{self.username} [{self.pk}]"

    @property
    def friendship_set(self):
        from friendship.models import Friendship
        return Friendship.objects.filter_by_user(self)

    def is_friend_with(self, user):
        from friendship.models import Friendship
        print(user, self)
        return Friendship.objects.get(user_a=self, user_b=user) is not None

    @property
    def events(self) -> models.QuerySet:
        from event.models import Event, EventMember

        return Event.objects.filter(
            pk__in=[em.event.pk for em in EventMember.objects.filter(user=self)]
        )

    @property
    def friends(self) -> models.QuerySet:
        from friendship.models import Friendship

        return User.objects.filter(
            id__in=[
                fs.get_friend(self).id for fs in self.friendship_set
            ]
        )
