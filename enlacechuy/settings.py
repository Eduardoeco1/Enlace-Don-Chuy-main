from pathlib import Path
import os
import dj_database_url
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)&-pdp@)9&rqy1&&c6m4r&bo*g071p=-lhj1%t(m4xv30!^e)8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Tus apps:
    'Sucursales',
    'InicioSeccion', 
    'PanelControl',
    'Reportes', 
    'EntradaMercancia',
    'CierreCaja',
    'Inventario',
    'Perfil',
    'Personal',
    'Ventas',
    'Notificaciones',

]

AUTH_USER_MODEL = 'Sucursales.Usuario'

LOGIN_URL          = '/'
LOGIN_REDIRECT_URL = '/panel-control/'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'enlacechuy.middleware.SucursalActualMiddleware',
]

ROOT_URLCONF = 'enlacechuy.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'enlacechuy' / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'enlacechuy.context_processors.negocio_context',
                
                # 👇 AQUÍ ESTÁ EL CAMBIO: El inyector nuevo de las sucursales 👇
                'Sucursales.context_processors.sucursal_contexto',
                
                # 🌟 CONTEXT PROCESSOR UNIFICADO: Roles, Notificaciones y Sucursal Global
                'Perfil.context_processors.roles_y_notificaciones_globales',

            ],
        },
    },
]

WSGI_APPLICATION = 'enlacechuy.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.parse(
        'postgresql://enlaceadmin:6tMpqTPZ36FmiggYSCdHYmo4ZkVAUifn@dpg-d8adhmkm0tmc73a0j65g-a.oregon-postgres.render.com/enlacechuy'
    )
}

# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
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
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'es-mx'

TIME_ZONE = 'America/Mexico_City'

USE_I18N = True

USE_TZ = False


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]





STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ── CONFIGURACIÓN: ARCHIVOS MEDIA ───────────────────────────
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ── NUEVA CONFIGURACIÓN: SERVICIO DE EMAIL (GMAIL) ───────────
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'tu-email@gmail.com'  # Cambiar por tu correo real de Gmail
EMAIL_HOST_PASSWORD = 'tu-app-password'  # Cambiar por tu contraseña de aplicación de Google
DEFAULT_FROM_EMAIL = 'Enlace Don Chuy <noreply@enlacedonchuy.com>'




#DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.onrender.com',
]




