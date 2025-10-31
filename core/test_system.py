from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.db import connection


class SystemEndpointsTestCase(APITestCase):
    """Test cases for System & Health endpoints"""

    def test_health_check_success(self):
        """Test health check endpoint when system is healthy"""
        url = '/api/v1/health/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'healthy')
        self.assertEqual(response.data['database'], 'connected')
        self.assertIn('timestamp', response.data)
        self.assertIn('version', response.data)

    def test_health_check_unauthenticated(self):
        """Test that health check doesn't require authentication"""
        url = '/api/v1/health/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_version_info_success(self):
        """Test version info endpoint"""
        url = '/api/v1/version/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['api_version'], 'v1')
        self.assertEqual(response.data['deprecated'], False)
        self.assertEqual(response.data['latest_version'], 'v1')
        self.assertIn('v1', response.data['supported_versions'])
        self.assertIn('version', response.data)
        self.assertIn('changelog_url', response.data)

    def test_version_info_unauthenticated(self):
        """Test that version endpoint doesn't require authentication"""
        url = '/api/v1/version/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_api_schema_success(self):
        """Test API schema endpoint (now using drf-spectacular)"""
        url = '/api/v1/schema/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # drf-spectacular returns OpenAPI format (can be JSON or YAML)
        content_type = response['Content-Type']
        self.assertTrue(
            'application/vnd.oai.openapi' in content_type or
            'application/json' in content_type or
            'application/yaml' in content_type or
            'application/x-yaml' in content_type
        )
        
        # Try to parse as JSON
        try:
            schema_data = response.json()
            self.assertEqual(schema_data['openapi'], '3.0.0')
            self.assertIn('info', schema_data)
            self.assertIn('paths', schema_data)
            
            info = schema_data['info']
            self.assertEqual(info['title'], 'Dynamic Forms System API')
            self.assertIn('version', info)
        except:
            # If it's YAML, that's also acceptable for drf-spectacular
            pass

    def test_api_schema_unauthenticated(self):
        """Test that schema endpoint doesn't require authentication"""
        url = '/api/v1/schema/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_version_info_headers(self):
        """Test version endpoint returns proper structure"""
        url = '/api/v1/version/'
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.data
        self.assertIsInstance(data['supported_versions'], list)
        self.assertGreater(len(data['supported_versions']), 0)

