from django.contrib.auth import password_validation
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Role, User


class UserSerializer(serializers.ModelSerializer):
    """Read-only view of an account."""

    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name", "email", "phone",
            "role", "role_display", "is_active", "must_change_password",
            "date_joined", "last_login",
        ]
        read_only_fields = fields


def _check_role_allowed(request_user, role):
    """Admins may only manage normal users. Super Admins may manage any role."""
    if request_user.role == Role.ADMIN and role != Role.USER:
        raise serializers.ValidationError(
            "Admins can only create or manage accounts with the User role."
        )
    return role


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = [
            "username", "password", "first_name", "last_name",
            "email", "phone", "role",
        ]

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def validate_role(self, value):
        return _check_role_allowed(self.context["request"].user, value)

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.must_change_password = True
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "first_name", "last_name", "email", "phone", "role", "is_active",
        ]

    def validate_role(self, value):
        return _check_role_allowed(self.context["request"].user, value)

    def validate(self, attrs):
        request_user = self.context["request"].user
        if self.instance and self.instance.pk == request_user.pk:
            if "role" in attrs and attrs["role"] != self.instance.role:
                raise serializers.ValidationError("You cannot change your own role.")
            if attrs.get("is_active") is False:
                raise serializers.ValidationError("You cannot deactivate your own account.")
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_old_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value

    def validate_new_password(self, value):
        password_validation.validate_password(value, self.context["request"].user)
        return value


class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value


class HoplonTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Login response: access + refresh tokens and the user's details."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["username"] = user.username
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data
