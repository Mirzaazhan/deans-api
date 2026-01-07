from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from .models import Crisis, CrisisType, CrisisAssistance
from unittest.mock import patch

class CrisisModelTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Mock requests.post to avoid network calls
        patcher = patch('requests.post')
        cls.mock_post = patcher.start()
        cls.addClassCleanup(patcher.stop)

        # Create dependencies
        cls.crisis_type = CrisisType.objects.create(name="Fire")
        cls.assistance = CrisisAssistance.objects.create(name="Ambulance")
        
        # Create a crisis instance
        cls.crisis = Crisis.objects.create(
            your_name="John Doe",
            mobile_number="12345678",
            crisis_description="Big fire here!",
            crisis_status="PD", # Pending
            crisis_location1="1.3521",
            crisis_location2="103.8198"
        )
        cls.crisis.crisis_type.add(cls.crisis_type)
        cls.crisis.crisis_assistance.add(cls.assistance)

    def test_string_representation(self):
        """Test the string representation of the model"""
        self.assertEqual(str(self.crisis), str(self.crisis.crisis_id))

    def test_default_values(self):
        """Test that default values are set correctly"""
        # Assuming crisis_time is auto_now_add, it should be populated
        self.assertIsNotNone(self.crisis.crisis_time)
        # Verify status is what we set
        self.assertEqual(self.crisis.crisis_status, "PD")

class CrisisAPITest(TestCase):
    def setUp(self):
        # Mock requests.post
        self.patcher = patch('requests.post')
        self.mock_post = self.patcher.start()
        self.addCleanup(self.patcher.stop)

        self.client = APIClient()
        
        # Create admin user for protected endpoints
        self.admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'password123')
        
        # Create dependencies
        self.crisis_type = CrisisType.objects.create(name="Flood")
        self.assistance = CrisisAssistance.objects.create(name="Rescue")
        
        # Create initial crisis
        self.crisis = Crisis.objects.create(
            your_name="Jane Doe",
            mobile_number="87654321",
            crisis_description="Flooding!",
            crisis_status="PD",
            crisis_location1="Orchard Road"
        )
        self.crisis.crisis_type.add(self.crisis_type)
        self.crisis.crisis_assistance.add(self.assistance)
        
        self.valid_payload = {
            "your_name": "Test User",
            "mobile_number": "99999999",
            "crisis_type": [self.crisis_type.pk],
            "crisis_description": "Test Crisis",
            "crisis_assistance": [self.assistance.pk],
            "crisis_location1": "Test Location"
        }

    def test_list_crises(self):
        """Test retrieving a list of crises"""
        response = self.client.get('/api/crises/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should contain at least the one we created
        self.assertGreaterEqual(len(response.data), 1)

    def test_create_crisis(self):
        """Test creating a new crisis"""
        response = self.client.post('/api/crises/', self.valid_payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Crisis.objects.count(), 2)

    def test_retrieve_crisis(self):
        """Test retrieving a single crisis"""
        response = self.client.get(f'/api/crises/{self.crisis.pk}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['your_name'], "Jane Doe")

    def test_update_crisis_unauthorized(self):
        """Test updating a crisis without admin permissions"""
        # Anonymous user should not be able to update
        payload = {"crisis_status": "RS"} # Resolved
        response = self.client.patch(f'/api/crises/{self.crisis.pk}/', payload)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_crisis_admin(self):
        """Test updating a crisis with admin permissions"""
        self.client.force_authenticate(user=self.admin_user)
        payload = {"crisis_status": "RS"}
        response = self.client.patch(f'/api/crises/{self.crisis.pk}/', payload)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.crisis.refresh_from_db()
        self.assertEqual(self.crisis.crisis_status, "RS")

    def test_delete_crisis_admin(self):
        """Test deleting a crisis with admin permissions"""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/crises/{self.crisis.pk}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Crisis.objects.count(), 0)
