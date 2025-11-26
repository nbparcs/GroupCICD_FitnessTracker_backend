from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


# Helper class for mocking 'request' object presence in authenticate call
class Anything(object):
    def __eq__(self, other):
        return True


class UserAuthTests(APITestCase):

    def setUp(self):
        self.email = 'newuser@example.com'
        self.password = 'AnotherStrongP@ssw0rd123'
        self.user = User.objects.create_user(
            email=self.email,
            password=self.password,
            first_name='Test',
            last_name='User'
        )
        self.login_url = reverse('login')
        self.profile_url = reverse('profile')


    # --- UserLoginView Tests ---
    def test_user_login_success(self):
        """
        Ensure a user can log in successfully with correct credentials.
        """
        data = {
            'email': self.email,
            'password': self.password
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('tokens', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['email'], self.email)

    @patch('django.contrib.auth.authenticate')
    def test_user_login_failure_invalid_credentials(self, mock_authenticate):
        """
        Ensure login fails with invalid credentials.
        """
        mock_authenticate.return_value = None

        data = {
            'email': 'wronguser@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(self.login_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
