from rest_framework import serializers
from event import models, validators
from user.serializers import UserSerializer, MiniUserSerializer
from utils.time import humanize_event_time


class EventSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    quick_detail = serializers.SerializerMethodField()

    class Meta:
        model = models.Event
        fields = [
            "pk",
            "title",
            "start_at",
            "end_at",
            "quick_detail",
            "status",
            "emoji",
            "viewers_mode",
            "mutual_friends_limit",
        ]
        ordering = ["start_at", "pk"]

    def validate(self, attrs):
        start_at, end_at = attrs.get("start_at"), attrs.get("end_at")
        if start_at and end_at:
            validators.validate_event_datetimes(start_at, end_at)
        return attrs

    def get_quick_detail(self, obj: models.Event) -> str:
        return humanize_event_time(obj.start_at)

    def get_status(self, obj: models.Event) -> int:
        return obj.status.value


"""Viewer Serializers"""


class EventPreviewFlashbackSerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Flashback
        fields = [
            "pk",
            "media"
        ]


class EventPreviewSerializer(serializers.ModelSerializer):
    flashback = EventPreviewFlashbackSerializer()

    class Meta:
        model = models.EventPreview
        fields = [
            "pk",
            "flashback",
            "order"
        ]


class EventViewerSerializer(serializers.ModelSerializer):
    event = EventSerializer(read_only=True)
    flashbacks_count = serializers.SerializerMethodField()
    preview = serializers.SerializerMethodField()

    class Meta:
        model = models.EventViewer
        fields = [
            "pk",
            "event",
            "flashbacks_count",
            "preview",
            "is_member"
        ]

    def get_flashbacks_count(self, obj):
        return obj.event.flashbacks.count()

    def get_preview(self, obj):
        return EventPreviewSerializer(
            instance=obj.event.eventpreview_set.all().order_by("order"),
            many=True
        ).data


class EventMemberSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer()

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
        return UserSerializer(instance=obj.event_member.user).data


class FlashbackViewerSerializer(serializers.ModelSerializer):
    media = serializers.ImageField(required=True)

    class Meta:
        model = models.FlashbackViewer
        fields = [
            "id",
            "flashback",
            "is_seen",
        ]
