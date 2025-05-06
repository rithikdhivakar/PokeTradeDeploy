from django.contrib import admin
from .models import (
    PokemonCard,
    UserCollection,
    Listing,
    TradeRequest,
    Achievement,
    UserAchievement
)

admin.site.register(PokemonCard)
admin.site.register(UserCollection)
admin.site.register(Listing)
admin.site.register(TradeRequest)
admin.site.register(Achievement)
admin.site.register(UserAchievement)

