from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
import random

class QuizQuestion(models.Model):
    QUESTION_TYPES = [
        ('rarity', 'Rarity'),
        ('element_type', 'Element Type'),
        ('generation', 'Generation'),
        ('evolution_stage', 'Evolution Stage'),
        ('legendary_status', 'Legendary Status'),
        ('ability', 'Ability'),
        ('dex_id', 'Dex ID'),
        ('region', 'Region'),
        ('base_hp', 'Base HP'),
        ('type_combination', 'Type Combination'),
    ]

    question_text = models.CharField(max_length=500)
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES)
    correct_property = models.CharField(max_length=100)

    def __str__(self):
        return self.question_text

class PokemonCard(models.Model):
    name = models.CharField(max_length=100)
    hp = models.IntegerField()
    type = models.CharField(max_length=50)
    rarity = models.CharField(max_length=50)
    image_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.name} (HP: {self.hp}, Type: {self.type}, Rarity: {self.rarity})"

    class Meta:
        unique_together = ("name", "hp", "type")

class UserCollection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(PokemonCard, on_delete=models.CASCADE)
    count = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('user', 'card')  # One row per user-card combo

class Listing(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(PokemonCard, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    is_sold = models.BooleanField(default=False)

class Trade(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sender')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='receiver')
    sender_card = models.ForeignKey(PokemonCard, on_delete=models.CASCADE, related_name='sender_card')
    receiver_card = models.ForeignKey(PokemonCard, on_delete=models.CASCADE, related_name='receiver_card')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')])

class Badge(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    date_awarded = models.DateField(auto_now_add=True)

class TradeRequest(models.Model):
    from_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_trades')
    to_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_trades')
    offered_cards = models.ManyToManyField(PokemonCard, related_name='offered_in_trades')
    requested_cards = models.ManyToManyField(PokemonCard, related_name='requested_in_trades')
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        offered = ", ".join(c.name for c in self.offered_cards.all())
        requested = ", ".join(c.name for c in self.requested_cards.all())
        return f"{self.from_user} offers [{offered}] to {self.to_user} for [{requested}]"

class Achievement(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    required_trades = models.IntegerField()
    icon_url = models.URLField(blank=True)  # ✅ Add this

    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    balance = models.IntegerField(default=1000)  # $1000 initial wallet
    display_name = models.CharField(max_length=50, blank=True, null=True)
    profile_pic = models.ImageField(upload_to='profile_pics/', blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - ${self.balance}"

# Auto-create profile when user is registered
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
