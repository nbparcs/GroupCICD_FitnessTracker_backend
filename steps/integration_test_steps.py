from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from datetime import date, timedelta
from django.utils import timezone
from steps.models import DailySteps, StepGoal, StepStreak

User = get_user_model()

class StepsAPITestCase(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create a step goal for the user
        self.step_goal = StepGoal.objects.create(
            user=self.user,
            daily_goal=10000
        )
        
        # Create a test step record
        self.step_data = {
            'date': '2025-10-31',
            'steps': 10000,
            'distance_km': 7.5,
            'calories_burned': 350,
            'active_minutes': 60,
            'source': 'manual'
        }
        
        self.step_record = DailySteps.objects.create(
            user=self.user,
            date='2025-10-31',
            steps=10000,
            distance_km=7.5,
            calories_burned=350,
            active_minutes=60,
            source='manual'
        )
        
        # Create a step streak
        self.step_streak = StepStreak.objects.create(
            user=self.user,
            current_streak=5,
            longest_streak=10,
            last_updated=date.today() - timedelta(days=1),
            total_days_goal_met=50
        )
        
        # Set up the client with authentication
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
    
    # Test creating a new daily step record
    def test_create_daily_steps(self):
        url = reverse('daily-steps-list')
        # Create a new step record with a unique date
        new_step_data = self.step_data.copy()
        new_step_data['date'] = '2025-11-01'  # Different date than the one in setup
        response = self.client.post(url, new_step_data, format='json')
        print(response.data)  # Debug output
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DailySteps.objects.count(), 2)  # One from setup, one new
        self.assertEqual(DailySteps.objects.latest('id').steps, new_step_data['steps'])
    
    # Test retrieving a daily step record
    def test_get_daily_steps(self):
        url = reverse('daily-steps-detail', args=[self.step_record.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['steps'], self.step_record.steps)
    
    # Test updating a daily step record
    def test_update_daily_steps(self):
        url = reverse('daily-steps-detail', args=[self.step_record.id])
        update_data = {'steps': 12000}
        response = self.client.patch(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.step_record.refresh_from_db()
        self.assertEqual(self.step_record.steps, 12000)
    
    # Test deleting a daily step record
    def test_delete_daily_steps(self):
        url = reverse('daily-steps-detail', args=[self.step_record.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(DailySteps.objects.count(), 0)
    
    # Test getting step goal

    # Test validation for step count
    def test_step_validation(self):
        url = reverse('daily-steps-list')
        invalid_data = self.step_data.copy()
        invalid_data['steps'] = -100  # Invalid step count
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # Test date validation
    def test_date_validation(self):
        url = reverse('daily-steps-list')
        future_date = (date.today() + timedelta(days=1)).isoformat()
        invalid_data = self.step_data.copy()
        invalid_data['date'] = future_date
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    # Test duplicate date prevention
    def test_duplicate_date_prevention(self):
        url = reverse('daily-steps-list')
        # Try to create a record with the same date as the one created in setUp
        response = self.client.post(url, self.step_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('date', response.data)
    
    # Test unauthenticated access
    def test_unauthenticated_access(self):
        self.client.force_authenticate(user=None)
        url = reverse('daily-steps-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    

    # Test step record with minimal data
    def test_create_minimal_steps(self):
        url = reverse('daily-steps-list')
        minimal_data = {
            'date': '2025-11-01',
            'steps': 5000
        }
        response = self.client.post(url, minimal_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DailySteps.objects.filter(date='2025-11-01').count(), 1)

    # Test step record with invalid source
    def test_invalid_source(self):
        url = reverse('daily-steps-list')
        invalid_data = self.step_data.copy()
        invalid_data['source'] = 'invalid_source'
        response = self.client.post(url, invalid_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # Test getting non-existent step record
    def test_get_nonexistent_steps(self):
        url = reverse('daily-steps-detail', args=[9999])  # Non-existent ID
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Test updating non-existent step record
    def test_update_nonexistent_steps(self):
        url = reverse('daily-steps-detail', args=[9999])  # Non-existent ID
        response = self.client.patch(url, {'steps': 5000}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Test deleting non-existent step record
    def test_delete_nonexistent_steps(self):
        url = reverse('daily-steps-detail', args=[9999])  # Non-existent ID
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # Test getting steps for a specific date range
    def test_get_steps_date_range(self):
        # Create some test data
        for i in range(1, 6):
            DailySteps.objects.create(
                user=self.user,
                date=date(2025, 10, i),
                steps=8000 + (i * 1000),
                distance_km=5.0 + (i * 0.5),
                calories_burned=300 + (i * 10),
                active_minutes=30 + (i * 5),
                source='device'
            )
        
        # Test date range filter
        url = f"{reverse('daily-steps-list')}?start_date=2025-10-02&end_date=2025-10-04"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should return 3 days of data (inclusive of start and end dates)
        self.assertEqual(len(response.data), 3)
        # Check if the dates are in the expected range
        for entry in response.data:
            entry_date = date.fromisoformat(entry['date'])
            self.assertTrue(date(2025, 10, 2) <= entry_date <= date(2025, 10, 4))
