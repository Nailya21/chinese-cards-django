from django.urls import path
from . import views

app_name = "cards"

urlpatterns = [
    path("", views.home, name="home"),
    path("cards/", views.card_list, name="card_list"),
    path("cards/add/", views.card_create, name="card_create"),
    path("cards/<int:card_id>/", views.card_detail, name="card_detail"),
    path("cards/<int:card_id>/edit/", views.card_edit, name="card_edit"),
    path("study/", views.study, name="study"),
]