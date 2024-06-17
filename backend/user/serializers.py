from rest_framework.serializers import ModelSerializer, SerializerMethodField

from user.models import User
from friendship.models import FriendRequest, Friendship
from friendship.status import get_friendship_status


class UserSerializer(ModelSerializer):
    friends_count = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "date_joined",
            "friends_count",
            "about",
            "profile",
        ]

    def get_friends_count(self, obj):
        return obj.friendship_set.count()


class UserFromPOVSerializer(UserSerializer):
    pov = SerializerMethodField()
    mutual_friends = SerializerMethodField()
    friendship = SerializerMethodField()
    friends = SerializerMethodField()

    def __init__(self, user_pov, *args, **kwargs):
        self.user_pov = user_pov

        super().__init__(*args, **kwargs)

    class Meta(UserSerializer.Meta):
        fields = [
            *UserSerializer.Meta.fields,
            "pov",
            "mutual_friends",
            "friendship",
            "friends"
        ]

    def get_pov(self, obj):
        if self.user_pov == obj: return "me"
        if self.user_pov.is_friend_with(obj): return "friend"
        
        try: 
            if FriendRequest.objects.get(from_user=self.user_pov, to_user=obj): return "me-requested"
        except FriendRequest.DoesNotExist: pass

        try: 
            if FriendRequest.objects.get(from_user=obj, to_user=self.user_pov): return "other-requested"
        except FriendRequest.DoesNotExist: pass

        return "stranger"

    def get_mutual_friends(self, obj):
        from friendship.models import Friendship
        return map(
            lambda i: UserSerializer(i).data,
            Friendship.objects.get_mutual_friends(self.user_pov, obj)
        )

    def get_friendship(self, obj):
        try: fs = Friendship.objects.get(user_a=self.user_pov, user_b=obj)
        except Friendship.DoesNotExist: return None
        return fs.pk if fs != None else None
    
    def get_friends(self, obj):
        return [
            UserSerializer(i.get_other_user(obj)).data
            for i in obj.friendship_set.all()
        ]


class CreateUserSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "password",
        ]


class BasicUserSerializer(ModelSerializer):
    quick_detail = SerializerMethodField()
    profile_url = SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "quick_detail",
            "profile_url"
        ]

    def get_quick_detail(self, obj: User) -> str:
        return "He is cool"

    def get_profile_url(self, obj: User) -> str:
        return "https://www.alexgrey.com/img/containers/art_images/Godself-2012-Alex-Grey-watermarked.jpeg/121e98270df193e56eeaebcff787023f.jpeg"


class UserPOVSerializer(BasicUserSerializer):
    friendship_status = SerializerMethodField()

    class Meta(BasicUserSerializer.Meta):
        fields = [
            *BasicUserSerializer.Meta.fields,
            "friendship_status"
        ]

    def __init__(self, *args, **kwargs):
        self.user_pov = kwargs.pop("user_pov")
        super().__init__(*args, **kwargs)

    def get_friendship_status(self, obj):
        return get_friendship_status(
            user_from=self.user_pov,
            user_to=obj
        ).value
