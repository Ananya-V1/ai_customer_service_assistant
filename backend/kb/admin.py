from django.contrib import admin

from .models import Conversation, Document, DocumentChunk, KnowledgeBase, Message, Order


@admin.register(KnowledgeBase)
class KnowledgeBaseAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "knowledge_base", "status", "page_count", "created_at")
    list_filter = ("status", "knowledge_base")


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "chunk_index", "knowledge_base")
    list_filter = ("knowledge_base",)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "created_at", "updated_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "created_at")
    list_filter = ("role",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "product_name", "status", "order_date", "amount")
    list_filter = ("status",)
    search_fields = ("customer_name", "product_name")
