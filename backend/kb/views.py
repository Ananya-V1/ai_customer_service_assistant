from django.contrib.auth import authenticate
from rest_framework import generics, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Conversation, Document, KnowledgeBase
from .permissions import IsAdminOrReadOnly
from .serializers import (
    ConversationSerializer,
    DocumentSerializer,
    KnowledgeBaseSerializer,
)
from .agents.graph import run as run_agent_graph
from .services.ingestion import ingest_document

# checks credentials (using authenticate())
# returns DRF auth token
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username", "") # parsing -> converting raw JSON text into a python dict (for request)
        password = request.data.get("password", "") # parsing
        user = authenticate(request, username=username, password=password) # Django's built in credential check (verifies password hash)
        if user is None:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED) # serialization -> converting the dict back into JSON format to send back over HTTP (for response)
        token, _ = Token.objects.get_or_create(user=user) # 
        return Response({"token": token.key, "is_staff": user.is_staff}) # serialization

# inherited CRUD operations
class KnowledgeBaseViewSet(viewsets.ModelViewSet):
    queryset = KnowledgeBase.objects.all() # access to all rows in kb
    serializer_class = KnowledgeBaseSerializer # converts to and from JSON
    # GET -> turns model into python dict; POST/PUT -> validates incoming JSON by checking that name isn't blank or too long
    permission_classes = [IsAdminOrReadOnly] # anyone can GET; only admin can POST/PUT/DELETE


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all() # access to all Document rows
    serializer_class = DocumentSerializer # converts Document rows to and from JSON
    permission_classes = [IsAdminOrReadOnly]

    def perform_create(self, serializer): # handles POST
        document = serializer.save() # writes to the document row (creates new document INSERT)
        ingest_document(document) # extract, chunk, embed, and store chunks


class ChatView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        question = request.data.get("message", "").strip() # parsing
        if not question:
            return Response({"detail": "message is required."}, status=status.HTTP_400_BAD_REQUEST) # if empty

        conversation_id = request.data.get("conversation_id") # get converssation id
        if conversation_id: # if conversation id exists
            try:
                conversation = Conversation.objects.get(pk=conversation_id)
            except Conversation.DoesNotExist:
                return Response({"detail": "Conversation not found."}, status=status.HTTP_404_NOT_FOUND)
        else: # if not create conversation
            conversation = Conversation.objects.create()

        answer, sources, agent_used = run_agent_graph(question, conversation)

        conversation.messages.create(role="user", content=question)
        conversation.messages.create(role="assistant", content=answer, sources=sources)
        conversation.save(update_fields=["updated_at"])

        return Response( # serialization
            {
                "conversation_id": conversation.id,
                "answer": answer,
                "sources": sources,
                "agent_used": agent_used,
            }
        )


class ConversationDetailView(generics.RetrieveAPIView):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [AllowAny]
