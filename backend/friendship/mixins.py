from rest_framework.permissions import IsAuthenticated

from friendship.models import FriendRequest, Friendship
from friendship.serializers import FriendRequestSerializer, FriendshipSerializer


class FriendRequestMixin:
    permissions_classes = [IsAuthenticated]
    serializer_class = FriendRequestSerializer

    def get_queryset(self):
        return FriendRequest.objects.filter(
            to_user = self.request.user
        )


class FriendshipMixin:
    permissions_classes = [IsAuthenticated]
    lookup_field = "pk"
    serializer_class = FriendshipSerializer

    def get_queryset(self):
        return self.request.user.friendship_set.all()