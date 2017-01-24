from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from oauth2_provider.models import AccessToken

import re


class AccountSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(),
                                    message=_('E-mail address is already '
                                              'taken!'))]
    )
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True,
                                     style={'input_type': 'password'})

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data['email'],
            username=validated_data['email'],
            first_name=getattr(validated_data, 'first_name', ''),
            last_name=getattr(validated_data, 'last_name', ''),
            is_active=0
        )

        user.set_password(validated_data['password'])
        user.save()

        return user

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password')


class GuestAccountSerializer(AccountSerializer):
    class Meta:
        model = User
        fields = ('first_name', )


class UpdateAccountSerializer(AccountSerializer):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')


class VerifyEmailSerializer(serializers.Serializer):
    key = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True,
                                     write_only=True,
                                     style={'input_type': 'password'})

    def validate(self, data):
        user = authenticate(username=data.get('username'),
                            password=data.get('password'))

        if not user:
            raise serializers.ValidationError('Invalid username and password')

        if not user.is_active:
            raise serializers.ValidationError('This account is not activated yet')  # noqa

        return data


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128)
    new_password = serializers.CharField(max_length=128)

    def __init__(self, *args, **kwargs):
        super(ChangePasswordSerializer, self).__init__(*args, **kwargs)
        self.request = self.context.get('request')

    def validate(self, data):
        """
        Below is the actual code for getting the user based on the token.
        If authenticated, HTTP request will already contain the logged-in
        User object. This is because django-oauth2-toolkit already handles
        the authentication behind-the-scenes. Just be sure to include
        the IsAuthenticated permission class to the view.
        """
        self.user = getattr(self.request, 'user', None)

        """
        For activity's sake, this is another way of authenticating a user
        based on the authentication token.
        """
        if 'HTTP_AUTHORIZATION' in self.request.META:
            token = self.request.META['HTTP_AUTHORIZATION']
            token = re.search('(Bearer)(\s)(.*)', token)

            if token:
                token = token.group(3)
            else:
                raise serializers.ValidationError('Invalid access token')
        else:
            raise serializers.ValidationError('Unauthorized access')  # noqa

        try:
            token = AccessToken.objects.get(token=token)
            self.user = token.user
        except AccessToken.DoesNotExist:
            raise serializers.ValidationError('Invalid access token')

        if not self.user or \
           not self.user.check_password(data.get('old_password')):
            raise serializers.ValidationError('Invalid password')

        return data

    def save(self):
        new_password = self.data.get('new_password')
        self.user.set_password(new_password)
        self.user.save()
