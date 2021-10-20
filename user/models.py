from django.db import models
import uuid
import jwt
from datetime import datetime
from social.settings import SECRET_KEY


class Users(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    mobile = models.CharField(max_length=15, blank=False, null=False)
    username = models.CharField(max_length=50, blank=False, null=False)
    email = models.CharField(max_length=100, blank=False, null=False)
    gender = models.CharField(max_length=10, default=None, blank=True, null=True)
    password = models.TextField( default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'users'
        managed = False


class LoginHistory(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    log_in_time = models.DateTimeField(blank=True, null=True)
    log_out_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'login_history'


class Activity(models.Model):
    _id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    log_in_time = models.DateTimeField(blank=True, null=True)
    log_out_time = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    deleted_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'login_history'

