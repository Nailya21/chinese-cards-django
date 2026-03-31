from django.db import models


class Card(models.Model):
    chinese = models.CharField("Китайское слово", max_length=100)
    pinyin = models.CharField("Пиньинь", max_length=100)
    translation = models.CharField("Перевод", max_length=200)
    example = models.TextField("Пример", blank=True)
    topic = models.CharField("Тема", max_length=100, blank=True)
    hsk_level = models.PositiveSmallIntegerField("Уровень HSK", default=1)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)

    def __str__(self):
        return f"{self.chinese} — {self.translation}"