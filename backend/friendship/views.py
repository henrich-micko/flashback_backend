from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveDestroyAPIView


from friendship.models import FriendRequest
from friendship.mixins import FriendRequestMixin, FriendshipMixin
from user.models import User


"""
====================
Friend Request Views
====================
"""


class SendFriendRequestAPIView(APIView, FriendRequestMixin):
    def post(self, request, to_user_pk):
        if self.request.user.pk == to_user_pk:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        user = get_object_or_404(User, pk=to_user_pk)
        friend_request, created = FriendRequest.objects.get_or_create(to_user=user, from_user=request.user)
        print(friend_request.pk)
        if not created:
            friend_request.status = FriendRequest.StatusChoices.PENDING
            friend_request.save()
        return Response(status=status.HTTP_200_OK)


class ProcessFriendRequestAPIView(APIView, FriendRequestMixin):
    def post(self, request, other_user: int, friend_request_status: str):
        try: other_user = User.objects.get(pk = other_user)
        except User.DoesNotExist: return Response(status=status.HTTP_400_BAD_REQUEST)

        try: friend_request = FriendRequest.objects.get(user_a=self.request.user, user_b=other_user)
        except FriendRequest.DoesNotExist: return Response(status=status.HTTP_400_BAD_REQUEST) 

        if not friend_request_status.upper() in FriendRequest.StatusChoices.names:
            return Response("Invalid FriendRequest status name.", status = status.HTTP_400_BAD_REQUEST)
        
        friend_request.status = FriendRequest.StatusChoices.names.index(friend_request_status.upper())
        friend_request.save()
        
        return Response(status=status.HTTP_200_OK)
    

class FriendRequestListAPIView(FriendRequestMixin, ListAPIView):
    pass


"""
================
Friendship Views
================
"""


class FriendshipListAPIView(FriendshipMixin, ListAPIView):
    pass


class FriendshipRDAPIView(FriendshipMixin, RetrieveDestroyAPIView):
    pass
