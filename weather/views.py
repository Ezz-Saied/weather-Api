# weather/views.py
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import CityForm, UserRegisterForm
from .models import City, UserProfile, FavoriteCity, SearchHistory

def signup_view(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'weather/signup.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {username}!')
            return redirect('index')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'weather/login.html')

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required(login_url='login')
def index(request):
    # Replace with your actual API key
    api_key = "YOUR_API_KEY"
    url = f'https://api.openweathermap.org/data/2.5/weather?q={{city}}&units=metric&appid=56f2ede7956e1f8f48ee5049620416a8'
    
    weather_data = None
    error_message = None
    
    # Get user's favorite cities
    favorite_cities = FavoriteCity.objects.filter(user=request.user).select_related('city')
    
    if request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            city_name = form.cleaned_data['name']
            try:
                response = requests.get(url.format(city=city_name)).json()
                
                if response.get('cod') == 200:
                    # Save search history
                    SearchHistory.objects.create(
                        user=request.user,
                        city_name=city_name
                    )
                    
                    # Check if city exists in database, if not create it
                    city, created = City.objects.get_or_create(
                        name=city_name,
                        defaults={'country_code': response['sys']['country']}
                    )
                    
                    # If it exists but country code is blank, update it
                    if not created and not city.country_code:
                        city.country_code = response['sys']['country']
                        city.save()
                    
                    weather_data = {
                        'city': city_name,
                        'temperature': response['main']['temp'],
                        'feels_like': response['main']['feels_like'],
                        'description': response['weather'][0]['description'],
                        'icon': response['weather'][0]['icon'],
                        'humidity': response['main']['humidity'],
                        'pressure': response['main']['pressure'],
                        'wind_speed': response['wind']['speed'],
                        'country': response['sys']['country'],
                        'city_id': city.id,
                        'is_favorite': FavoriteCity.objects.filter(user=request.user, city=city).exists()
                    }
                else:
                    error_message = f"City '{city_name}' not found!"
            except Exception as e:
                error_message = f"An error occurred: {str(e)}"
    else:
        form = CityForm()
    
    # Get recent searches
    recent_searches = SearchHistory.objects.filter(user=request.user).order_by('-search_date')[:5]
    
    context = {
        'weather_data': weather_data,
        'form': form,
        'error_message': error_message,
        'favorite_cities': favorite_cities,
        'recent_searches': recent_searches,
    }
    
    return render(request, 'weather/weather.html', context)

@login_required
def add_favorite(request, city_id):
    city = get_object_or_404(City, id=city_id)
    favorite, created = FavoriteCity.objects.get_or_create(user=request.user, city=city)
    
    if created:
        messages.success(request, f"{city.name} added to favorites!")
    else:
        messages.info(request, f"{city.name} is already in your favorites.")
    
    return redirect('index')

@login_required
def remove_favorite(request, city_id):
    city = get_object_or_404(City, id=city_id)
    favorite = FavoriteCity.objects.filter(user=request.user, city=city)
    
    if favorite.exists():
        favorite.delete()
        messages.success(request, f"{city.name} removed from favorites.")
    else:
        messages.info(request, f"{city.name} is not in your favorites.")
    
    return redirect('index')

@login_required
def user_profile(request):
    # Get or create user profile
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get user's favorite cities and search history
    favorites = FavoriteCity.objects.filter(user=request.user).select_related('city')
    searches = SearchHistory.objects.filter(user=request.user).order_by('-search_date')[:10]
    
    context = {
        'profile': profile,
        'favorites': favorites,
        'searches': searches,
    }
    
    return render(request, 'weather/profile.html', context)
