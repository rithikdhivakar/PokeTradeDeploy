from django.urls import path
from . import views
from django.contrib.auth.views import LoginView
from django.contrib.auth.views import LogoutView
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('collection/', views.my_collection, name='my_collection'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:user_id>/', views.user_collection, name='user_collection'),
    path('trade/send/<int:user_id>/', views.send_trade_request, name='send_trade'),
    path('trade/requests/', views.trade_requests, name='trade_requests'),
    path('trade/accept/<int:trade_id>/', views.accept_trade, name='accept_trade'),
    path('trade/reject/<int:trade_id>/', views.reject_trade, name='reject_trade'),
    # path('', views.home_redirect),  # default homepage
    path('', views.homepage, name='home'),
    path('about/', views.about, name='about'),
    path('sell/<int:card_id>/', views.list_for_sale, name='list_for_sale'),
    path('card/<int:card_id>/details/', views.card_details, name='card_details'),
    path('buy/<int:listing_id>/', views.buy_card, name='buy_card'),
    path('login/', LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('achievements/', views.my_achievements, name='my_achievements'),
    path('marketplace/', views.marketplace, name='marketplace'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
]

