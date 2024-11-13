
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db import transaction
from django.conf import settings
import jwt
from .models import PhoneNumber, CommunityMember, Token
from .serializers import PhoneNumberSerializer, JoinCommunitySerializer, CommunityMemberSerializer, TokenSerializer
from .authentication import PhoneNumberJWTAuthentication


class RegisterPhoneNumberAPI(APIView):
    def post(self, request, *args, **kwargs):
        serializer = PhoneNumberSerializer(data=request.data)
        if serializer.is_valid():
            phone_number = serializer.save()
            return Response(
                {
                    "message": "The OTP is sent to your number",
                    "number": phone_number.number,
                    "number_id": phone_number.id
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JoinCommunityAPI(APIView):
    authentication_classes = [PhoneNumberJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = JoinCommunitySerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            with transaction.atomic():
                community_member = serializer.save()

            # Retrieve JWT token for the authenticated user
            token_instance, _ = Token.objects.get_or_create(phone_number=request.user)
            jwt_token = token_instance.jwt_token

            return Response(
                {
                    "message": "Successfully joined community",
                    "jwt": jwt_token,
                    "phone_number": request.user.number,
                    "name": community_member.name,
                    "community": dict(CommunityMember.COMMUNITY_CHOICES).get(community_member.community),
                    "profile_image": community_member.profile_image,
                    "role": community_member.get_role_display()
                },
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyOTPAPI(APIView):
    def post(self, request, *args, **kwargs):
        number = request.data.get("number")
        otp = request.data.get("otp")

        try:
            phone_instance = PhoneNumber.objects.get(number=number)
        except PhoneNumber.DoesNotExist:
            return Response({"message": "Phone number not found."}, status=status.HTTP_404_NOT_FOUND)

        if phone_instance.is_verified:
            jwt_token = self.generate_jwt(phone_instance)
            community_data = self.get_community_data(phone_instance)

            return Response(
                {
                    "message": "The number is already verified",
                    "jwt": jwt_token,
                    **community_data
                },
                status=status.HTTP_200_OK
            )

        if otp == "0000":
            phone_instance.is_verified = True
            phone_instance.save()
            jwt_token = self.generate_jwt(phone_instance)

            return Response(
                {
                    "message": "The user is verified now",
                    "jwt": jwt_token,
                    "phone_number": phone_instance.number,
                    "name": "",
                    "community": "",
                    "profile_image": ""
                },
                status=status.HTTP_200_OK
            )
        else:
            return Response({"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def generate_jwt(phone_instance):
        payload = {'number': phone_instance.number}
        jwt_token = jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')

        # Update or create token in the Token model
        Token.objects.update_or_create(
            phone_number=phone_instance,
            defaults={"jwt_token": jwt_token}
        )
        return jwt_token

    @staticmethod
    def get_community_data(phone_instance):
        try:
            community_member = CommunityMember.objects.get(phone_number=phone_instance)
            return {
                "phone_number": phone_instance.number,
                "name": community_member.name,
                "community": dict(CommunityMember.COMMUNITY_CHOICES).get(community_member.community),
                "profile_image": community_member.profile_image
            }
        except CommunityMember.DoesNotExist:
            return {
                "phone_number": phone_instance.number,
                "name": "",
                "community": "",
                "profile_image": ""
            }
