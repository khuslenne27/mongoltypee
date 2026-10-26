from django.core.management.base import BaseCommand
from django.core.management import call_command
class Command(BaseCommand):
    help='Create tables and add development word lists'
    def handle(self,*args,**kwargs):
        call_command('migrate',interactive=False)
        call_command('seed_words')
        self.stdout.write(self.style.SUCCESS('Ready: python manage.py runserver 127.0.0.1:8000'))
