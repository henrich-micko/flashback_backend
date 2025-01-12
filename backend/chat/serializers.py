from rest_framework import serializers
from chat.models import Message
from user.serializers import MiniUserSerializer


class MessageParentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Message
        fields = [
            "pk",
            "content"
        ]


class MessageSerializer(serializers.ModelSerializer):
    user = MiniUserSerializer(read_only=True)
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
