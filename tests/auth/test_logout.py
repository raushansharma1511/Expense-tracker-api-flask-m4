import json
import pytest
from unittest.mock import patch
from flask import url_for


class TestLogout:
    """Test cases for user logout endpoint."""

    def test_successful_logout(self, client, auth_headers):
        """Test successful logout with valid token."""
        # Make the request
        response = client.post(url_for("auth.logout"), headers=auth_headers)

        # Check response
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "logged out" in data["message"].lower()

    def test_logout_without_token(self, client):
        """Test logout without providing a token."""
        response = client.post(url_for("auth.logout"))

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data

    def test_logout_with_invalid_token(self, client):
        """Test logout with an invalid token."""
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.post(url_for("auth.logout"), headers=headers)

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data
        assert "Invalid token" in data["error"]
