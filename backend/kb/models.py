from django.db import models
from django.utils.text import slugify
from pgvector.django import VectorField


class KnowledgeBase(models.Model):
    name = models.CharField(max_length=255, unique=True) # what a person reads in the UI
    slug = models.SlugField(max_length=255, unique=True, blank=True) # what would appear in the URL
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Document(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_READY = "ready"
    STATUS_FAILED = "failed"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_READY, "Ready"),
        (STATUS_FAILED, "Failed"),
    ]

    knowledge_base = models.ForeignKey(
        KnowledgeBase, related_name="documents", on_delete=models.CASCADE
    )
    title = models.CharField(max_length=255, blank=True)
    file = models.FileField(upload_to="documents/")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    page_count = models.PositiveIntegerField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        if not self.title and self.file:
            self.title = self.file.name.rsplit("/", 1)[-1]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title or f"Document {self.pk}"


class DocumentChunk(models.Model):
    document = models.ForeignKey(Document, related_name="chunks", on_delete=models.CASCADE)
    knowledge_base = models.ForeignKey(
        KnowledgeBase, related_name="chunks", on_delete=models.CASCADE
    )
    chunk_index = models.PositiveIntegerField()
    text = models.TextField()
    embedding = VectorField(dimensions=768)

    class Meta:
        ordering = ["document_id", "chunk_index"]
        indexes = [models.Index(fields=["document", "chunk_index"])]

    def __str__(self):
        return f"{self.document_id}:{self.chunk_index}"


class Conversation(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"Conversation {self.pk}"


class Order(models.Model):
    STATUS_PENDING = "pending"
    STATUS_SHIPPED = "shipped"
    STATUS_DELIVERED = "delivered"
    STATUS_REFUNDED = "refunded"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_SHIPPED, "Shipped"),
        (STATUS_DELIVERED, "Delivered"),
        (STATUS_REFUNDED, "Refunded"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    customer_name = models.CharField(max_length=255)
    product_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    order_date = models.DateField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "orders"
        ordering = ["-order_date"]

    def __str__(self):
        return f"Order {self.pk}: {self.customer_name} / {self.product_name}"


class Message(models.Model):
    ROLE_USER = "user"
    ROLE_ASSISTANT = "assistant"
    ROLE_CHOICES = [
        (ROLE_USER, "User"),
        (ROLE_ASSISTANT, "Assistant"),
    ]

    conversation = models.ForeignKey(
        Conversation, related_name="messages", on_delete=models.CASCADE
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    sources = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:40]}"
