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


class VerifyEmailSerializer(serializers.Serializer):
    key = serializers.CharField()


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(max_length=128)
    new_password = serializers.CharField(max_length=128)

    def __init__(self, *args, **kwargs):
        super(ChangePasswordSerializer, self).__init__(*args, **kwargs)
        self.request = self.context.get('request')
        self.user = getattr(self.request, 'user', None)

    def validate_old_password(self, value):
        if not self.user or not self.user.check_password(value):
            raise serializers.ValidationError('Invalid password')
        return value

    def save(self):
        new_password = self.data.get('new_password')
        self.user.set_password(new_password)
        self.user.save()
