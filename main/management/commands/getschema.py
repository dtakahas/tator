import json

from django.core.management.base import BaseCommand

from main.schema import CustomGenerator

class Command(BaseCommand):
    def handle(self, **options):
        generator = CustomGenerator(title='Tator REST API')
        spec = generator.get_schema()
        print(json.dumps(spec, indent=4))