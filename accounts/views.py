from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from .forms import SignupForm
from django.contrib.auth.decorators import login_required


from django.core.cache import cache
from django.contrib import messages

def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():

            user = form.save()
            login(request, user)

            
            url = "https://api.upstox.com/v2/login/authorization/dialog"
            params = {
                "client_id": user.client_id,
                "redirect_uri": "http://127.0.0.1:8000/accounts/balance/",
                "response_type": "code"
            }
            
            return redirect(f"{url}?client_id={params['client_id']}&redirect_uri={params['redirect_uri']}&response_type={params['response_type']}")
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:

            login(request, user)
            url = "https://api.upstox.com/v2/login/authorization/dialog"
            params = {
                "client_id": user.client_id,
                "redirect_uri": "http://127.0.0.1:8000/accounts/balance/",
                "response_type": "code"
            }
            
            return redirect(f"{url}?client_id={params['client_id']}&redirect_uri={params['redirect_uri']}&response_type={params['response_type']}")
   
    return render(request, 'accounts/login.html')

@login_required
def balance_view(request):
    code = request.GET.get('code')
    request.user.code = code
    request.user.save()
    return render(request, 'accounts/balance.html', {'balance': request.user.virtual_balance})

def logout_view(request):
    
    logout(request)
    return redirect('login')

@login_required
def add_balance(request):

    if request.method == 'POST':
        try:
            amount = float(request.POST.get('balance'))
            if amount > 0:
                request.user.update_balance(amount, 'INCREASE')
                messages.success(request, f"${amount} added to your balance.")
            else:
                messages.error(request, "Invalid amount. Enter a positive number.")
                return render(request, 'accounts/add_balance.html')
        except ValueError:
            messages.error(request, "Invalid input. Please enter a valid number.")
            return render(request, 'accounts/add_balance.html')
        
    return render(request, 'accounts/balance.html', {'balance': request.user.virtual_balance})

@login_required
def add_balance_page(request):
    """Renders the page to add balance."""
    return render(request, 'accounts/add_balance.html')