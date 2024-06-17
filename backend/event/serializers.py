from rest_framework import serializers
from event import models, validators
from user.serializers import BasicUserSerializer


class EventSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    quick_detail = serializers.SerializerMethodField()

    class Meta:
        model = models.Event
        fields = "__all__"

    def validate(self, attrs):
        validators.validate_event_datetimes(attrs["start_at"], attrs["end_at"])
        return attrs

    def get_quick_detail(self, obj: models.Event) -> str:
        members = models.EventMember.objects.filter(event=obj)[0:2]
        return f"Members: " + ", ".join([m.user.username for m in members])

    def get_status(self, obj: models.Event) -> int:
        return obj.status.value


class EventMemberSerializer(serializers.ModelSerializer):
    user = BasicUserSerializer()

    class Meta:
        model = models.EventMember
        fields = "__all__"


class FlashbackSerializer(serializers.ModelSerializer):
    media = serializers.ImageField(required=True)
    created_by = serializers.SerializerMethodField()

    class Meta:
        model = models.Flashback
        fields = [
            "id",
            "media",
            "created_by",
            "created_at"
        ]

    def get_created_by(self, obj: models.Flashback):
        return BasicUserSerializer(instance=obj.event_member.user).data
