import jwt
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from .models import Token, PhoneNumber


class PhoneNumberJWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None  # No authentication header provided

        # Validate and parse the token
        try:
            prefix, token = auth_header.split(' ')
            if prefix.lower() != 'bearer':
                raise AuthenticationFailed('Invalid token prefix.')
        except ValueError:
            raise AuthenticationFailed('Invalid token header. No credentials provided.')

        # Decode JWT token and extract phone number
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
            phone_number_value = payload.get('number')
            if not phone_number_value:
                raise AuthenticationFailed('Invalid token payload.')

            phone_number = PhoneNumber.objects.get(number=phone_number_value)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token has expired.')
        except jwt.DecodeError:
            raise AuthenticationFailed('Error decoding token.')
        except PhoneNumber.DoesNotExist:
            raise AuthenticationFailed('Phone number does not exist.')

        # Verify stored token matches provided token
        try:
            token_instance = Token.objects.get(phone_number=phone_number)
            if token_instance.jwt_token != token:
                raise AuthenticationFailed('Token does not match.')
        except Token.DoesNotExist:
            raise AuthenticationFailed('Token not found.')

        return (phone_number, None)
