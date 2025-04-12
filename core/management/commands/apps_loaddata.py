import os

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings

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
            "core": [
                "Groups",
            ]
        }
        
        commands_skip_testing = [
            "core/Groups",
        ]
        
        for command_category, commands in commands_data.items():
            for command in commands:
                
                full_command = f"{command_category}/{command}"
                
                # Skip testing for specific commands
                if settings.IS_TESTING and full_command in commands_skip_testing:
                    print(f"Skipping {full_command} because testing mode is enabled.")
                    continue
                
                try:
                    call_command("loaddata", full_command)
                except Exception as e:
                    print(f"Error in {BASE_FILE}: {e}")
                    continue