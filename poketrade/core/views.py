from django.contrib import messages
from django.db.models import Q    
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm
from .models import PokemonCard, UserCollection, Listing, TradeRequest, UserAchievement, UserProfile, Achievement
import random, requests
from .forms import ProfileUpdateForm

def homepage(request):
    return render(request, 'home.html')

def about(request):
    return render(request, 'about.html')

@login_required
def update_profile(request):
    profile = request.user.userprofile
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated!')
            return redirect('update_profile')
    else:
        form = ProfileUpdateForm(instance=profile)
    
    return render(request, 'update_profile.html', {'form': form})

def card_details(request, card_id):
    card = get_object_or_404(PokemonCard, id=card_id)
    poke_name = card.name.lower().replace(" ", "-")

    poke_url = f"https://pokeapi.co/api/v2/pokemon/{poke_name}"
    species_url = f"https://pokeapi.co/api/v2/pokemon-species/{poke_name}"

    print("PokeAPI URL (pokemon):", poke_url)
    print("PokeAPI URL (species):", species_url)

    try:
        poke_response = requests.get(poke_url)
        if poke_response.status_code != 200:
            raise Exception(f"PokeAPI returned {poke_response.status_code}")
        poke_data = poke_response.json()

        species_response = requests.get(species_url)
        if species_response.status_code != 200:
            raise Exception(f"PokeAPI species returned {species_response.status_code}")
        species_data = species_response.json()

    except Exception as e:
        return render(request, 'card_detail.html', {
            'card': card,
            'error': f"PokeAPI error: {str(e)}"
        })

    # Extract desired data from the JSON responses
    height = poke_data.get('height')
    weight = poke_data.get('weight')
    abilities = [a['ability']['name'] for a in poke_data.get('abilities', [])]

    flavor_text_entries = species_data.get('flavor_text_entries', [])
    english_flavor_text = next(
        (entry['flavor_text'] for entry in flavor_text_entries if entry['language']['name'] == 'en'),
        "No description available."
    )

    return render(request, 'card_detail.html', {
        'card': card,
        'height': height,
        'weight': weight,
        'abilities': abilities,
        'flavor_text': english_flavor_text,
    })


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            assign_random_cards(user)
            login(request, user)
            return redirect('my_collection')
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def home_redirect(request):
    if request.user.is_authenticated:
        return redirect('my_collection')
    return redirect('login')

def assign_random_cards(user):
    import requests
    from .models import PokemonCard, UserCollection
    import random

    url = "https://api.pokemontcg.io/v2/cards"
    params = {"pageSize": 50}  # More to choose from
    response = requests.get(url, params=params)
    data = response.json()

    cards = data["data"]
    random.shuffle(cards)

    count = 0
    for item in cards:
        name = item.get("name", "Unknown")

        # Skip cards with spaces in name (PokeAPI limitation)
        if " " in name:
            continue

        hp = int(item.get("hp", "0")) if item.get("hp", "0").isdigit() else 0
        types = item.get("types", [])
        type_ = types[0] if types else "Unknown"
        rarity = item.get("rarity", "Common")
        image_url = item.get("images", {}).get("small", "")

        # Create or get card in DB
        card, _ = PokemonCard.objects.get_or_create(
            name=name,
            hp=hp,
            type=type_,
            defaults={"rarity": rarity, "image_url": image_url}
        )

        # Assign to user
        user_card, created = UserCollection.objects.get_or_create(user=user, card=card)
        if not created:
            user_card.count += 1
        user_card.save()

        count += 1
        if count >= 5:
            break

@login_required
def my_collection(request):
    cards = UserCollection.objects.filter(user=request.user, count__gt=0)
    listed_cards = Listing.objects.filter(seller=request.user, is_sold=False).values_list('card', flat=True)
    return render(request, 'collection.html', {'cards': cards, 'listed_cards': listed_cards})

@login_required
def user_list(request):
    users = User.objects.exclude(id=request.user.id).filter(is_staff=False)
    return render(request, 'user_list.html', {'users': users})

