from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action, api_view
from rest_framework.authtoken.models import Token
from django.shortcuts import get_object_or_404

from user.serializers import UserPOVSerializer, CreateUserSerializer, UserSerializer
from user.models import User
from user.utils import validate_google_token, get_username_from_email
from friendship.models import Friendship, FriendRequest
from friendship.serializers import FriendRequestSerializer


@api_view(["POST"])
def google_auth(request):
    token = request.data.get("auth_token", None)
    if token is None:
        return Response(data={"auth_token": "Not provided."}, status=status.HTTP_400_BAD_REQUEST)

    is_token_valid, user_data = validate_google_token(token)
    if not is_token_valid:
        return Response(data={"auth_token": "Invalid token."}, status=status.HTTP_400_BAD_REQUEST)

    user, created = User.objects.get_or_create(
        email=user_data["email"],
        defaults={"username": get_username_from_email(user_data["email"])}
    )

    if created:
        user.is_active = True
        user.save()

    token, created = Token.objects.get_or_create(user=user)
    return Response({"token": token.key}, status=status.HTTP_201_CREATED)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == "create": return CreateUserSerializer
        if self.action in ("me", "friendship", "search"): return UserSerializer
        if self.action == "requests": return FriendRequestSerializer
        return UserPOVSerializer

    def get_serializer(self, *args, **kwargs):
        if self.get_serializer_class().__name__ == "UserPOVSerializer":
            kwargs["user_pov"] = self.request.user
        return super().get_serializer(*args, **kwargs)

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        instance = serializer.save()
        instance.set_password(serializer.data["password"])
        instance.is_active = True
        instance.save()

    def create(self, request, *args, **kwargs):
        response = super().create(request, *args, **kwargs)
        response.data["token"] = Token.objects.get(user_id=response.data["id"]).key
        return response

    @action(detail=False, methods=["get", "put"])
    def me(self, request):
        if request.method == "GET":
            serializer = self.get_serializer(instance=request.user)
            return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def search(self, request):
        search_value = request.GET.get('value')
        if not search_value:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        users = User.objects.filter(username__icontains=search_value).exclude(id=request.user.id)
        serializer = self.get_serializer(instance=users, many=True)
        return Response(
            serializer.data, status=status.HTTP_200_OK
        )

    @action(detail=True, methods=["get", "post", "put", "delete"])
    def friend(self, request, pk):
        user_from: User = request.user
        user_to: User = self.get_object()

        if request.method == "GET":
            serializer = self.get_serializer(instance=request.user.friends, many=True)
            return Response(data=serializer.data, status=status.HTTP_200_OK)

        if user_from == user_to:
            return Response(data={"detail": "You cannot do friends operation on yourself."},
                            status=status.HTTP_400_BAD_REQUEST)

        if request.method == "POST":
            if user_from.is_friend_with(user_to):
                return Response(status=status.HTTP_200_OK)
            friend_request, created = FriendRequest.objects.get_or_create(from_user=user_from, to_user=user_to)
            response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
            return Response(status=response_status)

        if request.method == "PUT":
            if user_from.is_friend_with(user_to):
                return Response(status=status.HTTP_200_OK)

            friend_request = get_object_or_404(FriendRequest.objects.all(), from_user=user_to, to_user=user_from)
            friend_request.status = FriendRequest.StatusChoices.ACCEPTED
            friend_request.save()

            return Response(status=status.HTTP_200_OK)

        if request.method == "DELETE":
            friendship = Friendship.objects.get(user_a=user_from, user_b=user_to)
            if friendship is not None:
                friendship.delete()
                return Response(status=status.HTTP_204_NO_CONTENT)

            friend_request = get_object_or_404(FriendRequest.objects.all(), user_a=user_from, user_b=user_to)
            friend_request.status = FriendRequest.StatusChoices.REFUSED
            friend_request.save()

            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"])
    def my_friends(self, request):
        serializer = self.get_serializer(instance=request.user.friends, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def requests(self, request):
        instance = FriendRequest.objects.filter(to_user=self.request.user)
        serializer = self.get_serializer(instance=instance, many=True)
        return Response(data=serializer.data, status=status.HTTP_200_OK)
