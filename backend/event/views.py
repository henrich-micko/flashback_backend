from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from event.serializers import EventSerializer, EventMemberSerializer, FlashbackSerializer, FlashbackViewerSerializer, EventViewerSerializer
from event.models import EventMember, EventMemberRole, EventViewer, FlashbackViewer
from event.permissions import IsEventHost
from user.serializers import UserSerializer
from utils.shortcuts import get_object_or_exception
from utils.views import parse_boolean_value
from utils import constants as cnst


class EventViewSet(viewsets.ModelViewSet):
    lookup_field = "pk"
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.action == "to_view":
            return EventViewerSerializer
        return EventSerializer

    def get_permissions(self):
        output = [permissions.IsAuthenticated()]
        if self.action in ["put", "patch"]:
            output.append(IsEventHost())
        return output

    def perform_create(self, serializer) -> None:
        instance = serializer.save()
        EventMember.objects.create(user=self.request.user, event=instance, role=EventMemberRole.HOST)

    def get_queryset(self) -> QuerySet:
        qs = self.request.user.events.order_by("-start_at")

        # filtering by status
        status_filter = self.request.query_params.get("status", None)
        if status_filter is not None:
            try: status_filter = int(status_filter)
            except ValueError: return qs
            qs = qs.filter_by_status(status=status_filter)
        return qs

    @action(detail=True, methods=["post"])
    def close(self, request, pk):
        event = get_object_or_404(self.get_queryset(), pk=pk)
        event.close()
        return Response(self.get_serializer(instance=event).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def to_view(self, request, **kwargs):
        ev = EventViewer.objects.filter(user=self.request.user).order_by("-event__end_at").order_by("is_member")
        return Response(self.get_serializer(ev, many=True).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"])
    def get_friends_members(self, request, pk):
        event = get_object_or_404(self.get_queryset(), pk=pk)
        members = event.get_friends_members(request.user)
        data = EventMemberSerializer(members, many=True).data
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["get"])
    def validate_dates(self, request, **kwargs):
        start_at = self.request.query_params.get("start_at", None)
        end_at = self.request.query_params.get("end_at", None)

        if start_at is None or end_at is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class EventFlashbackViewSet(mixins.ListModelMixin,
                            mixins.RetrieveModelMixin,
                            mixins.CreateModelMixin,
                            viewsets.GenericViewSet):

    lookup_field = "pk"
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = FlashbackSerializer

    def get_serializer_class(self):
        if self.action == cnst.ACTION_CREATE:
            return FlashbackSerializer
        return FlashbackViewerSerializer

    def get_queryset(self):
        event_viewer = get_object_or_exception(EventViewer.objects.all(), PermissionDenied(), event__pk=self.kwargs.get("event_id"))
        queryset = FlashbackViewer.objects.filter(event_viewer=event_viewer)

        if self.action == cnst.ACTION_LIST:
            is_seen_filter = parse_boolean_value(self.request.query_params.get("is_seen", "false"))
            queryset = queryset.filter(is_seen=is_seen_filter)

        return queryset

    def perform_create(self, serializer):
        event_member = get_object_or_exception(
            EventMember.objects.all(), PermissionDenied(), event__pk=self.kwargs.get("event_id", None), user=self.request.user
        )

        serializer.save(event_member=event_member)

    @action(detail=True, methods=["post"])
    def mark_as_seen(self, request, pk):
        flashback_viewer = get_object_or_exception(
            FlashbackViewer.objects.all(), PermissionDenied(), user=self.request.user, pk=pk
        )

        flashback_viewer.is_seen = True
        flashback_viewer.save()


class MemberViewSet(mixins.ListModelMixin,
                    mixins.RetrieveModelMixin,
                    mixins.DestroyModelMixin,
                    viewsets.GenericViewSet):

    lookup_field = "user__pk"
    serializer_class = EventMemberSerializer
    permission_classes = [IsAuthenticated]

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
        queryset = request.user.friends.all()
        serializer = UserSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

