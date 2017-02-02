from allauth.account.utils import send_email_confirmation
from allauth.account.views import ConfirmEmailView

from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils.decorators import method_decorator
from django.views.decorators.debug import sensitive_post_parameters

from oauth2_provider.models import AccessToken
from oauth2_provider.views import TokenView

from rest_framework import status
from rest_framework.generics import (CreateAPIView, ListAPIView,
                                     RetrieveUpdateAPIView)
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (LoginSerializer, AccountSerializer,
                          GuestAccountSerializer, UpdateAccountSerializer,
                          VerifyEmailSerializer, ChangePasswordSerializer)

from . import permissions

import json
import re

sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters('password', 'old_password', 'new_password'),
)


def parse_token(token):
    token = re.search('(Bearer)(\s)(.*)', token)

    if token:
        return token.group(3)
    return None


class LoginView(APIView, TokenView):
    """
    This view logins a user and generates an access token.
    django-oauth-toolkit already handles the login through its own view.
    For activity's sake, below is a code that does the same exact thing.

    Please note that this login view will generate a new access token every
    time. Reason being, the purpose of this view is to provide an access token
    to the frontend / client. Once the client gets the access token, it will
    save this token somewhere and use it to authenticate other views throughout
    the whole session. Only if the token has expired will the client access
    this view again to generate another access token.
    """

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(LoginView, self).dispatch(*args, **kwargs)

    def get_serializer(self, *args, **kwargs):
        return LoginSerializer(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        user = authenticate(username=data.get('username'),
                            password=data.get('password'))

        if not user:
            return Response(
                {'detail': 'Login failed! Make sure username and password '
                           'is correct, or that the account is activated.'},
                status=status.HTTP_401_UNAUTHORIZED)

        url, headers, body, _status = self.create_token_response(request)

        body = json.loads(body)
        access_token = '%s %s' % (body.get('token_type'), body.get('access_token'))  # noqa

        return Response({'access_token': access_token}, status=_status)  # noqa


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

    def get_serializer(self, *args, **kwargs):
        return VerifyEmailSerializer(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return Response({"detail": 'Method "GET" not allowed.'},
                        status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # set the verification key to the EmailConfirmation object
        self.kwargs['key'] = serializer.validated_data['key']

        # use django-allauth to confirm the e-mail
        # automatically issues an HTTP 404 if invalid key is given
        confirmation = self.get_object()
        confirmation.confirm(self.request)

        # get the associated user and activate it
        user = confirmation.email_address.user
        user.is_active = 1
        user.save()

        account_serializer = AccountSerializer(user)

        return Response(account_serializer.data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """
    This view allows the user to change his password. Uses django's built-in
    methods to check and modify password.
    """
    # permission_classes = [permissions.IsAuthenticatedAndActive, ]

    def get_serializer(self, *args, **kwargs):
        return ChangePasswordSerializer(*args, **kwargs)

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(ChangePasswordView, self).dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(context={'request': request},
                                         data=request.data)
        serializer.is_valid(raise_exception=True)

        data = serializer.validated_data

        """
        Django-oauth-toolkit already handles the authentication behind the
        scenes, using its built-in authentication backend.

        Just use the request.user object to validate the user.

        For activity's sake, this is another way of authenticating a user
        based on the OAuth2 token.
        """
        if 'HTTP_AUTHORIZATION' in self.request.META:
            token = parse_token(self.request.META['HTTP_AUTHORIZATION'])
            if not token:
                return Response({'detail': 'Invalid access token'},
                                status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response({'detail': 'Unauthorized access'},
                            status=status.HTTP_401_UNAUTHORIZED)

        try:
            token = AccessToken.objects.get(token=token)
            user = token.user
        except AccessToken.DoesNotExist:
            return Response({'detail': 'Invalid access token'},
                            status=status.HTTP_401_UNAUTHORIZED)

        if not user:
            return Response({'detail': 'User does not exist'},
                            status=status.HTTP_401_UNAUTHORIZED)

        if not user.is_active:
            return Response({'detail': 'User is inactive'},
                            status=status.HTTP_401_UNAUTHORIZED)

        if not user.check_password(data.get('old_password')):
            return Response({'detail': 'Invalid password'},
                            status=status.HTTP_401_UNAUTHORIZED)

        user.set_password(data.get('new_password'))
        user.save()

        return Response({'status': 'OK'}, status=status.HTTP_200_OK)


class UserListView(ListAPIView):
    """
    This view displays the lists of users. If authenticated, full user details
    are shown. If not, only the first names are shown.
    """
    queryset = User.objects.all()

    def get_serializer_class(self):
        user = self.request.user
        if user.is_authenticated() and user.is_active:
            return AccountSerializer
        else:
            return GuestAccountSerializer


class ProfileView(RetrieveUpdateAPIView):
    """
    This view displays the user's profile and provides update functionality.
    Upon update, it checks if the e-mail was changed. If changed, the
    username is set to the new e-mail.
    """
    permission_classes = [permissions.IsAuthenticatedAndActive, ]
    serializer_class = UpdateAccountSerializer

    def get_object(self):
        return self.request.user  # user to be displayed and modified

    def retrieve(self, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_update(self, serializer):
        user = self.get_object()

        if 'email' in serializer.validated_data:
            email = serializer.validated_data['email']

            if user.email != email:
                serializer.save(username=email)
            else:
                serializer.save()
        else:
            serializer.save()
