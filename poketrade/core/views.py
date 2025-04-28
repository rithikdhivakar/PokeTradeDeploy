from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import TradeRequestForm
from .forms import CustomUserCreationForm
from .models import PokemonCard, UserCollection, Listing, TradeRequest, UserAchievement, UserProfile, Achievement, \
    QuizQuestion
import random
import requests
from .forms import ProfileUpdateForm

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .forms import TradeRequestForm, CustomUserCreationForm, ProfileUpdateForm
from .models import PokemonCard, UserCollection, Listing, TradeRequest, UserAchievement, UserProfile, Achievement, \
    QuizQuestion
import random
import requests


@login_required
def quiz_view(request):
    if request.method == 'GET':
        questions = random.sample(list(QuizQuestion.objects.all()), 5)
        quiz_data = []

        for question in questions:
            while True:
                pokemon_id = random.randint(1, 151)
                pokemon_response = requests.get(f"https://pokeapi.co/api/v2/pokemon/{pokemon_id}")

                if pokemon_response.status_code != 200:
                    continue

                pokemon_data = pokemon_response.json()
                pokemon_name = pokemon_data['name']

                if ' ' not in pokemon_name:
                    break

            correct_answer = get_correct_answer(pokemon_data, question)
            wrong_answers = generate_wrong_options(question.question_type, correct_answer)

            options = wrong_answers + [correct_answer]
            random.shuffle(options)

            quiz_data.append({
                'question_id': question.id,
                'question_text': question.question_text.replace('________', pokemon_name.capitalize()),
                'pokemon_name': pokemon_name.capitalize(),
                'question_type': question.question_type,
                'correct_property': question.correct_property,
                'pokemon_data': pokemon_data,
                'options': options,
                'correct_answer': correct_answer
            })

        context = {'quiz_data': quiz_data}
        return render(request, 'quiz.html', context)

    elif request.method == 'POST':
        score = 0
        total = int(request.POST.get('total_questions', 5))
        pokemon_name = request.POST.get('pokemon_name')

        for key, value in request.POST.items():
            if key.startswith('q'):
                question_id = key[1:]
                selected_answer = value
                correct_answer = request.POST.get(f'correct_q{question_id}')

                # Fix case/space matching
                if selected_answer.strip().lower() == correct_answer.strip().lower():
                    score += 1

        card_image_url = None

        if score == total:
            user = request.user
            card = PokemonCard.objects.filter(name__iexact=pokemon_name).first()

            if not card:
                tcg_url = "https://api.pokemontcg.io/v2/cards"
                params = {"q": f'name:\"{pokemon_name}\"'}
                response = requests.get(tcg_url, params=params)

                if response.status_code == 200:
                    data = response.json()
                    cards = data.get("data", [])

                    if cards:
                        card_data = cards[0]
                        name = card_data.get("name", "Unknown")
                        hp = int(card_data.get("hp", "0")) if card_data.get("hp", "0").isdigit() else 0
                        types = card_data.get("types", [])
                        type_ = types[0] if types else "Unknown"
                        rarity = card_data.get("rarity", "Common")
                        image_url = card_data.get("images", {}).get("small", "")

                        card = PokemonCard.objects.create(
                            name=name,
                            hp=hp,
                            type=type_,
                            rarity=rarity,
                            image_url=image_url
                        )
                        card_image_url = image_url
                    else:
                        message = f"❌ Pokémon Card '{pokemon_name}' not found."
                        return render(request, 'quiz_result.html', {'message': message, 'success': False})

                else:
                    message = "❌ Could not connect to external database."
                    return render(request, 'quiz_result.html', {'message': message, 'success': False})

            user_card, created = UserCollection.objects.get_or_create(user=user, card=card)
            if not created:
                user_card.count += 1
            user_card.save()

            message = f"🎉 Congratulations! You have earned a new {pokemon_name.capitalize()} card!"
            success = True
            if not card_image_url:
                card_image_url = card.image_url

        else:
            message = "❌ One or more answers are wrong. Please try again."
            success = False

        return render(request, 'quiz_result.html', {
            'message': message,
            'success': success,
            'score': score,
            'total': total,
            'card_image_url': card_image_url
        })


