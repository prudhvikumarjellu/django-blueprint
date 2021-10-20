from django.conf.urls import url
from .views import LoginWithPassword, Logout, Register

urlpatterns = [
    url(r'^login$', LoginWithPassword.as_view(), name="Login API"),
    url(r'^register$', Register.as_view(), name="register user API"),
    url(r'^logout$', Logout.as_view(), name="Logout API"),
]
