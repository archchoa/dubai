from django.conf.urls import url

from .views import RegisterView, VerifyEmailView

urlpatterns = [
    url(r'^register/$', RegisterView.as_view(), name='api_register'),
    url(r'^verify-email/$', VerifyEmailView.as_view(), name='api_verify_email'),
]
