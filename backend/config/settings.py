import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR.parent/".env")

SECRET_KEY = os.environ.get("KOUOJ_SECRET_KEY", "dev-only-secret-key")
DEBUG = os.environ.get("KOUOJ_DEBUG", "1") == "1"
ALLOWED_HOSTS = os.environ.get("KOUOJ_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "apps.accounts",
    "apps.problems",
    "apps.submissions",
    "apps.judge",
    "apps.ai_agent",
    'apps.announcements',
    "apps.home",
    "apps.solutions",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("KOUOJ_DB_NAME", "kouoj"),
        "USER": os.environ.get("KOUOJ_DB_USER", "kouoj_user"),
        "PASSWORD": os.environ.get("KOUOJ_DB_PASSWORD", ""),
        "HOST": os.environ.get("KOUOJ_DB_HOST", "localhost"),
        "PORT": os.environ.get("KOUOJ_DB_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
AUTH_USER_MODEL = "accounts.User"

CORS_ALLOWED_ORIGINS = os.environ.get(
    "KOUOJ_CORS_ALLOWED_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}

JUDGE_PYTHON_COMMAND = os.environ.get("KOUOJ_JUDGE_PYTHON", "python")

# Tavily 网页搜索配置。
# 当前项目只把 Tavily 作为后端 agent 的内部资料检索工具，不直接暴露给前端。
# API Key 必须通过环境变量注入，避免把真实密钥写进代码仓库。
KOUOJ_TAVILY_API_KEY = os.environ.get("KOUOJ_TAVILY_API_KEY", "")

# Tavily 单次搜索结果数量。默认 5 条，工具层会再次限制到 1~20，避免环境变量写错。
KOUOJ_TAVILY_MAX_RESULTS = os.environ.get("KOUOJ_TAVILY_MAX_RESULTS", "5")

# Tavily 搜索深度。默认 basic，成本低且足够用于 v1 的外部题解资料检索。
KOUOJ_TAVILY_SEARCH_DEPTH = os.environ.get("KOUOJ_TAVILY_SEARCH_DEPTH", "basic")

# AI 模型配置。
# 这里先按 OpenAI-compatible 接口预留配置：很多模型服务都支持 base_url + api_key + model
# 这种调用方式。后续真正把 LangGraph 的 render/decision 节点接入 LLM 时，统一从这里取值。
KOUOJ_AI_MODEL_PROVIDER = os.environ.get("KOUOJ_AI_MODEL_PROVIDER", "openai-compatible")

# 模型服务地址，例如 OpenAI、DeepSeek、通义千问兼容模式、本地 Ollama 代理等。
KOUOJ_AI_MODEL_BASE_URL = os.environ.get("KOUOJ_AI_MODEL_BASE_URL", "")

# 模型 API Key 必须从环境变量读取，不能写死在代码里。
KOUOJ_AI_MODEL_API_KEY = os.environ.get("KOUOJ_AI_MODEL_API_KEY", "")

# 默认模型名。真实使用哪个模型由 .env 决定，代码只提供一个便于开发的默认值。
KOUOJ_AI_MODEL_NAME = os.environ.get("KOUOJ_AI_MODEL_NAME", "gpt-4o-mini")

# 模型调用的温度和超时配置。温度默认 0，让诊断输出更稳定；超时默认 30 秒。
KOUOJ_AI_MODEL_TEMPERATURE = os.environ.get("KOUOJ_AI_MODEL_TEMPERATURE", "0")
KOUOJ_AI_MODEL_TIMEOUT = os.environ.get("KOUOJ_AI_MODEL_TIMEOUT", "30")
