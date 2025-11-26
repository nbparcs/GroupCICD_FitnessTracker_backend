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
        self.logout_url = reverse('logout')
        self.register_url = reverse('register')
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

    # --- UserLogoutView Tests ---
    def test_user_logout_success(self):
        """
        Ensure a user can log out by blacklisting their refresh token.
        """
        # First, log in to get a valid token
        login_data = {
            'email': self.email,
            'password': self.password
        }
        login_response = self.client.post(self.login_url, login_data, format='json')
        refresh_token = login_response.data['tokens']['refresh']
        
        # Now log out with the refresh token
        response = self.client.post(
            self.logout_url, 
            {'refresh_token': refresh_token}, 
            format='json',
            HTTP_AUTHORIZATION=f"Bearer {login_response.data['tokens']['access']}"
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Logout successful')

    def test_user_logout_unauthenticated(self):
        """
        Ensure an unauthenticated user cannot access the logout endpoint.
        """
        response = self.client.post(
            self.logout_url,
            {'refresh_token': 'anytoken'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # --- UserRegistrationView Tests ---
    def test_user_registration_success(self):
        """
        Ensure a new user can register and receive tokens.
        We provide all fields required by a standard User model and serializer.
        """
        # Use a unique email for this test
        data = {
            'email': 'newuser2@example.com',
            'username': 'newuser2',
            'password': 'AnotherStrongP@ssw0rd123',
            'password2': 'AnotherStrongP@ssw0rd123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(self.register_url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED, f"Errors: {response.data}")
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(User.objects.count(), 2)
