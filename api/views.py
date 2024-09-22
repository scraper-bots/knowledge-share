# api/views.py
from rest_framework import viewsets
from .models import Workout
from .serializers import WorkoutSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework import generics
from .serializers import UserRegistrationSerializer
from rest_framework.permissions import AllowAny
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from django.http import HttpResponse

def home(request):
    return HttpResponse("Welcome to the Fitness Backend API!")

class RegisterView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

class LoginView(ObtainAuthToken):
    permission_classes = [AllowAny]
  
    def post(self, request, *args, **kwargs):
        response = super(LoginView, self).post(request, *args, **kwargs)
        token = response.data['token']
        return Response({'token': token})



class WorkoutViewSet(viewsets.ModelViewSet):
    serializer_class = WorkoutSerializer
    permission_classes = [IsAuthenticated]
  
    def get_queryset(self):
        return self.request.user.workouts.all()
  
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
