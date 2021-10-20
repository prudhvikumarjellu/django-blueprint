from django.conf.urls import include
from django.conf.urls import url

from social import views

urlpatterns = [
    url(r'^$', views.homepage, name="Homepage Api's"),
    url(r'^user/api/v1/', include('user.urls'), name="User Api's"),
]
