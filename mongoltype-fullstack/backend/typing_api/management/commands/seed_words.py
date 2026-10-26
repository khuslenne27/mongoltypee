from django.core.management.base import BaseCommand
from typing_api.models import Word
class Command(BaseCommand):
    help = 'Seed basic development words; Mongolian script examples are unverified.'
    def handle(self,*args,**options):
        groups = {
          'en': 'time people world day life hand work place home water school book good new first small think learn write read'.split(),
          'mn-Cyrl': 'монгол хүн өдөр гэр ус ном сургууль ажил цаг амьдрал найз дэлхий хэл бичиг сурах унших бичих сайхан шинэ хот'.split(),
          'mn-Mong': ['ᠮᠣᠩᠭᠣᠯ','ᠪᠢᠴᠢᠭ','ᠨᠣᠮ','ᠤᠰᠤ','ᠮᠣᠷᠢ','ᠭᠡᠷ','ᠬᠦᠮᠦᠨ','ᠰᠠᠶᠢᠨ','ᠠᠪᠤ','ᠡᠵᠢ']
        }
        for lang,words in groups.items():
            for text in words:
                Word.objects.get_or_create(language=lang,text=text,defaults={'verified':lang!='mn-Mong','source':'Development examples; review Mongolian script before production'})
        self.stdout.write(self.style.SUCCESS('Development word list ready'))
