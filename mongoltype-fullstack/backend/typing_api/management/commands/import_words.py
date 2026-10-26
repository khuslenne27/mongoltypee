import csv
import unicodedata
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from typing_api.models import Word
class Command(BaseCommand):
    help = 'Import UTF-8 CSV: text,cyrillic,verified,source. Do not remove FVS/MVS/NNBSP.'
    def add_arguments(self,parser):
        parser.add_argument('file')
        parser.add_argument('--language',choices=['en','mn-Cyrl','mn-Mong'],default='mn-Mong')
    def handle(self,*args,**options):
        count=0
        with open(options['file'],encoding='utf-8-sig',newline='') as f, transaction.atomic():
            reader=csv.DictReader(f)
            if not reader.fieldnames or 'text' not in reader.fieldnames: raise CommandError('CSV requires text column')
            for n,row in enumerate(reader,2):
                text=unicodedata.normalize('NFC',row['text'].strip(' \r\n\t'))
                if not text: continue
                if len(text)>200 or any(0xE000<=ord(c)<=0xF8FF for c in text): raise CommandError(f'Line {n}: invalid length or legacy private-use encoding')
                if options['language']=='mn-Mong' and not any(0x1820<=ord(c)<=0x18AA for c in text): raise CommandError(f'Line {n}: no Mongolian letters')
                Word.objects.update_or_create(language=options['language'],text=text,defaults={'cyrillic':row.get('cyrillic',''),'verified':row.get('verified','').lower() in ['1','true','yes'],'source':row.get('source','')})
                count+=1
        self.stdout.write(self.style.SUCCESS(f'Imported {count} rows'))
