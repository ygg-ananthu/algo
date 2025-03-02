from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from datetime import datetime, timedelta
from django.utils import timezone

class User(AbstractUser):
    virtual_balance = models.FloatField(default=0)
    groups = models.ManyToManyField(
        Group, related_name="customuser_set", blank=True)
    user_permissions = models.ManyToManyField(
        Permission, related_name="customuser_set", blank=True)
    client_id = models.CharField(max_length=100, blank=True, default="")
    client_secret = models.CharField(max_length=100, blank=True, default="")
    config = models.CharField(max_length=100, blank=True, default="")
    code = models.CharField(max_length=100,null=True, blank=True, default="")
    access_token = models.TextField(blank=True, default="")
    token_created_at = models.DateTimeField(null=True, blank=True)

    
    def update_balance(self, amount, action):
        """Update balance"""
        if action == 'INCREASE':
            self.virtual_balance += amount
        elif action == 'DECREASE':
            self.virtual_balance -= amount
        self.save()

    def update_access_token(self, new_token):
        """Update the access token and store the time only if it changes."""
        self.access_token = new_token
        self.token_created_at = datetime.now()
        self.save()
            
    def is_token_expired(self):
        """Check if the access token is expired (expires at 3:30 AM)."""
        if not self.token_created_at:
            return True  # If no token exists, it's considered expired
        
        now = timezone.now()
        created_date = self.token_created_at.date()  # Extract just the date
        expiry_time = timezone.make_aware(datetime.combine(created_date, datetime.min.time())).replace(hour=3, minute=30)
        # If token was created after 3:30 AM today, it expires the next day at 3:30 AM
        if self.token_created_at >= expiry_time:
            expiry_time += timedelta(days=1)
    
        return now >= expiry_time


class Strategy(models.Model):
    name = models.CharField(max_length=100, blank=True, default="")
    
class UserStrategy(models.Model):
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_active = models.BooleanField(default = True)
