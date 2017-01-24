from django.conf.urls import url

from .views import (LoginView, RegisterView, VerifyEmailView,
                    ChangePasswordView, UserListView, ProfileView)


urlpatterns = [
    url(r'^login/$', LoginView.as_view(), name='api_login'),
    url(r'^register/$', RegisterView.as_view(), name='api_register'),
    url(r'^verify-email/$', VerifyEmailView.as_view(), name='api_verify_email'),  # noqa
    url(r'^change-password/$', ChangePasswordView.as_view(), name='api_change_password'),  # noqa
    url(r'^users/$', UserListView.as_view(), name='api_users'),
    url(r'^profile/$', ProfileView.as_view(), name='api_profile')
]
