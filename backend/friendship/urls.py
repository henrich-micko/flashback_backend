from django.urls import path
from friendship import views


urlpatterns = [
    # friend request api views
    path("requests/my", views.FriendRequestListAPIView.as_view()),
    path("requests/send/<int:to_user_pk>", views.SendFriendRequestAPIView.as_view()),
    path("requests/process/<int:other_user>/<str:friend_request_status>", views.ProcessFriendRequestAPIView.as_view()),

    # friendships api views
    path("friends/my", views.FriendshipListAPIView.as_view()),
    path("friends/<int:pk>", views.FriendshipRDAPIView.as_view()),
]