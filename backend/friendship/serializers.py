from rest_framework import serializers

from friendship.models import FriendRequest, Friendship
from user.serializers import UserSerializer, BasicUserSerializer


class FriendRequestSerializer(serializers.ModelSerializer):
    to_user = BasicUserSerializer()
    from_user = BasicUserSerializer()

    class Meta:
        model = FriendRequest
        fields = [
            "id",
            "to_user",
            "from_user",
            "status",
            "date"
        ]


class FriendshipSerializer(serializers.ModelSerializer):
    with_user = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = [
            "pk",
            "with_user",
            "date",
        ]

    def get_with_user(self, obj):
        other = obj.get_other_user(self.context['request'].user)
        return None if not other else UserSerializer(instance=other).data
