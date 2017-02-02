from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from rest_framework import serializers
from rest_framework.validators import UniqueValidator


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
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
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


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128, required=True)
    new_password = serializers.CharField(max_length=128, required=True)

    def validate(self, data):
        if data.get('old_password') == data.get('new_password'):
            raise serializers.ValidationError(
                'New password must be different from old password')
        return data
