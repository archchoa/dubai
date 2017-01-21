from allauth.account.utils import send_email_confirmation
from allauth.account.views import ConfirmEmailView

from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import permissions, status
from rest_framework.generics import (CreateAPIView, ListAPIView,
                                     RetrieveUpdateAPIView)
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (AccountSerializer, GuestAccountSerializer,
                          VerifyEmailSerializer, ChangePasswordSerializer)

sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters('password', 'old_password', 'new_password'),
)


class RegisterView(CreateAPIView):
    """
    This view allows the user to register for an account in the site.
    Uses django-allauth to send a verification e-mail to the user.
    """
    serializer_class = AccountSerializer

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(RegisterView, self).dispatch(*args, **kwargs)

    def perform_create(self, serializer):
        user = serializer.save()

        # use django-allauth to send verification e-mail
        send_email_confirmation(self.request._request, user)

        return user


class VerifyEmailView(APIView, ConfirmEmailView):
    """
    This view allows the user to verify his e-mail. Uses django-allauth
    to confirm the e-mail.
    """
    allowed_methods = ['POST', 'HEAD', 'OPTIONS']

    def get_serializer(self, *args, **kwargs):
        return VerifyEmailSerializer(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)  # redirect to POST

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # set the verification key to the EmailConfirmation object
        self.kwargs['key'] = serializer.validated_data['key']

        # use django-allauth to confirm the e-mail
        confirmation = self.get_object()
        confirmation.confirm(self.request)

        # get the associated user
        user = confirmation.email_address.user
        account_serializer = AccountSerializer(user)

        return Response(account_serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    This view allows the user to change his password. Uses django's built-in
    methods to check and modify password.
    """
    permission_classes = [permissions.IsAuthenticated, ]

    def get_serializer(self, *args, **kwargs):
        return ChangePasswordSerializer(*args, **kwargs)

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(ChangePasswordView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(context={'request': request},
                                         data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({'status': 'OK'}, status=status.HTTP_200_OK)


class UserListView(ListAPIView):
    """
    This view displays the lists of users. If authenticated, full user details
    are shown. If not, only the first names are shown.
    """
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.user.is_authenticated():
            return AccountSerializer
        else:
            return GuestAccountSerializer


class ProfileView(RetrieveUpdateAPIView):
    """
    This view displays the user's profile and provides update functionality.
    Update functionality is already provided by DRF for PATCH, PUT requests.
    """
    permission_classes = [permissions.IsAuthenticated, ]
    serializer_class = AccountSerializer

    def get_object(self):
        return self.request.user  # user to be displayed and modified

    def retrieve(self, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
