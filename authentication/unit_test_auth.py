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
