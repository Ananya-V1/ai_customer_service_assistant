from rest_framework import serializers

from .models import Conversation, Document, KnowledgeBase, Message


class KnowledgeBaseSerializer(serializers.ModelSerializer):
    document_count = serializers.IntegerField(source="documents.count", read_only=True)

    class Meta:
        model = KnowledgeBase
        fields = ["id", "name", "slug", "description", "created_at", "document_count"]
        read_only_fields = ["id", "slug", "created_at", "document_count"]


class DocumentSerializer(serializers.ModelSerializer):
    knowledge_base_name = serializers.CharField(source="knowledge_base.name", read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "knowledge_base",
            "knowledge_base_name",
            "title",
            "file",
            "status",
            "page_count",
            "error_message",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "page_count", "error_message", "created_at", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "role", "content", "sources", "created_at"]
        read_only_fields = fields


class ConversationSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Conversation
        fields = ["id", "created_at", "updated_at", "messages"]
        read_only_fields = fields
