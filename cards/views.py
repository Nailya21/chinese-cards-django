from urllib.parse import urlencode

from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import BulkCardFormSet, CardForm
from .models import Card


def home(request):
    return render(request, "cards/home.html")


def card_list(request):
    cards = Card.objects.all().order_by("-created_at")

    topic = request.GET.get("topic", "").strip()
    hsk_level = request.GET.get("hsk_level", "").strip()

    if topic:
        cards = cards.filter(topic__icontains=topic)

    if hsk_level:
        cards = cards.filter(hsk_level=hsk_level)

    context = {
        "cards": cards,
        "topic": topic,
        "hsk_level": hsk_level,
    }
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


def bulk_card_create(request):
    if request.method == "POST":
        formset = BulkCardFormSet(request.POST, queryset=Card.objects.none())
        if formset.is_valid():
            formset.save()
            return redirect("cards:card_list")
    else:
        formset = BulkCardFormSet(queryset=Card.objects.none())

    context = {
        "formset": formset,
    }
    return render(request, "cards/bulk_card_form.html", context)


def study(request):
    selected_topic = request.GET.get("topic", "").strip()

    if request.method == "POST":
        action = request.POST.get("action", "")
        selected_topic = request.POST.get("topic", "").strip()

        if action == "mark_right":
            request.session["study_total"] = request.session.get("study_total", 0) + 1
            request.session["study_correct"] = request.session.get("study_correct", 0) + 1
        elif action == "mark_wrong":
            request.session["study_total"] = request.session.get("study_total", 0) + 1
        elif action == "reset_stats":
            request.session["study_total"] = 0
            request.session["study_correct"] = 0

        query_string = urlencode({"topic": selected_topic}) if selected_topic else ""
        url = reverse("cards:study")
        if query_string:
            url = f"{url}?{query_string}"
        return redirect(url)

    cards = Card.objects.all()

    if selected_topic:
        cards = cards.filter(topic=selected_topic)

    card = cards.order_by("?").first()

    topics = (
        Card.objects.exclude(topic="")
        .values_list("topic", flat=True)
        .distinct()
        .order_by("topic")
    )

    total = request.session.get("study_total", 0)
    correct = request.session.get("study_correct", 0)
    percent = round((correct / total) * 100, 1) if total else 0

    context = {
        "card": card,
        "topics": topics,
        "selected_topic": selected_topic,
        "total": total,
        "correct": correct,
        "percent": percent,
    }
    return render(request, "cards/study.html", context)