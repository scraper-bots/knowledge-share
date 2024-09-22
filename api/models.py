# api/models.py
from django.db import models
from django.contrib.auth.models import User

class Workout(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workouts')
    date = models.DateField()
    duration = models.DurationField()
    calories_burned = models.PositiveIntegerField()
  
    def __str__(self):
        return f"{self.user.username} - {self.date}"
