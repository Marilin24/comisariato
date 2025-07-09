from django.urls import path
from . import views

urlpatterns = [
    path('', views.plantilla, name='plantilla'),
    path('api/chatbot/', views.chatbot_view, name='chatbot_view'),
]
