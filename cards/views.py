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


def _extract_prompt_settings(request):
    show_chinese = bool(request.POST.get("show_chinese_prompt"))
    show_pinyin = bool(request.POST.get("show_pinyin_prompt"))
    show_translation = bool(request.POST.get("show_translation_prompt"))

    if not (show_chinese or show_pinyin or show_translation):
        show_chinese = True

    return {
        "show_chinese": show_chinese,
        "show_pinyin": show_pinyin,
        "show_translation": show_translation,
    }


def _get_prompt_settings_from_session(request):
    return {
        "show_chinese": request.session.get("study_prompt_show_chinese", True),
        "show_pinyin": request.session.get("study_prompt_show_pinyin", False),
        "show_translation": request.session.get("study_prompt_show_translation", False),
    }


def _build_study_queue(topic="", hsk_level="", card_ids=None):
    if card_ids is None:
        queryset = Card.objects.all()

        if topic:
            queryset = queryset.filter(topic=topic)

        if hsk_level:
            queryset = queryset.filter(hsk_level=hsk_level)

        card_ids = list(queryset.values_list("id", flat=True))

    queue = list(card_ids)
    random.shuffle(queue)
    return queue


def _start_study_session(request, topic="", hsk_level="", card_ids=None, prompt_settings=None):
    if prompt_settings is None:
        prompt_settings = _get_prompt_settings_from_session(request)

    queue = _build_study_queue(topic=topic, hsk_level=hsk_level, card_ids=card_ids)

    request.session["study_topic"] = topic
    request.session["study_hsk_level"] = hsk_level
    request.session["study_queue"] = queue
    request.session["study_wrong_ids"] = []
    request.session["study_answered"] = 0
    request.session["study_correct"] = 0
    request.session["study_total_cards"] = len(queue)
    request.session["study_started"] = True
    request.session["study_started_at"] = int(time.time())
    request.session["study_finished_at"] = None
    request.session["study_prompt_show_chinese"] = prompt_settings["show_chinese"]
    request.session["study_prompt_show_pinyin"] = prompt_settings["show_pinyin"]
    request.session["study_prompt_show_translation"] = prompt_settings["show_translation"]


def study(request):
    if request.method == "POST":
        action = request.POST.get("action", "")

        if action == "start_topic":
            topic = request.POST.get("topic", "").strip()
            hsk_level = request.POST.get("hsk_level", "").strip()
            prompt_settings = _extract_prompt_settings(request)
            _start_study_session(
                request,
                topic=topic,
                hsk_level=hsk_level,
                prompt_settings=prompt_settings,
            )
            return redirect("cards:study")

        if action == "restart_topic":
            saved_topic = request.session.get("study_topic", "")
            saved_hsk_level = request.session.get("study_hsk_level", "")
            prompt_settings = _get_prompt_settings_from_session(request)
            _start_study_session(
                request,
                topic=saved_topic,
                hsk_level=saved_hsk_level,
                prompt_settings=prompt_settings,
            )
            return redirect("cards:study")

        if action == "retry_wrong":
            saved_topic = request.session.get("study_topic", "")
            saved_hsk_level = request.session.get("study_hsk_level", "")
            wrong_ids = request.session.get("study_wrong_ids", [])
            prompt_settings = _get_prompt_settings_from_session(request)
            _start_study_session(
                request,
                topic=saved_topic,
                hsk_level=saved_hsk_level,
                card_ids=wrong_ids,
                prompt_settings=prompt_settings,
            )
            return redirect("cards:study")

        if action in {"mark_right", "mark_wrong"}:
            queue = request.session.get("study_queue", [])

            if queue:
                current_card_id = int(request.POST.get("card_id", "0"))
                first_card_id = queue[0]

                if current_card_id == first_card_id:
                    queue.pop(0)
                elif current_card_id in queue:
                    queue.remove(current_card_id)

                request.session["study_queue"] = queue
                request.session["study_answered"] = (
                    request.session.get("study_answered", 0) + 1
                )

                if action == "mark_right":
                    request.session["study_correct"] = (
                        request.session.get("study_correct", 0) + 1
                    )
                else:
                    wrong_ids = request.session.get("study_wrong_ids", [])
                    if current_card_id not in wrong_ids:
                        wrong_ids.append(current_card_id)
                    request.session["study_wrong_ids"] = wrong_ids

                if not queue:
                    request.session["study_finished_at"] = int(time.time())

            return redirect("cards:study")

    topics = (
        Card.objects.exclude(topic="")
        .values_list("topic", flat=True)
        .distinct()
        .order_by("topic")
    )

    hsk_levels = (
        Card.objects.values_list("hsk_level", flat=True)
        .distinct()
        .order_by("hsk_level")
    )

    selected_topic = request.session.get("study_topic", "")
    selected_hsk_level = request.session.get("study_hsk_level", "")
    prompt_settings = _get_prompt_settings_from_session(request)

    queue = request.session.get("study_queue", [])
    answered = request.session.get("study_answered", 0)
    correct = request.session.get("study_correct", 0)
    wrong_ids = request.session.get("study_wrong_ids", [])
    total_cards = request.session.get("study_total_cards", 0)
    started = request.session.get("study_started", False)

    current_card = None
    if queue:
        current_card = Card.objects.filter(id=queue[0]).first()

    finished = started and total_cards > 0 and answered == total_cards and not queue
    no_cards_in_topic = started and total_cards == 0 and not queue

    wrong_count = answered - correct
    percent = round((correct / answered) * 100, 1) if answered else 0
    remaining = len(queue)
    progress_percent = round((answered / total_cards) * 100, 1) if total_cards else 0
    current_number = answered + 1 if current_card else total_cards

    started_at = request.session.get("study_started_at")
    finished_at = request.session.get("study_finished_at")

    if started_at:
        end_time = finished_at if finished_at else int(time.time())
        duration_seconds = max(0, int(end_time - started_at))
    else:
        duration_seconds = 0

    minutes = duration_seconds // 60
    seconds = duration_seconds % 60
    duration_text = f"{minutes}:{seconds:02d}"

    context = {
        "topics": topics,
        "hsk_levels": hsk_levels,
        "selected_topic": selected_topic,
        "selected_hsk_level": selected_hsk_level,
        "started": started,
        "current_card": current_card,
        "finished": finished,
        "no_cards_in_topic": no_cards_in_topic,
        "answered": answered,
        "correct": correct,
        "wrong_count": wrong_count,
        "percent": percent,
        "remaining": remaining,
        "total_cards": total_cards,
        "progress_percent": progress_percent,
        "current_number": current_number,
        "duration_text": duration_text,
        "started_at_ts": started_at or "",
        "finished_at_ts": finished_at or "",
        "can_retry_wrong": len(wrong_ids) > 0,
        "prompt_show_chinese": prompt_settings["show_chinese"],
        "prompt_show_pinyin": prompt_settings["show_pinyin"],
        "prompt_show_translation": prompt_settings["show_translation"],
    }
    return render(request, "cards/study.html", context)