from django import forms
from .models import UserProfile, TradeRequest, PokemonCard
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class TradeRequestForm(forms.ModelForm):
    offered_cards = forms.ModelMultipleChoiceField(
        queryset=PokemonCard.objects.none(),
        widget=forms.SelectMultiple(attrs={'size': 6})
    )
    requested_cards = forms.ModelMultipleChoiceField(
        queryset=PokemonCard.objects.none(),
        widget=forms.SelectMultiple(attrs={'size': 6})
    )

    class Meta:
        model = TradeRequest
        fields = ['offered_cards', 'requested_cards']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        to_user = kwargs.pop('to_user', None)
        super().__init__(*args, **kwargs)

        if user:
            self.fields['offered_cards'].queryset = PokemonCard.objects.filter(usercollection__user=user)

        if to_user:
            self.fields['requested_cards'].queryset = PokemonCard.objects.filter(usercollection__user=to_user)

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['display_name', 'profile_pic']

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2"]
        help_texts = {
            'username': None,
            'password1': "Must be at least 8 characters and not too common.",
            'password2': None,
        }

    def __init__(self, *args, **kwargs):
        super(CustomUserCreationForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = ""
        self.fields['password1'].help_text = "Must be at least 8 characters, not too common."
        self.fields['password2'].help_text = ""

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email




