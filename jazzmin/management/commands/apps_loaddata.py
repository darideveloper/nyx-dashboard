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
            ],
        }
        
        for command_category, commands in commands_data.items():
            for command in commands:
                full_command = f"{command_category}/{command}"
                print(f"\n{BASE_FILE}: Loading data for {full_command}")
                call_command("loaddata", full_command)
                print(f"{BASE_FILE}: Data loaded for {full_command}")