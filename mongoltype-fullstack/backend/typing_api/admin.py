from django.contrib import admin
from .models import Word,TestSession,Result
@admin.register(Word)
class WordAdmin(admin.ModelAdmin):
    list_display=('text','cyrillic','language','verified','source')
    list_filter=('language','verified')
    search_fields=('text','cyrillic')
@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display=('id','language','mode','amount','category','demo','created_at')
    list_filter=('language','mode','category','demo')
    readonly_fields=('created_at',)
@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display=('id','session','wpm','accuracy','errors','created_at')
    readonly_fields=('created_at',)
