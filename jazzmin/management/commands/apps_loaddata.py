import os

from django.core.management.base import BaseCommand
from django.core.management import call_command

BASE_FILE = os.path.basename(__file__)


class Command(BaseCommand):
    help = 'Load data for all apps'
    
    def handle(self, *args, **kwargs):
        commands_data = {
            "landing": [
                "Category",
            ],
            "store": [
                "StoreStatus",
                "Color",
                "ColorsNum",
                "Addon",
                "SaleStatus",
                "Set",
                "PromoCodeType",
            ],
        }
        
        for command_category, commands in commands_data.items():
            for command in commands:
                try:
                    full_command = f"{command_category}/{command}"
                    call_command("loaddata", full_command)
                except Exception as e:
                    print(f"Error in {BASE_FILE}: {e}")
                    continue