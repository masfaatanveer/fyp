from django.urls import path
from . import views

urlpatterns = [
    path("query/", views.agent_query, name="agent_query"),
    path("vapi/", views.vapi_webhook, name="vapi_webhook"),
    path("admin/logs/", views.admin_logs, name="admin_logs"),
    path("student/<str:roll_no>/", views.student_lookup, name="student_lookup"),
]
