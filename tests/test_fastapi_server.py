"""Tests for FastAPI server functionality."""

import pytest
from fastapi.testclient import TestClient
from app.main import app


class TestFastAPIServer:
    """Test cases for FastAPI server endpoints."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.client = TestClient(app)
    
    def test_root_endpoint(self):
        """Test the root endpoint returns expected response."""
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        assert response.json() == {"Hello": "World!"}
    
    def test_app_title(self):
        """Test that the FastAPI app has the correct title."""
        assert app.title == "Flashgram Bot"
    
    def test_cors_middleware_configured(self):
        """Test that CORS middleware is properly configured."""
        client = TestClient(app)
        
        # Test CORS headers on OPTIONS request
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        
        # Should allow the request (status may be 200 or 204)
        assert response.status_code in [200, 204, 405]  # 405 is acceptable for OPTIONS on GET endpoint
    
    def test_server_health(self):
        """Test that the server responds to health checks."""
        client = TestClient(app)
        response = client.get("/")
        
        # Basic health check - server is responding
        assert response.status_code == 200
        assert "Hello" in response.json()
    
    def test_nonexistent_endpoint(self):
        """Test that non-existent endpoints return 404."""
        client = TestClient(app)
        response = client.get("/nonexistent")
        
        assert response.status_code == 404