@login_required
def user_collection(request, user_id):
    selected_user = User.objects.get(id=user_id)
    cards = UserCollection.objects.filter(user=selected_user, count__gt=0).select_related('card')
    
    return render(request, 'user_collection.html', {
        'cards': cards,
        'selected_user': selected_user
    })

@login_required
def list_for_sale(request, card_id):
    card = PokemonCard.objects.get(id=card_id)
    user_card = UserCollection.objects.get(user=request.user, card=card)

    listed_count = Listing.objects.filter(seller=request.user, card=card, is_sold=False).count()

    if request.method == 'POST':
        price = int(request.POST.get('price'))
        if listed_count >= user_card.count:
            return HttpResponse("❌ You’ve already listed all available copies of this card.", status=403)

        Listing.objects.create(seller=request.user, card=card, price=price)
        return redirect('my_collection')

    return render(request, 'list_for_sale.html', {
        'card': card,
        'remaining': user_card.count - listed_count,
        'listed_count': listed_count
    })

@login_required
def marketplace(request):
    listings = Listing.objects.exclude(seller=request.user).filter(is_sold=False)

    # Filters
    card_type = request.GET.get('type')
    min_hp = request.GET.get('min_hp')
    rarity = request.GET.get('rarity')

    if card_type:
        listings = listings.filter(card__type__iexact=card_type)
    if min_hp:
        listings = listings.filter(card__hp__gte=min_hp)
    if rarity:
        listings = listings.filter(card__rarity__iexact=rarity)

    # Get dynamic dropdown values from DB
    all_types = PokemonCard.objects.values_list('type', flat=True).distinct()
    all_rarities = PokemonCard.objects.values_list('rarity', flat=True).distinct()

    return render(request, 'marketplace.html', {
        'listings': listings,
        'types': all_types,
        'rarities': all_rarities
    })

