import random
import time

from django.shortcuts import get_object_or_404, redirect, render

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


def _build_study_queue(topic="", card_ids=None):
    if card_ids is None:
        queryset = Card.objects.all()
        if topic:
            queryset = queryset.filter(topic=topic)
        card_ids = list(queryset.values_list("id", flat=True))

    queue = list(card_ids)
    random.shuffle(queue)
    return queue


def _start_study_session(request, topic="", card_ids=None):
    queue = _build_study_queue(topic=topic, card_ids=card_ids)

    request.session["study_topic"] = topic
    request.session["study_queue"] = queue
    request.session["study_wrong_ids"] = []
    request.session["study_answered"] = 0
    request.session["study_correct"] = 0
    request.session["study_started"] = True
    request.session["study_started_at"] = time.time()
    request.session["study_finished_at"] = None


def study(request):
    if request.method == "POST":
        action = request.POST.get("action", "")
        topic = request.POST.get("topic", "").strip()

        if action == "start_topic":
            _start_study_session(request, topic=topic)
            return redirect("cards:study")

        if action == "restart_topic":
            saved_topic = request.session.get("study_topic", "")
            _start_study_session(request, topic=saved_topic)
            return redirect("cards:study")

        if action == "retry_wrong":
            saved_topic = request.session.get("study_topic", "")
            wrong_ids = request.session.get("study_wrong_ids", [])
            _start_study_session(request, topic=saved_topic, card_ids=wrong_ids)
            return redirect("cards:study")

        if action in {"mark_right", "mark_wrong"}:
            queue = request.session.get("study_queue", [])

            if queue:
                current_card_id = int(request.POST.get("card_id", "0"))
                expected_card_id = queue[0]

                if current_card_id == expected_card_id:
                    queue.pop(0)
                elif current_card_id in queue:
                    queue.remove(current_card_id)

                request.session["study_queue"] = queue
                request.session["study_answered"] = request.session.get("study_answered", 0) + 1

                if action == "mark_right":
                    request.session["study_correct"] = request.session.get("study_correct", 0) + 1
                else:
                    wrong_ids = request.session.get("study_wrong_ids", [])
                    if current_card_id not in wrong_ids:
                        wrong_ids.append(current_card_id)
                    request.session["study_wrong_ids"] = wrong_ids

                if not queue:
                    request.session["study_finished_at"] = time.time()

            return redirect("cards:study")

    topics = (
        Card.objects.exclude(topic="")
        .values_list("topic", flat=True)
        .distinct()
        .order_by("topic")
    )

    selected_topic = request.session.get("study_topic", "")
    queue = request.session.get("study_queue", [])
    answered = request.session.get("study_answered", 0)
    correct = request.session.get("study_correct", 0)
    wrong_ids = request.session.get("study_wrong_ids", [])
    started = request.session.get("study_started", False)

    current_card = None
    if queue:
        current_card = Card.objects.filter(id=queue[0]).first()

    finished = started and answered > 0 and not queue
    no_cards_in_topic = started and answered == 0 and not queue

    percent = round((correct / answered) * 100, 1) if answered else 0
    wrong_count = answered - correct
    remaining = len(queue)

    started_at = request.session.get("study_started_at")
    finished_at = request.session.get("study_finished_at")

    if started_at:
        end_time = finished_at if finished_at else time.time()
        duration_seconds = int(end_time - started_at)
    else:
        duration_seconds = 0

    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    duration_text = f"{minutes}:{seconds:02d}"

    context = {
        "topics": topics,
        "selected_topic": selected_topic,
        "started": started,
        "current_card": current_card,
        "finished": finished,
        "no_cards_in_topic": no_cards_in_topic,
        "answered": answered,
        "correct": correct,
        "wrong_count": wrong_count,
        "percent": percent,
        "remaining": remaining,
        "duration_text": duration_text,
        "can_retry_wrong": len(wrong_ids) > 0,
    }
    return render(request, "cards/study.html", context)