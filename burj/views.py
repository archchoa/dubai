from allauth.account.utils import send_email_confirmation
from allauth.account.views import ConfirmEmailView

from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AccountSerializer, GuestAccountSerializer, VerifyEmailSerializer

sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters('password')
)


class RegisterView(CreateAPIView):
    serializer_class = AccountSerializer

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(RegisterView, self).dispatch(*args, **kwargs)

    def perform_create(self, serializer):
        # save email as username
        email = serializer.validated_data['email']
        user = serializer.save(username=email)

        # django-allauth method
        send_email_confirmation(self.request._request, user)

        return user


class VerifyEmailView(APIView, ConfirmEmailView):
    allowed_methods = ['POST', 'HEAD', 'OPTIONS']

    def get_serializer(self, *args, **kwargs):
        return VerifyEmailSerializer(*args, **kwargs)

    def get(self, request, *args, **kwargs):  # redirect to POST
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # use django-allauth view to return EmailConfirmation object
        self.kwargs['key'] = serializer.validated_data['key']
        confirmation = self.get_object()
        confirmation.confirm(self.request)

        # get the associated user
        user = confirmation.email_address.user
        account_serializer = AccountSerializer(user)

        return Response(account_serializer.data, status=status.HTTP_200_OK)


class UserListView(ListAPIView):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.user.is_authenticated():
            return AccountSerializer
        else:
            return GuestAccountSerializer