@login_required
def buy_card(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    if listing.seller == request.user or listing.is_sold:
        return redirect('marketplace')

    buyer = request.user
    buyer_profile = UserProfile.objects.get(user=buyer)

    if buyer_profile.balance < listing.price:
        messages.error(request, "❌ You don’t have enough funds to buy this card.")
        return redirect('marketplace')

    # 💰 Deduct money from buyer
    buyer_profile.balance -= listing.price
    buyer_profile.save()
        
    # 💸 Credit money to seller
    seller_profile = UserProfile.objects.get(user=listing.seller)
    seller_profile.balance += listing.price
    seller_profile.save()

    # 🃏 Add card to buyer's collection
    user_card, created = UserCollection.objects.get_or_create(user=buyer, card=listing.card)
    
    if created:
        user_card.count = 1  # New entry — set explicitly to 1
    else:
        user_card.count += 1  # Existing entry — increment count

    user_card.save()
        
    # ❌ Remove 1 card from seller's collection
    try:
        seller_card = UserCollection.objects.get(user=listing.seller, card=listing.card)
        seller_card.count -= 1
        if seller_card.count == 0:
            seller_card.delete()
        else:
            seller_card.save()
    except UserCollection.DoesNotExist:
        pass  # Shouldn't happen, but failsafe in case

    # ✅ Mark listing as sold
    listing.is_sold = True
    listing.save()

    return redirect('marketplace')

@login_required
def send_trade_request(request, user_id):
    other_user = User.objects.get(id=user_id)
    my_cards = UserCollection.objects.filter(user=request.user, count__gt=0)
    their_cards = UserCollection.objects.filter(user=other_user, count__gt=0)

    if request.method == 'POST':
        offered_card_id = request.POST.get('offered_card')
        requested_card_id = request.POST.get('requested_card')
        offered_card = PokemonCard.objects.get(id=offered_card_id)
        requested_card = PokemonCard.objects.get(id=requested_card_id)

        TradeRequest.objects.create(
            from_user=request.user,
            to_user=other_user,
            offered_card=offered_card,
            requested_card=requested_card,
        )
        return redirect('user_collection', user_id=other_user.id)

    return render(request, 'send_trade.html', {
        'other_user': other_user,
        'my_cards': my_cards,
        'their_cards': their_cards
    })

@login_required
def trade_requests(request):
    incoming = TradeRequest.objects.filter(to_user=request.user, status='pending')
    outgoing = TradeRequest.objects.filter(from_user=request.user).exclude(status='accepted')

    return render(request, 'trade_requests.html', {
        'incoming_requests': incoming,
        'outgoing_requests': outgoing
    })


@login_required
def accept_trade(request, trade_id):
    trade = TradeRequest.objects.get(id=trade_id)

    if trade.to_user != request.user or trade.status != 'pending':
        return redirect('trade_requests')

    # Remove offered card from sender
    try:
        sender_card = UserCollection.objects.get(user=trade.from_user, card=trade.offered_card)
        if sender_card.count > 0:
            sender_card.count -= 1
            sender_card.save()
        else:
            messages.error(request, "Sender doesn't have the offered card anymore.")
            return redirect('trade_requests')
    except UserCollection.DoesNotExist:
        messages.error(request, "Sender doesn't have the offered card.")
        return redirect('trade_requests')

    # Remove requested card from receiver
    try:
        receiver_card = UserCollection.objects.get(user=trade.to_user, card=trade.requested_card)
        if receiver_card.count > 0:
            receiver_card.count -= 1
            receiver_card.save()
        else:
            messages.error(request, "You don't have the requested card anymore.")
            return redirect('trade_requests')
    except UserCollection.DoesNotExist:
        messages.error(request, "You don't have the requested card.")
        return redirect('trade_requests')

    # ✅ Add received cards properly

    receiver_new_card, receiver_created = UserCollection.objects.get_or_create(
        user=trade.to_user, card=trade.offered_card
    )
    sender_new_card, sender_created = UserCollection.objects.get_or_create(
        user=trade.from_user, card=trade.requested_card
    )

    receiver_new_card.count = 1 if receiver_created else receiver_new_card.count + 1
    sender_new_card.count = 1 if sender_created else sender_new_card.count + 1

    receiver_new_card.save()
    sender_new_card.save()

    # ✅ Mark trade accepted
    trade.status = 'accepted'
    trade.save()


    # ✅ Award achievements to the initiating user
    from_user = trade.from_user

    from_user_trade_count = TradeRequest.objects.filter(
        Q(from_user=from_user) | Q(to_user=from_user),
        status='accepted'
    ).count()

    earned = UserAchievement.objects.filter(user=from_user).values_list('achievement_id', flat=True)
    eligible = Achievement.objects.filter(required_trades__lte=from_user_trade_count).exclude(id__in=earned)

    for achievement in eligible:
        UserAchievement.objects.create(user=from_user, achievement=achievement)

    # ✅ Also award achievements to the receiver (to_user)
    to_user = trade.to_user

    to_user_trade_count = TradeRequest.objects.filter(
        Q(from_user=to_user) | Q(to_user=to_user),
        status='accepted'
    ).count()

    earned_to_user = UserAchievement.objects.filter(user=to_user).values_list('achievement_id', flat=True)
    eligible_to_user = Achievement.objects.filter(required_trades__lte=to_user_trade_count).exclude(id__in=earned_to_user)

    for achievement in eligible_to_user:
        UserAchievement.objects.create(user=to_user, achievement=achievement)

    return redirect('trade_requests')


@login_required
def reject_trade(request, trade_id):
    trade = TradeRequest.objects.get(id=trade_id)

    if trade.to_user == request.user and trade.status == 'pending':
        trade.status = 'rejected'
        trade.save()

    return redirect('trade_requests')

from django.db.models import Q

@login_required
def my_achievements(request):
    user = request.user

    # All achievements
    all_achievements = Achievement.objects.all()

    # Achievements this user has earned
    earned = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)

    # Count of accepted trades
    trade_count = TradeRequest.objects.filter(
        Q(from_user=user) | Q(to_user=user),
        status='accepted'
    ).count()

    # Prepare achievement progress
    progress_data = []
    for achievement in all_achievements:
        unlocked = achievement.id in earned
        progress_data.append({
            'achievement': achievement,
            'unlocked': unlocked,
            'progress': min(trade_count, achievement.required_trades),
        })

    return render(request, 'my_achievements.html', {
        'progress_data': progress_data
    })

