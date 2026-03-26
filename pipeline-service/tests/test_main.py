import unittest
from unittest.mock import patch, MagicMock
from main import app
from fastapi.testclient import TestClient

class FastAPITestCase(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @patch('main.CustomerIngestionService')
    def test_ingest_endpoint_success(self, mock_service):
        """Test successful ingestion endpoint"""
        # Mock the ingestion service
        mock_instance = MagicMock()
        mock_instance.ingest_customers.return_value = {
            "status": "success",
            "records_processed": 20
        }
        mock_service.return_value = mock_instance
        
        response = self.client.post('/api/ingest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['records_processed'], 20)

    @patch('main.CustomerIngestionService')
    def test_ingest_endpoint_failure(self, mock_service):
        """Test ingestion endpoint failure"""
        # Mock the ingestion service to raise an exception
        mock_service.side_effect = Exception("Database connection failed")
        
        response = self.client.post('/api/ingest')
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn('detail', data)

    @patch('main.get_db_session')
    def test_get_customers_endpoint(self, mock_get_db):
        """Test get customers endpoint"""
        # Mock database session
        mock_db = MagicMock()
        mock_db.query.return_value.count.return_value = 2
        mock_db.query.return_value.offset.return_value.limit.return_value.all.return_value = []
        mock_get_db.return_value = iter([mock_db])
        
        response = self.client.get('/api/customers?page=1&limit=10')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('data', data)
        self.assertIn('total', data)
        self.assertIn('page', data)
        self.assertIn('limit', data)

    @patch('main.get_db_session')
    def test_get_customer_endpoint_found(self, mock_get_db):
        """Test get single customer endpoint when found"""
        # Mock database session
        mock_db = MagicMock()
        mock_customer = MagicMock()
        mock_customer.customer_id = 'CUST001'
        mock_customer.first_name = 'John'
        mock_customer.last_name = 'Doe'
        mock_customer.email = 'john.doe@example.com'
        mock_customer.phone = '+1-555-0101'
        mock_customer.address = '123 Main St'
        mock_customer.date_of_birth = None
        mock_customer.account_balance = None
        mock_customer.created_at = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_customer
        mock_get_db.return_value = iter([mock_db])
        
        response = self.client.get('/api/customers/CUST001')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('data', data)
        self.assertEqual(data['data']['customer_id'], 'CUST001')

    @patch('main.get_db_session')
    def test_get_customer_endpoint_not_found(self, mock_get_db):
        """Test get single customer endpoint when not found"""
        # Mock database session
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None
        mock_get_db.return_value = iter([mock_db])
        
        response = self.client.get('/api/customers/NONEXISTENT')
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertIn('detail', data)

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['status'], 'healthy')

if __name__ == '__main__':
    unittest.main()
