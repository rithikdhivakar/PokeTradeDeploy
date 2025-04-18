from django.db import models
from django.contrib.auth.models import User

class PokemonCard(models.Model):

    name = models.CharField(max_length=100)
    set_name = models.CharField(max_length=100)
    card_number = models.CharField(max_length=20)
    image_url = models.URLField(blank=True, null=True)
    
    # Card details
    pokemon_type = models.CharField(max_length=20)
    hp = models.IntegerField(null=True, blank=True)
    card_text = models.TextField(blank=True)
    
    # Market information
    market_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    last_price_update = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.set_name} {self.card_number})"

    class Meta:
        unique_together = ['set_name', 'card_number']

class UserCard(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    card = models.ForeignKey(PokemonCard, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    date_acquired = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username}'s {self.card.name} x{self.quantity}"

    class Meta:
        unique_together = ['user', 'card']
