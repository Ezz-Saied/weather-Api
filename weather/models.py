# weather/models.py
from django.db import models
from django.contrib.auth.models import User

class City(models.Model):
    name = models.CharField(max_length=100)
    country_code = models.CharField(max_length=2, blank=True)
    
    class Meta:
        verbose_name_plural = 'cities'
    
    def __str__(self):
        return self.name

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    default_temperature_unit = models.CharField(
        max_length=1, 
        choices=[('C', 'Celsius'), ('F', 'Fahrenheit')],
        default='C'
    )
    
    def __str__(self):
        return f"{self.user.username}'s profile"

class FavoriteCity(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city = models.ForeignKey(City, on_delete=models.CASCADE)
    date_added = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'favorite cities'
        unique_together = ('user', 'city')
    
    def __str__(self):
        return f"{self.user.username} - {self.city.name}"

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    city_name = models.CharField(max_length=100)
    search_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = 'search histories'
        ordering = ['-search_date']
    
    def __str__(self):
        return f"{self.user.username} searched for {self.city_name}"
