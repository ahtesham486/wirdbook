from django.db import models

class PhoneNumber(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]

    number = models.CharField(max_length=15, unique=True)
    is_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    def __str__(self):
        return self.number

    @property
    def is_authenticated(self):
        return True  # Mimics authenticated user behavior


class CommunityMember(models.Model):
    COMMUNITY_CHOICES = [
        (1, 'Health'),
        (2, 'Software House'),
        (3, 'Sport'),
    ]

    ROLE_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
    ]

    name = models.CharField(max_length=255)
    phone_number = models.ForeignKey(PhoneNumber, on_delete=models.CASCADE, related_name="community_members")
    community = models.IntegerField(choices=COMMUNITY_CHOICES)
    profile_image = models.TextField()  # Stores base64 image data as text
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')

    def __str__(self):
        return f"{self.name} ({self.get_role_display()}) in {self.get_community_display()}"


class Token(models.Model):
    phone_number = models.OneToOneField(PhoneNumber, on_delete=models.CASCADE, related_name="token")
    jwt_token = models.TextField()  # Stores JWT as text to handle longer tokens
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Token for {self.phone_number}"
