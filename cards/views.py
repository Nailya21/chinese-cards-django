from django.shortcuts import get_object_or_404, redirect, render

from .forms import CardForm
from .models import Card


def home(request):
    return render(request, "cards/home.html")


def card_list(request):
    cards = Card.objects.all().order_by("-created_at")
    context = {"cards": cards}
    return render(request, "cards/card_list.html", context)


def card_detail(request, card_id):
    card = get_object_or_404(Card, id=card_id)
    context = {"card": card}
    return render(request, "cards/card_detail.html", context)


def card_create(request):
    if request.method == "POST":
        form = CardForm(request.POST)
        if form.is_valid():
            card = form.save()
            return redirect("cards:card_detail", card_id=card.id)
    else:
        form = CardForm()

    context = {
        "form": form,
        "page_title": "Добавить карточку",
        "button_text": "Сохранить",
    }
    return render(request, "cards/card_form.html", context)


def card_edit(request, card_id):
    card = get_object_or_404(Card, id=card_id)

    if request.method == "POST":
        form = CardForm(request.POST, instance=card)
        if form.is_valid():
            card = form.save()
            return redirect("cards:card_detail", card_id=card.id)
    else:
        form = CardForm(instance=card)

    context = {
        "form": form,
        "page_title": "Редактировать карточку",
        "button_text": "Обновить",
        "card": card,
    }
    return render(request, "cards/card_form.html", context)


def study(request):
    card = Card.objects.order_by("?").first()
    context = {"card": card}
    return render(request, "cards/study.html", context)