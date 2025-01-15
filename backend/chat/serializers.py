from rest_framework import serializers
from chat.models import Message
from user.serializers import MiniUserSerializer
from user.serializers_fields import AnonymousOrMiniSerializerField


class MessageParentSerializer(serializers.ModelSerializer):
    user = AnonymousOrMiniSerializerField()

    class Meta:
        model = Message
        fields = [
            "pk",
            "content",
            "user",
        ]


class MessageSerializer(serializers.ModelSerializer):
    user = AnonymousOrMiniSerializerField()
    parent = MessageParentSerializer(read_only=True)

    class Meta:
        model = Message
        fields = read_only_fields = [
            "pk",
            "user",
            "content",
            "timestamp",
            "parent"
        ]


class MessageWritableSerializer(MessageSerializer):
    parent = serializers.PrimaryKeyRelatedField(
        queryset=Message.objects.all(),
        required=False,
        allow_null=True
    )

    content = serializers.CharField()
