from datetime import timedelta
import re

from django.contrib.auth.models import User
from django.core import mail
from django.urls import reverse
from django.utils import timezone

from oauthlib.common import generate_token
from oauth2_provider.models import AccessToken, get_application_model

from rest_framework import status
from rest_framework.test import APITestCase


Application = get_application_model()


def get_verification_key(mail):
    match = re.search('/accounts/confirm-email/(.+)/$',
                      mail.outbox[0].body,
                      re.MULTILINE)
    if match:
        return match.group(1)
    return None


def parse_token(token):
    token = re.search('(Bearer)(\s)(.*)', token)

    if token:
        return token.group(3)
    return None


class RegisterUserTest(APITestCase):
    def setUp(self):
        self.email = 'potus@whitehouse.gov'
        self.password = 'donaldtrump'
        self.first_name = 'Donald'
        self.last_name = 'Trump'

    def test_register_user(self):
        data = {
            'email': self.email,
            'password': self.password,
            'first_name': self.first_name,
            'last_name': self.last_name
        }

        response = self.client.post(reverse('api_register'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)

        data = {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name
        }
        self.assertEqual(response.data, data)

    def test_register_user_with_no_email(self):
        data = {
            'password': self.password,
        }

        response = self.client.post(reverse('api_register'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_user_with_no_password(self):
        data = {
            'email': self.email,
        }

        response = self.client.post(reverse('api_register'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class VerifyEmailTest(APITestCase):
    def setUp(self):
        self.email = 'potus@whitehouse.gov'
        self.password = 'donaldtrump'
        self.first_name = 'Donald'
        self.last_name = 'Trump'

    def test_activate_user(self):
        data = {
            'email': self.email,
            'password': self.password,
            'first_name': self.first_name,
            'last_name': self.last_name
        }

        # check if email was properly sent
        response = self.client.post(reverse('api_register'), data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)

        # get the key from the email
        key = get_verification_key(mail)

        self.assertNotEqual(key, None)

        # activate user account using key
        response = self.client.post(reverse('api_verify_email'), {'key': key})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # check if User object is returned and is same with registered user
        data = {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name
        }
        self.assertEqual(response.data, data)

        # activate using invalid key
        key = 'donaldtrumphatesmexicans'
        response = self.client.post(reverse('api_verify_email'), {'key': key})

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class LoginTest(APITestCase):
    def setUp(self):
        self.email = 'potus@whitehouse.gov'
        self.password = 'donaldtrump'

        self.user = User.objects.create_user(username=self.email,
                                             email=self.email,
                                             password=self.password,
                                             is_active=1)

        app_data = {
            'client_type': Application.CLIENT_PUBLIC,
            'authorization_grant_type': Application.GRANT_PASSWORD
        }

        self.app = Application.objects.create(**app_data)

    def test_login(self):
        data = {
            'username': self.email,
            'password': self.password,
            'grant_type': 'password',
            'client_id': self.app.client_id,
        }

        # login using credentials
        response = self.client.post(reverse('api_login'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access_token', response.data)

        # check if access token belongs to logged in user
        token = parse_token(response.data.get('access_token'))
        access_token = AccessToken.objects.get(token=token)

        self.assertEqual(access_token.user.username, self.email)

    def test_login_with_invalid_credentials(self):
        data = {
            'username': self.email,
            'password': self.password,
            'grant_type': 'password',
            'client_id': 'hillaryclinton',  # invalid client ID
        }

        response = self.client.post(reverse('api_login'), data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        data = {
            'username': self.email,
            'password': 'ilovemexicans',  # incorrect password
            'grant_type': 'password',
            'client_id': self.app.client_id,
        }

        response = self.client.post(reverse('api_login'), data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChangePasswordTest(APITestCase):
    def setUp(self):
        self.email = 'potus@whitehouse.gov'
        self.old_password = 'donaldtrump'
        self.new_password = 'melaniatrump'

        user_data = {
            'username': self.email,
            'password': self.old_password,
            'is_active': 1
        }

        self.user = User.objects.create_user(**user_data)

        app_data = {
            'client_type': Application.CLIENT_PUBLIC,
            'authorization_grant_type': Application.GRANT_PASSWORD
        }

        self.app = Application.objects.create(**app_data)

        token_data = {
            'user': self.user,
            'application': self.app,
            'expires': timezone.now() + timedelta(days=365),
            'token': generate_token(),
        }

        self.access_token = AccessToken.objects.create(**token_data)

    def test_change_password(self):
        password_data = {
            'old_password': self.old_password,
            'new_password': self.new_password,
        }

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self.access_token)  # noqa

        response = self.client.post(reverse('api_change_password'), password_data)  # noqa

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        login_data = {
            'username': self.email,
            'password': self.new_password,
            'grant_type': 'password',
            'client_id': self.app.client_id,
        }

        response = self.client.post(reverse('api_login'), login_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_invalid_password(self):
        password_data = {
            'old_password': 'hillaryclinton',
            'new_password': self.new_password,
        }

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self.access_token)  # noqa

        response = self.client.post(reverse('api_change_password'), password_data)  # noqa

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_with_same_password(self):
        password_data = {
            'old_password': self.old_password,
            'new_password': self.old_password,
        }

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self.access_token)  # noqa

        response = self.client.post(reverse('api_change_password'), password_data)  # noqa

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_with_invalid_token(self):
        password_data = {
            'old_password': self.old_password,
            'new_password': self.new_password,
        }

        response = self.client.post(reverse('api_change_password'), password_data)  # noqa

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserListTest(APITestCase):
    def setUp(self):
        self.email = 'potus@whitehouse.gov'
        self.password = 'donaldtrump'
        self.first_name = 'Donald'
        self.last_name = 'Trump'

        user_data = {
            'username': self.email,
            'email': self.email,
            'password': self.password,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': 1
        }

        self.user = User.objects.create_user(**user_data)

        app_data = {
            'client_type': Application.CLIENT_PUBLIC,
            'authorization_grant_type': Application.GRANT_PASSWORD
        }

        self.app = Application.objects.create(**app_data)

        token_data = {
            'user': self.user,
            'application': self.app,
            'expires': timezone.now() + timedelta(days=365),
            'token': generate_token(),
        }

        self.access_token = AccessToken.objects.create(**token_data)

    def test_view_users_with_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self.access_token)  # noqa
        response = self.client.get(reverse('api_users'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
        }

        self.assertEqual(dict(response.data[0]), data)

    def test_view_users_with_invalid_token(self):
        response = self.client.get(reverse('api_users'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            'first_name': self.first_name,
        }

        self.assertEqual(dict(response.data[0]), data)


class UserProfileTest(APITestCase):
    def setUp(self):
        self.email = 'potus@whitehouse.gov'
        self.password = 'donaldtrump'
        self.first_name = 'Donald'
        self.last_name = 'Trump'

        user_data = {
            'username': self.email,
            'email': self.email,
            'password': self.password,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'is_active': 1
        }

        self.user = User.objects.create_user(**user_data)

        user_data = {
            'username': 'flotus@whitehouse.gov',
            'email': 'flotus@whitehouse.gov',
            'password': 'michelleobama',
            'first_name': 'Melania',
            'last_name': 'Trump',
            'is_active': 1
        }

        User.objects.create_user(**user_data)

        app_data = {
            'client_type': Application.CLIENT_PUBLIC,
            'authorization_grant_type': Application.GRANT_PASSWORD
        }

        self.app = Application.objects.create(**app_data)

        token_data = {
            'user': self.user,
            'application': self.app,
            'expires': timezone.now() + timedelta(days=365),
            'token': generate_token(),
        }

        self.access_token = AccessToken.objects.create(**token_data)

    def test_view_profile_with_token(self):
        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self.access_token)  # noqa
        response = self.client.get(reverse('api_profile'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
        }

        self.assertEqual(response.data, data)

    def test_view_profile_with_invalid_token(self):
        response = self.client.get(reverse('api_profile'))

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_with_token(self):
        data = {
            'first_name': 'Hillary',
        }

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self.access_token)  # noqa
        response = self.client.patch(reverse('api_profile'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        data = {
            'email': self.email,
            'first_name': 'Hillary',
            'last_name': self.last_name,
        }

        self.assertEqual(response.data, data)

    def test_update_profile_with_invalid_token(self):
        data = {
            'first_name': 'Hillary',
        }

        response = self.client.patch(reverse('api_profile'), data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_profile_with_different_email(self):
        # change email to a different email
        data = {
            'email': 'obama@whitehouse.gov',
        }

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self.access_token)  # noqa
        response = self.client.patch(reverse('api_profile'), data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # change email to an already existing email
        data = {
            'email': 'flotus@whitehouse.gov',
        }

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self.access_token)  # noqa
        response = self.client.patch(reverse('api_profile'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # use invalid email
        data = {
            'email': 'thisisaninvalidemail',
        }

        self.client.credentials(HTTP_AUTHORIZATION='Bearer %s' % self.access_token)  # noqa
        response = self.client.patch(reverse('api_profile'), data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
