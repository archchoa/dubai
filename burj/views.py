from allauth.account.utils import send_email_confirmation
from allauth.account.views import ConfirmEmailView

from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from .permissions import WriteOnlyPermission
from .serializers import AccountSerializer, VerifyEmailSerializer

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
    permission_classes = (WriteOnlyPermission, )

    def get_serializer(self, *args, **kwargs):
        return VerifyEmailSerializer(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # use django-allauth view to return EmailConfirmation object
            self.kwargs['key'] = serializer.validated_data['key']
            confirmation = self.get_object()
            confirmation.confirm(self.request)

            # get the associated user
            user = confirmation.email_address.user
            account_serializer = AccountSerializer(user)

            return Response(account_serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
