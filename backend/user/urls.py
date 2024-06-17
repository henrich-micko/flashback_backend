from rest_framework.authtoken import views as rest_framework_views
from rest_framework import routers
from django.urls import path
from user import views

router = routers.DefaultRouter()
router.register(r"", views.UserViewSet, basename="user")

urlpatterns = [
    path("login/", rest_framework_views.obtain_auth_token),
] + router.urls
