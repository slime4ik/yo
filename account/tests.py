from django.test import TestCase, Client
from django.urls import reverse
from account.models import User  # Импорт кастомной модели
from .models import Ad, Category, ExchangeProposal
from .forms import AdForm, SearchForm

class ModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Тестовая категория')
        
    def test_ad_creation(self):
        ad = Ad.objects.create(
            title='Тестовое объявление',
            description='Тестовое описание',
            user=self.user,
            category=self.category,
            condition='new'
        )
        self.assertEqual(ad.title, 'Тестовое объявление')
        self.assertEqual(ad.get_condition_display(), 'Новое')
        self.assertTrue(Ad.objects.filter(id=ad.id).exists())

class FormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='formuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='Форма категория')
    
    def test_valid_ad_form(self):
        form_data = {
            'title': 'Тест форма',
            'description': 'Описание теста',
            'category': self.category.id,
            'condition': 'used'
        }
        form = AdForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_invalid_ad_form(self):
        form_data = {
            'title': '',
            'description': 'Описание',
            'category': self.category.id,
            'condition': 'used'
        }
        form = AdForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('title', form.errors)

class ViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='viewuser',
            password='testpass123'
        )
        self.category = Category.objects.create(name='View категория')
        self.ad = Ad.objects.create(
            title='View тест',
            description='Тест описания',
            user=self.user,
            category=self.category,
            condition='new'
        )
    
    def test_ad_list_view(self):
        response = self.client.get(reverse('ad_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'View тест')
    
    def test_ad_detail_view(self):
        response = self.client.get(reverse('ad_detail', args=[self.ad.id]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.ad.title)
    
    def test_create_view_authenticated(self):
        self.client.login(username='viewuser', password='testpass123')
        response = self.client.get(reverse('create'))
        self.assertEqual(response.status_code, 200)
    
    def test_create_view_unauthenticated(self):
        response = self.client.get(reverse('create'))
        self.assertEqual(response.status_code, 302)

class ExchangeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user1 = User.objects.create_user(username='user1', password='test123')
        self.user2 = User.objects.create_user(username='user2', password='test123')
        self.category = Category.objects.create(name='Обмен категория')
        
        self.ad1 = Ad.objects.create(
            title='Обмен 1',
            user=self.user1,
            category=self.category,
            condition='new'
        )
        
        self.ad2 = Ad.objects.create(
            title='Обмен 2',
            user=self.user2,
            category=self.category,
            condition='used'
        )
    
    def test_create_exchange(self):
        self.client.login(username='user1', password='test123')
        response = self.client.post(
            reverse('create_trade', args=[self.ad2.id]),
            {'sender_ad': self.ad1.id, 'comment': 'Тестовый обмен'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(ExchangeProposal.objects.exists())
    
    def test_accept_exchange(self):
        proposal = ExchangeProposal.objects.create(
            ad_sender=self.ad1,
            ad_receiver=self.ad2,
            status='pending'
        )
        self.client.login(username='user2', password='test123')
        response = self.client.post(reverse('accept_proposal', args=[proposal.id]))
        proposal.refresh_from_db()
        self.assertEqual(proposal.status, 'accepted')