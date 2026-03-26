import unittest
import json
from app import app

class FlaskAppTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.app.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'healthy')

    def test_get_customers_pagination(self):
        """Test paginated customers endpoint"""
        response = self.app.get('/api/customers?page=1&limit=5')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('data', data)
        self.assertIn('total', data)
        self.assertIn('page', data)
        self.assertIn('limit', data)
        self.assertEqual(data['page'], 1)
        self.assertEqual(data['limit'], 5)
        self.assertLessEqual(len(data['data']), 5)

    def test_get_single_customer(self):
        """Test single customer endpoint"""
        response = self.app.get('/api/customers/CUST001')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('data', data)
        self.assertEqual(data['data']['customer_id'], 'CUST001')

    def test_get_nonexistent_customer(self):
        """Test 404 for missing customer"""
        response = self.app.get('/api/customers/NONEXISTENT')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertIn('error', data)

    def test_invalid_pagination_params(self):
        """Test invalid pagination parameters"""
        response = self.app.get('/api/customers?page=-1&limit=0')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertIn('error', data)

if __name__ == '__main__':
    unittest.main()
