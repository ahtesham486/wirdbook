from rest_framework import serializers
from .models import PhoneNumber, CommunityMember, Token

class PhoneNumberSerializer(serializers.ModelSerializer):
    class Meta:
        model = PhoneNumber
        fields = ['id', 'number', 'is_verified', 'role']
        read_only_fields = ['role']

    def validate_number(self, value):
        if PhoneNumber.objects.filter(number=value).exists():
            raise serializers.ValidationError("This phone number is already registered.")
        return value


class JoinCommunitySerializer(serializers.ModelSerializer):
    phone_number = serializers.HiddenField(default=serializers.CurrentUserDefault())
    role = serializers.HiddenField(default='user')

    class Meta:
        model = CommunityMember
        fields = ['id', 'name', 'community', 'profile_image', 'phone_number', 'role']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=CommunityMember.objects.all(),
                fields=['phone_number', 'community'],
                message="This phone number is already a member of the selected community."
            )
        ]

    def create(self, validated_data):
        return CommunityMember.objects.create(**validated_data)


class CommunityMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommunityMember
        fields = ['id', 'name', 'phone_number', 'community', 'profile_image', 'role']
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=CommunityMember.objects.all(),
                fields=['phone_number', 'community'],
                message="This phone number is already a member of the selected community."
            )
        ]

    def validate_role(self, value):
        community = self.initial_data.get('community')
        if value == 'admin' and CommunityMember.objects.filter(community=community, role='admin').exists():
            raise serializers.ValidationError("This community already has an admin.")
        return value


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = Token
        fields = ['jwt_token', 'created_at']
