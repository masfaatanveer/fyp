from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse


def home(request):
    return JsonResponse(
        {
            "status": "ok",
            "message": "KFUEIT Agent Assist backend is running.",
            "routes": [
                "/admin/",
                "/api/agent/query/",
                "/api/agent/admin/logs/",
            ],
        }
    )

urlpatterns = [
    path("", home, name="home"),
    path("admin/", admin.site.urls),
    path("api/agent/", include("apps.agent.urls")),
]
