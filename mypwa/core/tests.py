from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Property

User = get_user_model()

class UserAuthTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_register(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'new@example.com',
            'password1': 'TestPassword12345',
            'password2': 'TestPassword12345'
        }, follow=True)

        print("\nREGISTER RESPONSE HTML:\n", response.content.decode())  # Debug print
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_login(self):
        # Create user with secure-enough password
        User.objects.create_user(username='testuser', email='test@example.com', password='TestPassword12345')
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'TestPassword12345'
        }, follow=True)
        self.assertEqual(response.status_code, 200)

class PropertyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='TestPassword12345')
        self.client.force_login(self.user)

    def test_add_property(self):
        response = self.client.post(reverse('add_property'), {
            'address': '123 Test Street',
            'purchase_date': '2023-01-01',
            'purchase_price': 500000,
            'weekly_rent': 1200,
            'weekly_mortgage': 800,
            'property_type': 'rental'  # Must match choices
        }, follow=True)

        print("\nPROPERTY ADD RESPONSE HTML:\n", response.content.decode())  # Debug print
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Property.objects.filter(address='123 Test Street').exists())
