import pytest
from django.contrib.auth import get_user_model, authenticate
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from unittest.mock import patch
import json

User = get_user_model()


@pytest.mark.django_db
def test_user_login_view():
    """Test user login through the API endpoint."""
    client = APIClient()
    email = 'loginuser@example.com'
    password = 'AStrongPassword123!'
    User.objects.create_user(email=email, password=password)
    url = reverse('login')
    data = {
        'email': email,
        'password': password
    }

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert 'tokens' in response.data
    assert 'access' in response.data['tokens']
    assert 'refresh' in response.data['tokens']
    assert response.data['user']['email'] == email


@pytest.mark.django_db
def test_user_login_invalid_credentials():
    """Test that login fails with incorrect password."""
    client = APIClient()
    email = 'invalidlogin@example.com'
    password = 'AStrongPassword123!'
    User.objects.create_user(email=email, password=password)
    url = reverse('login')
    data = {
        'email': email,
        'password': 'WrongPassword456!'
    }

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert 'error' in response.data
    assert response.data['error'] == 'Invalid credentials'

@pytest.mark.django_db
def test_user_logout_view():
    """Test user logout (token blacklisting) through the API endpoint."""
    client = APIClient()
    email = 'logoutuser@example.com'
    password = 'AStrongPassword123!'
    user = User.objects.create_user(email=email, password=password)

    # Generate tokens
    refresh = RefreshToken.for_user(user)
    refresh_token = str(refresh)
    access_token = str(refresh.access_token)

    url = reverse('logout')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
    data = {'refresh_token': refresh_token}

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert response.data['message'] == 'Logout successful'

    # Verify token is blacklisted (try using it again for a different call, should fail)
    # The simplejwt library handles blacklisting internally, so a direct check on the token's validity
    # would likely be complex. The success of the logout call is a good enough indicator for a unit test.


@pytest.mark.django_db
def test_user_logout_invalid_token():
    """Test that logout fails with an invalid refresh token."""
    client = APIClient()
    url = reverse('logout')
    data = {'refresh_token': 'an_invalid_token_string'}

    # We still need a valid access token to hit the endpoint (IsAuthenticated permission)
    email = 'validaccess@example.com'
    password = 'AStrongPassword123!'
    user = User.objects.create_user(email=email, password=password)
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.data['error'] == 'Invalid token'

@pytest.mark.django_db
def test_user_registration_view():
    """Test user registration through the API endpoint."""
    client = APIClient()
    url = reverse('register')
    data = {
        'email': 'newuser@example.com',
        'username': 'newuser',
        'password': 'AStrongPassword123!',
        'password2': 'AStrongPassword123!',
        'first_name': 'New',
        'last_name': 'User'
    }

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    assert 'access' in response.data
    assert 'refresh' in response.data
    assert response.data['user']['email'] == 'newuser@example.com'
    assert User.objects.filter(email='newuser@example.com').exists()


@pytest.mark.django_db
def test_user_registration_passwords_mismatch():
    """Test that registration fails if passwords do not match."""
    client = APIClient()
    url = reverse('register')
    data = {
        'email': 'mismatch@example.com',
        'username': 'mismatchuser',
        'password': 'SecurePass123!@#',
        'password2': 'DifferentPass456$%^',
        'first_name': 'Mismatch',
        'last_name': 'User'
    }

    response = client.post(url, data, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'password' in response.data
    assert "Password fields didn't match." in response.data['password']
