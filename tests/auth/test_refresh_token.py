import json
import pytest
from unittest.mock import patch
from flask import url_for


class TestRefreshToken:
    """Test cases for token refresh endpoint."""

    def test_refresh_token_success(self, client, test_user):
        """Test successful token refresh."""
        # First login to get refresh token
        login_response = client.post(
            url_for("auth.login"),
            json={"username": "user@test.com", "password": "Password123!"},
        )

        login_data = json.loads(login_response.data)
        print(f"login data = {login_data}")
        refresh_token = login_data["refresh_token"]

        # Use refresh token to get new access token
        refresh_headers = {"Authorization": f"Bearer {refresh_token}"}
        response = client.post(url_for("auth.refresh-token"), headers=refresh_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert "access_token" in data
        assert len(data["access_token"]) > 20

    def test_refresh_with_access_token(self, app, client, auth_headers):
        """Test refresh attempt using an access token instead of refresh token."""
        response = client.post(url_for("auth.refresh-token"), headers=auth_headers)

        # Should fail because we're using an access token
        assert response.status_code != 200
        data = response.get_json()
        assert "error" in data

    def test_refresh_without_token(self, client):
        """Test refresh attempt without providing a token."""
        response = client.post(url_for("auth.refresh-token"))

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data
