from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Property  # Adjust if it's in a different app

User = get_user_model()

class LoginTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = 'testpass123'
        
        # Verified user
        self.verified_user = User.objects.create_user(
            username='verifieduser',
            email='verified@example.com',
            password=self.password,
            is_verified=True
        )

        # Unverified user
        self.unverified_user = User.objects.create_user(
            username='unverifieduser',
            email='unverified@example.com',
            password=self.password,
            is_verified=False
        )

    def test_successful_login_verified_user(self):
        response = self.client.post(reverse('login'), {
            'username': self.verified_user.username,
            'password': self.password
        })
        self.assertRedirects(response, reverse('dashboard'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_unverified_user(self):
        response = self.client.post(reverse('login'), {
            'username': self.unverified_user.username,
            'password': self.password
        })
        self.assertContains(response, 'Please verify your email address', status_code=200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_invalid_credentials(self):
        response = self.client.post(reverse('login'), {
            'username': 'nonexistent',
            'password': 'wrongpass'
        })
        self.assertContains(response, 'Invalid username/email or password', status_code=200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)


class PropertyModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_create_property(self):
        from .models import Property
        property = Property.objects.create(
            address='99 Example Street',
            purchase_date='2023-06-15',
            purchase_price=600000.00,
            property_type='House',  # Ensure this matches your choices
            weekly_mortgage=500.00,
            owner=self.user  # Set manually like in your view
        )

        self.assertEqual(Property.objects.count(), 1)
        self.assertEqual(property.owner.username, 'testuser')
        self.assertEqual(property.address, '99 Example Street')
        self.assertEqual(float(property.purchase_price), 600000.00)
