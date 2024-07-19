import os
from dotenv import load_dotenv

# Env variables
load_dotenv()
LANDING_HOST = os.getenv('LANDING_HOST')


def load_env_variables(request):
    return {
        'LANDING_HOST': LANDING_HOST
    }