from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ChatView,
    ConversationDetailView,
    DocumentViewSet,
    KnowledgeBaseViewSet,
    LoginView,
)

router = DefaultRouter()
router.register("knowledge-bases", KnowledgeBaseViewSet, basename="knowledge-base")
router.register("documents", DocumentViewSet, basename="document")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="login"),
    path("chat/", ChatView.as_view(), name="chat"),
    path("conversations/<int:pk>/", ConversationDetailView.as_view(), name="conversation-detail"),
    path("", include(router.urls)),
]