def get_correct_answer(pokemon_data, question):
    if question.question_type == 'element_type':
        return pokemon_data['types'][0]['type']['name'].capitalize()
    elif question.question_type == 'base_hp':
        for stat in pokemon_data['stats']:
            if stat['stat']['name'] == 'hp':
                return str(stat['base_stat'])
    elif question.question_type == 'ability':
        return pokemon_data['abilities'][0]['ability']['name'].capitalize()
    elif question.question_type == 'generation':
        species_url = pokemon_data['species']['url']
        species_response = requests.get(species_url)
        if species_response.status_code == 200:
            species_data = species_response.json()
            return species_data['generation']['name'].replace('-', ' ').capitalize()
    elif question.question_type == 'region':
        species_url = pokemon_data['species']['url']
        species_response = requests.get(species_url)
        if species_response.status_code == 200:
            species_data = species_response.json()
            habitat = species_data.get('habitat')
            return habitat['name'].capitalize() if habitat else "Unknown"
    elif question.question_type == 'evolution_stage':
        return "Basic"
    return "Unknown"


def generate_wrong_options(question_type, correct_answer):
    wrong_options = []

    if question_type == 'element_type':
        all_types = ['Fire', 'Water', 'Grass', 'Electric', 'Psychic', 'Rock', 'Ghost', 'Ground', 'Flying', 'Bug',
                     'Dark', 'Steel', 'Fairy', 'Dragon', 'Fighting', 'Poison', 'Ice', 'Normal']
        if correct_answer in all_types:
            all_types.remove(correct_answer)
        wrong_options = random.sample(all_types, 3)
    elif question_type == 'base_hp':
        wrong_options = [str(int(correct_answer) + 10), str(int(correct_answer) - 5), str(int(correct_answer) + 15)]
    elif question_type == 'ability':
        all_abilities = ['Overgrow', 'Blaze', 'Torrent', 'Pressure', 'Run Away', 'Swift Swim', 'Intimidate', 'Levitate']
        if correct_answer in all_abilities:
            all_abilities.remove(correct_answer)
        wrong_options = random.sample(all_abilities, 3)
    elif question_type == 'generation':
        all_generations = ['Generation i', 'Generation ii', 'Generation iii', 'Generation iv', 'Generation v',
                           'Generation vi', 'Generation vii', 'Generation viii']
        if correct_answer in all_generations:
            all_generations.remove(correct_answer)
        wrong_options = random.sample(all_generations, 3)
    elif question_type == 'region':
        all_regions = ['Kanto', 'Johto', 'Hoenn', 'Sinnoh', 'Unova', 'Kalos', 'Alola', 'Galar']
        if correct_answer in all_regions:
            all_regions.remove(correct_answer)
        wrong_options = random.sample(all_regions, 3)
    elif question_type == 'evolution_stage':
        wrong_options = ['Stage 1', 'Stage 2', 'Final']

    return wrong_options


# Your other views (home, marketplace, user_collection, etc) remain exactly as you posted.


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
    cards = UserCollection.objects.filter(user=request.user, count__gt=0).select_related('card')
    listed_cards = Listing.objects.filter(seller=request.user, is_sold=False).values_list('card', flat=True)

    detailed_cards = []

    for item in cards:
        card = item.card
        card_data = {
            'id': card.id,
            'name': card.name,
            'hp': card.hp,
            'type': card.type,
            'rarity': card.rarity,
            'image_url': card.image_url,
            'count': item.count,
            'listed': card.id in listed_cards,
        }

        # Fetch additional details from PokeAPI
        poke_name = card.name.lower().replace(" ", "-")
        poke_url = f"https://pokeapi.co/api/v2/pokemon/{poke_name}"
        species_url = f"https://pokeapi.co/api/v2/pokemon-species/{poke_name}"

        try:
            poke_response = requests.get(poke_url)
            species_response = requests.get(species_url)

            if poke_response.status_code == 200:
                poke_data = poke_response.json()
                card_data.update({
                    'base_experience': poke_data.get('base_experience', 'N/A'),
                    'height': poke_data.get('height', 'N/A'),
                    'weight': poke_data.get('weight', 'N/A'),
                    'abilities': [a['ability']['name'] for a in poke_data.get('abilities', [])],
                })
            else:
                card_data.update({
                    'base_experience': 'N/A',
                    'height': 'N/A',
                    'weight': 'N/A',
                    'abilities': [],
                })

            if species_response.status_code == 200:
                species_data = species_response.json()
                flavor_text_entries = species_data.get('flavor_text_entries', [])
                english_flavor_text = next(
                    (entry['flavor_text'] for entry in flavor_text_entries if entry['language']['name'] == 'en'),
                    "No description available."
                )
                card_data['flavor_text'] = english_flavor_text
            else:
                card_data['flavor_text'] = "No description available."

        except Exception as e:
            card_data.update({
                'base_experience': 'N/A',
                'height': 'N/A',
                'weight': 'N/A',
                'abilities': [],
                'flavor_text': "No description available."
            })

        detailed_cards.append(card_data)

    return render(request, 'collection.html', {'cards': detailed_cards})


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
    my_cards = UserCollection.objects.filter(user=request.user, count__gt=0).values_list('card', flat=True)
    their_cards = UserCollection.objects.filter(user=other_user, count__gt=0).values_list('card', flat=True)

    if request.method == 'POST':
        form = TradeRequestForm(request.POST)
        form.fields['offered_cards'].queryset = PokemonCard.objects.filter(id__in=my_cards)
        form.fields['requested_cards'].queryset = PokemonCard.objects.filter(id__in=their_cards)

        if form.is_valid():
            offered_cards = form.cleaned_data['offered_cards']
            requested_cards = form.cleaned_data['requested_cards']

            trade = TradeRequest.objects.create(
                from_user=request.user,
                to_user=other_user,
            )

            trade.offered_cards.set(offered_cards)
            trade.requested_cards.set(requested_cards)

            return redirect('trade_requests')
    else:
        form = TradeRequestForm()
        form.fields['offered_cards'].queryset = PokemonCard.objects.filter(id__in=my_cards)
        form.fields['requested_cards'].queryset = PokemonCard.objects.filter(id__in=their_cards)

    return render(request, 'send_trade.html', {
        'form': form,
        'other_user': other_user
    })


