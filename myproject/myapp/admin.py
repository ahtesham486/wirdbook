from django.contrib import admin
from .models import PhoneNumber,CommunityMember,Token

admin.site.register(Token)
admin.site.register(PhoneNumber)
admin.site.register(CommunityMember)