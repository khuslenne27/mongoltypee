import uuid
from django.db import models
class Word(models.Model):
    language = models.CharField(max_length=12,choices=[('en','English'),('mn-Cyrl','Кирилл'),('mn-Mong','Монгол бичиг')])
    text = models.CharField(max_length=200)
    cyrillic = models.CharField(max_length=200,blank=True)
    verified = models.BooleanField(default=False)
    source = models.CharField(max_length=500,blank=True)
    class Meta:
        constraints=[models.UniqueConstraint(fields=['language','text'],name='unique_language_word')]
    def __str__(self): return f'{self.language}: {self.text}'
class TestSession(models.Model):
    id = models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    visitor = models.UUIDField(db_index=True)
    language = models.CharField(max_length=12)
    mode = models.CharField(max_length=10,default='time')
    category = models.CharField(max_length=16,default='words')
    amount = models.PositiveIntegerField(default=30)
    duration = models.PositiveIntegerField(default=30)
    text = models.TextField()
    demo = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True,blank=True)
class Result(models.Model):
    session = models.OneToOneField(TestSession,on_delete=models.CASCADE)
    typed_text = models.TextField()
    elapsed_ms = models.PositiveIntegerField()
    wpm = models.FloatField()
    accuracy = models.FloatField()
    errors = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
