from django import forms

from .models import Card


class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ["chinese", "pinyin", "translation", "example", "topic", "hsk_level"]
        widgets = {
            "chinese": forms.TextInput(attrs={"class": "form-input"}),
            "pinyin": forms.TextInput(attrs={"class": "form-input"}),
            "translation": forms.TextInput(attrs={"class": "form-input"}),
            "example": forms.Textarea(attrs={"class": "form-input", "rows": 4}),
            "topic": forms.TextInput(attrs={"class": "form-input"}),
            "hsk_level": forms.NumberInput(attrs={"class": "form-input", "min": 1, "max": 6}),
        }

    def clean_chinese(self):
        chinese = self.cleaned_data["chinese"].strip()
        if not chinese:
            raise forms.ValidationError("Поле 'Китайское слово' не может быть пустым.")
        return chinese

    def clean_pinyin(self):
        pinyin = self.cleaned_data["pinyin"].strip()
        if not pinyin:
            raise forms.ValidationError("Поле 'Пиньинь' не может быть пустым.")
        return pinyin

    def clean_translation(self):
        translation = self.cleaned_data["translation"].strip()
        if not translation:
            raise forms.ValidationError("Поле 'Перевод' не может быть пустым.")
        return translation

    def clean_hsk_level(self):
        hsk_level = self.cleaned_data["hsk_level"]
        if hsk_level < 1 or hsk_level > 6:
            raise forms.ValidationError("Уровень HSK должен быть от 1 до 6.")
        return hsk_level