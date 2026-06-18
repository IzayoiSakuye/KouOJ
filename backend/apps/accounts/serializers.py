from django.contrib.auth import get_user_model
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

# 基本信息
class UserSerializer(serializers.ModelSerializer):
    is_admin = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "role",
            "is_admin",
            "solved_count",
            "submit_count",
            "nickname",
            "bio",
            "avatar_url",
        )
        read_only_fields = ("id", "username", "role", "is_admin", "solved_count", "submit_count")

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

# 修改密码使用
class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only = True)
    new_password = serializers.CharField(write_only = True, min_length = 6)
    def validate_new_password(self, value):
        # validate_password(value)
        return value
    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({"old_password":"旧密码不正确"})
        return attrs
    
    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=["password"])
        return user
