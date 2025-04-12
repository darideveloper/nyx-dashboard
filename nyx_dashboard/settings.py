import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Setup .env file
load_dotenv()
ENV = os.getenv('ENV')
env_path = os.path.join(BASE_DIR, f'.env.{ENV}')
load_dotenv(env_path)
print(f'\nEnvironment: {ENV}')

# Env variables
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'False') == 'True'
HOST = os.environ.get("HOST")
STORAGE_AWS = os.environ.get("STORAGE_AWS") == "True"
LANDING_HOST = os.getenv('LANDING_HOST')
TEST_HEADLESS = os.getenv('TEST_HEADLESS') == 'True'
STRIPE_API_HOST = os.getenv('STRIPE_API_HOST')
STRIPE_API_USER = os.getenv('STRIPE_API_USER')
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL')
PAYPAL_CLIENT_ID = os.getenv('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')
PAYPAL_API_BASE = os.getenv('PAYPAL_API_BASE')
PAYPAL_SANDBOX_USER = os.getenv('PAYPAL_SANDBOX_USER')
PAYPAL_SANDBOX_PASSWORD = os.getenv('PAYPAL_SANDBOX_PASSWORD')
AFFILIATES_DISCOUNT = float(os.getenv('AFFILIATES_DISCOUNT'))
AFFILIATES_COMMISSION = float(os.getenv('AFFILIATES_COMMISSION'))


print(f"DEBUG: {DEBUG}")
print(f"HOST: {HOST}")
print(f"STORAGE_AWS: {STORAGE_AWS}\n")

ALLOWED_HOSTS = ["*"]

# Application definition
INSTALLED_APPS = [
    # Local apps
    'jazzmin',
    'landing',
    'user',
    'store',
    'affiliates',
    'core',
    
    # Modules
    'corsheaders',
    
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'whitenoise.runserver_nostatic',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'user.middlewere.AdminCookieMiddleware',
]

ROOT_URLCONF = 'nyx_dashboard.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'store.context_processors.load_env_variables'
            ],
        },
    },
]

WSGI_APPLICATION = 'nyx_dashboard.wsgi.application'


# Database

IS_TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'

if IS_TESTING:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'testing.sqlite3'),
        }
    }
else:
    
    options = {}
    if os.environ.get("DB_ENGINE") == "django.db.backends.mysql":
        options = {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        }
    
    DATABASES = {
        'default': {
            'ENGINE': os.environ.get("DB_ENGINE"),
            'NAME': os.environ.get("DB_NAME"),
            'USER': os.environ.get("DB_USER"),
            'PASSWORD': os.environ.get("DB_PASSWORD"),
            'HOST': os.environ.get("DB_HOST"),
            'PORT': os.environ.get("DB_PORT"),
            'OPTIONS': options,
        }
    }

# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Madrid'

USE_I18N = True

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'


