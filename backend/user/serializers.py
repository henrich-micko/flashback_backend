from rest_framework.serializers import ModelSerializer, SerializerMethodField
from django.conf import settings

from user.models import User
from friendship.status import get_friendship_status


class CreateUserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
        ]


class UserSerializer(ModelSerializer):
    quick_detail = SerializerMethodField()
    profile_url = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "quick_detail",
            "profile_url"
        ]

    def get_quick_detail(self, obj: User) -> str:
        return "He is cool"

    def get_profile_url(self, obj: User) -> str:
        return "https://www.alexgrey.com/img/containers/art_images/Godself-2012-Alex-Grey-watermarked.jpeg/121e98270df193e56eeaebcff787023f.jpeg"


class UserPOVSerializer(UserSerializer):
    friendship_status = SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = [
            *UserSerializer.Meta.fields,
            "friendship_status"
        ]

    def __init__(self, *args, **kwargs):
        self.user_pov = kwargs.pop("user_pov")
        super().__init__(*args, **kwargs)

    def get_friendship_status(self, obj):
        return get_friendship_status(
            user_from=self.user_pov,
            user_to=obj
        ).value


class MiniUserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "profile"
        ]

    @staticmethod
    def anonymous():
        return settings.ANONYMOUS_USER
