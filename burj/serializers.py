from django.contrib.auth.models import User
from django.utils.translation import ugettext as _

from rest_framework import serializers
from rest_framework.validators import UniqueValidator


class AccountSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(),
                                    message=_('E-mail address is already taken!'))]
    )
    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password')


class VerifyEmailSerializer(serializers.Serializer):
    key = serializers.CharField()