JAZZMIN_SETTINGS = {
    # Yext
    "site_title": "NYX Dashboard",
    "site_header": "Admin",
    "site_brand": "NYX Dashboard",
    "welcome_sign": "Welcome to NYX Dashboard",
    "copyright": "",

    # Media
    "site_logo": "landing/imgs/logo.png",
    "login_logo": "landing/imgs/logo.png",
    "login_logo_dark": "landing/imgs/logo.png",
    "site_logo_classes": "img-circle",
    "site_icon": "landing/imgs/favicon.ico",
    
    # Search model in header
    "search_model": [],

    # Field name on user model that contains avatar
    # ImageField/URLField/Charfield or a callable that receives the user
    "user_avatar": None,

    ############
    # Top Menu #
    ############

    # Links to put along the top menu
    "topmenu_links": [
        {"name": "Home", "url": LANDING_HOST},
    ],

    #############
    # User Menu #
    #############

    # Additional links to include in the user menu on the top right
    # ("app" url type is not allowed)
    "usermenu_links": [
        # {"model": "auth.user"}
    ],

    #############
    # Side Menu #
    #############

    # Whether to display the side menu
    "show_sidebar": True,

    # Whether to aut expand the menu
    "navigation_expanded": True,

    # Hide these apps when generating side menu e.g (auth)
    "hide_apps": [],

    # Hide these models when generating side menu (e.g auth.user)
    "hide_models": [
        "store.Addon",
        "store.Color",
        "store.ColorsNum",
        "store.PromoCodeType",
        "store.SaleStatus",
        "store.Set",
    ],

    # List of apps (and/or models) to base side menu ordering off of
    # (does not need to contain all apps/models)
    "order_with_respect_to": ["landing", "auth"],

    # Custom links to append to app groups, keyed on app name
    "custom_links": {
        # "books": [{
        #     "name": "Make Messages",
        #     "url": "make_messages",
        #     "icon": "fas fa-comments",
        #     "permissions": ["books.view_book"]
        # }]
    },

    # Custom icons for side menu apps/models
    # See https://fontawesome.com/icons?d=gallery&m=free
    # for the full list of 5.13.0 free icon classes
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        
        "store.Sale": "fas fa-shopping-cart",
        "store.StoreStatus": "fas fa-store",
        "store.FutureStock": "fas fa-calendar-alt",
        "store.FutureStockSubscription": "fas fa-bell",
        "store.PromoCode": "fas fa-percent",
        
        "landing.Image": "fas fa-image",
        "landing.Text": "fas fa-font",
        "landing.Video": "fas fa-video",
        
        "affiliates.Affiliate": "fas fa-user-friends",
        "affiliates.Comission": "fas fa-money-bill-wave",
    },
    # Icons that are used when one is not manually specified
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",

    #################
    # Related Modal #
    #################
    # Use modals instead of popups
    "related_modal_active": False,

    #############
    # UI Tweaks #
    #############
    # Relative paths to custom CSS/JS scripts (must be present in static files)
    "custom_css": "jazzmin/css/custom.css",
    "custom_js": "jazzmin/js/custom.js",
    # Whether to link font from fonts.googleapis.com
    # (use custom_css to supply font otherwise)
    "use_google_fonts_cdn": True,
    # Whether to show the UI customizer on the sidebar
    "show_ui_builder": False,

    ###############
    # Change view #
    ###############
    # Render out the change view as a single form, or in tabs, current options are
    # - single
    # - horizontal_tabs (default)
    # - vertical_tabs
    # - collapsible
    # - carousel
    "changeform_format": "horizontal_tabs",
    # override change forms on a per modeladmin basis
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs"
    },
}

# Cors
CORS_ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS').split(',')

CSRF_TRUSTED_ORIGINS = os.getenv('ALLOWED_ORIGINS').split(',')

# Storage settings
if STORAGE_AWS:
    # aws settings
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
    AWS_DEFAULT_ACL = None
    AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}

    # s3 static settings
    STATIC_LOCATION = 'static'
    STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{STATIC_LOCATION}/'
    STATICFILES_STORAGE = 'nyx_dashboard.storage_backends.StaticStorage'
    # s3 public media settings

    PUBLIC_MEDIA_LOCATION = 'media'
    MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{PUBLIC_MEDIA_LOCATION}/'
    DEFAULT_FILE_STORAGE = 'nyx_dashboard.storage_backends.PublicMediaStorage'

    # s3 private media settings
    PRIVATE_MEDIA_LOCATION = 'private'
    PRIVATE_FILE_STORAGE = 'nyx_dashboard.storage_backends.PrivateMediaStorage'
    
    # Disable Django's own staticfiles handling in favour of WhiteNoise
    # for greater consistency between gunicorn and
    STATIC_ROOT = None
    MEDIA_ROOT = None
else:
    # Local development (Windows or local server)
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
    
    # Static files (CSS, JavaScript, Images)
    STATIC_URL = '/static/'
    MEDIA_URL = '/media/'
    
# Email settings
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = os.getenv('EMAIL_PORT')
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL')

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "commands.log",
            "formatter": "verbose",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
    },
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
        "simple": {
            "format": "{levelname} {message}",
            "style": "{",
        },
    },
    "root": {
        "handlers": ["file", "console"],
        "level": "INFO",
    },
}