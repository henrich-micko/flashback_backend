from rest_framework import routers
from event.views import EventViewSet, MemberViewSet

router = routers.DefaultRouter()
router.register(r"(?P<event_id>[^/.]+)/member", MemberViewSet, basename="member")
router.register(r"", EventViewSet, basename="event")

urlpatterns = router.urls