@login_required
def trade_requests(request):
    incoming = TradeRequest.objects.filter(to_user=request.user).prefetch_related('offered_cards', 'requested_cards')
    outgoing = TradeRequest.objects.filter(from_user=request.user).prefetch_related('offered_cards', 'requested_cards')

    return render(request, 'trade_requests.html', {
        'incoming_requests': incoming,
        'outgoing_requests': outgoing
    })


@login_required
@login_required
def accept_trade(request, trade_id):
    trade = get_object_or_404(TradeRequest, id=trade_id)

    if trade.to_user != request.user or trade.status != 'pending':
        return redirect('trade_requests')

    # Step 1: Transfer offered cards from sender to receiver
    for card in trade.offered_cards.all():
        try:
            sender_card = UserCollection.objects.get(user=trade.from_user, card=card)
            if sender_card.count > 0:
                sender_card.count -= 1
                sender_card.save()
            else:
                messages.error(request, "Sender doesn't have the offered card anymore.")
                return redirect('trade_requests')
        except UserCollection.DoesNotExist:
            messages.error(request, "Sender doesn't have the offered card.")
            return redirect('trade_requests')

        # Add to receiver
        receiver_card, created = UserCollection.objects.get_or_create(user=trade.to_user, card=card)
        receiver_card.count = 1 if created else receiver_card.count + 1
        receiver_card.save()

    # Step 2: Transfer requested cards from receiver to sender
    for card in trade.requested_cards.all():
        try:
            receiver_card = UserCollection.objects.get(user=trade.to_user, card=card)
            if receiver_card.count > 0:
                receiver_card.count -= 1
                receiver_card.save()
            else:
                messages.error(request, "You don't have the requested card anymore.")
                return redirect('trade_requests')
        except UserCollection.DoesNotExist:
            messages.error(request, "You don't have the requested card.")
            return redirect('trade_requests')

        # Add to sender
        sender_card, created = UserCollection.objects.get_or_create(user=trade.from_user, card=card)
        sender_card.count = 1 if created else sender_card.count + 1
        sender_card.save()

    # Step 3: Mark trade as accepted
    trade.status = 'accepted'
    trade.save()

    # Step 4: Award achievements to both users
    for user in [trade.from_user, trade.to_user]:
        trade_count = TradeRequest.objects.filter(
            Q(from_user=user) | Q(to_user=user),
            status='accepted'
        ).count()

        earned = UserAchievement.objects.filter(user=user).values_list('achievement_id', flat=True)
        eligible = Achievement.objects.filter(required_trades__lte=trade_count).exclude(id__in=earned)

        for achievement in eligible:
            UserAchievement.objects.create(user=user, achievement=achievement)

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

