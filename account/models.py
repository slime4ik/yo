from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import string
import random
from unidecode import unidecode
from django.utils.text import slugify

class User(AbstractUser):
    pass

def generate_unique_code():
    length = 8
    characters = string.ascii_letters + string.digits
    return ''.join(random.choices(characters, k=length))

class Category(models.Model):
    name = models.CharField(max_length=50)
    
    def __str__(self):
        return self.name

class Ad(models.Model):
    CONDITION_CHOICES = [
        ('new', 'Новое'),
        ('used', 'Б/у'),
    ]
    
    id = models.CharField(
        max_length=8,
        primary_key=True,
        default=generate_unique_code,
        editable=False,
        unique=True
    )
    condition = models.CharField(max_length=50, choices=CONDITION_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                           on_delete=models.CASCADE,
                           related_name='ads')
    title = models.CharField(max_length=35)
    slug = models.SlugField(unique=True, blank=True)
    description = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='ads')
    
    class Meta: 
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['category']),
            models.Index(fields=['user']),
        ]
    def save(self, *args, **kwargs):
        # Обновляем slug только если имя изменилось или это новая запись
        if not self.slug or not self.pk or (
            self.pk and self.title != Ad.objects.get(pk=self.pk).title
        ):
            base_slug = slugify(unidecode(self.title))
            self.slug = base_slug
            counter = 1
            while Ad.objects.filter(slug=self.slug).exclude(pk=self.pk).exists():
                self.slug = f"{base_slug}-{counter}"
                counter += 1

        # Убедимся, что id установлен
        if not self.id:
            self.id = generate_unique_code()
            while Ad.objects.filter(id=self.id).exists():
                self.id = generate_unique_code()

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class ExchangeProposal(models.Model):
    STATUS_CHOICES = [
        ('pending', 'На рассмотрении'),
        ('accepted', 'Принято'),
        ('rejected', 'Отклонено'),
    ]

    ad_sender = models.ForeignKey(
        Ad,
        on_delete=models.CASCADE,
        related_name='sent_proposals',
        verbose_name="Предлагаемый товар (отправитель)"
    )
    ad_receiver = models.ForeignKey(
        Ad,
        on_delete=models.CASCADE,
        related_name='received_proposals',
        verbose_name="Запрашиваемый товар (получатель)"
    )
    comment = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Предложение #{self.id}: {self.ad_sender.title} → {self.ad_receiver.title}"

    class Meta:
        unique_together = ('ad_sender', 'ad_receiver')
        ordering = ['-created_at']
    

    def accept(self):
        if self.status != 'pending':
            return False  # Можно обработать ошибку
        
        self.status = 'accepted'
        self.save()
        
        # Помечаем другие предложения для этих объявлений как отклонённые
        ExchangeProposal.objects.filter(
            models.Q(ad_sender=self.ad_sender) |
            models.Q(ad_receiver=self.ad_receiver),
            status='pending'
        ).exclude(pk=self.pk).update(status='rejected')
        
        return True
    
    def reject(self):
        self.status = 'rejected'
        self.save()
        return True