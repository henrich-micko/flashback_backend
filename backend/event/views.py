from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from event.serializers import EventSerializer, EventMemberSerializer, FlashbackSerializer
from event.models import EventMember, EventMemberRole, Flashback
from user.serializers import BasicUserSerializer
from utils.shortcuts import get_object_or_exception


class EventViewSet(viewsets.ModelViewSet):
    lookup_field = "id"
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.action == "flashback":
            return FlashbackSerializer
        return EventSerializer

    def perform_create(self, serializer) -> None:
        instance = serializer.save()
        EventMember.objects.create(user=self.request.user, event=instance, role=EventMemberRole.HOST)

    def get_queryset(self) -> QuerySet:
        return self.request.user.events.order_by("-start_at")

    @action(detail=True, methods=["post", "get"])
    def flashback(self, request, id):
        event = get_object_or_404(self.get_queryset(), id=id)
        event_member = EventMember.objects.get(user=request.user, event=event)

        if request.method == "GET":
            serializer = FlashbackSerializer(event.flashbacks, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if request.method == "POST":
            serializer = FlashbackSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            serializer.save(event_member=event_member)
            return Response(status=status.HTTP_201_CREATED, data=serializer.data)

    @action(detail=True, methods=["post"])
    def close(self, request, id):
        event = get_object_or_404(self.get_queryset(), id=id)
        event.close()
        return Response(self.get_serializer(instance=event).data, status=status.HTTP_200_OK)


class MemberViewSet(mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):

    lookup_field = "user__pk"
    serializer_class = EventMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        event_id = self.kwargs.get("event_id", None)
        event = get_object_or_exception(self.request.user.events, PermissionDenied(), pk=event_id)
        return EventMember.objects.filter(event=event)

    def destroy(self, request, *args, **kwargs):
        response = super().destroy(request, *args, **kwargs)
        response.data = self.serializer_class(instance=self.get_queryset(), many=True).data
        return response

    @action(detail=True, methods=["post"])
    def add(self, request, *args, **kwargs) -> Response:
        user_id = kwargs.get("user__pk")
        event_id = self.kwargs.get("event_id")
        event_member, _ = EventMember.objects.get_or_create(user_id=user_id, event_id=event_id)
        response_data = self.serializer_class(instance=self.get_queryset(), many=True).data
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["get"])
    def possible(self, request, *args, **kwargs):
        event_id = self.kwargs.get("event_id", None)
        event = get_object_or_exception(self.request.user.events, PermissionDenied(), pk=event_id)

        data = [
            {"event": int(event_id), "user": BasicUserSerializer(instance=user).data, "is_member": event.is_member(user)}
            for user in self.request.user.friends if user != request.user
        ]

        return Response(data, status=status.HTTP_200_OK)