from django.contrib.auth.models import User
from allauth.account.utils import send_email_confirmation
from rest_framework import viewsets

from .serializers import AccountSerializer


class AccountViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = AccountSerializer

    def perform_create(self, serializer):
        # save email as username
        data = serializer.validated_data.copy()
        email = data['email']
        user = serializer.save(username=email)

        # django-allauth method
        send_email_confirmation(self.request._request, user)
