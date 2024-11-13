
from django.urls import path
from .views import RegisterPhoneNumberAPI ,VerifyOTPAPI,JoinCommunityAPI

urlpatterns = [
    path('register-phone/', RegisterPhoneNumberAPI.as_view(), name='register-phone'),
    path('verify-otp/', VerifyOTPAPI.as_view(), name='verify-otp'),
     path('join-community/', JoinCommunityAPI.as_view(), name='join-community'),
     
]
