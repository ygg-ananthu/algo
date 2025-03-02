from django.urls import path
from .views import signup_view, login_view, balance_view, logout_view, add_balance, add_balance_page
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('signup/', signup_view, name='signup'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('balance/', balance_view, name='balance_page'),
    path('add_balance/', add_balance, name='add_balance'),
    path('add_balance_page/', add_balance_page, name='add_balance_page'),
]
