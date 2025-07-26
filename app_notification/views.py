# == apps/notifications/views/notification_views.py ==
from rest_framework import generics, permissions
from .models import Notification
from .serializers import NotificationSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
import logging

logger = logging.getLogger(__name__)


class UnreadNotificationsView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user, is_read=False)


class NotificationHistoryView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)


class MarkAsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        ids = request.data.get("ids", [])
        Notification.objects.filter(id__in=ids, user=request.user).update(is_read=True)
        return Response({"message": "Notifications marked as read."})


# == apps/notifications/views/preference_views.py ==
from .models import NotificationPreference
from .serializers import NotificationPreferenceSerializer

class PreferenceListCreateView(generics.ListCreateAPIView):
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return NotificationPreference.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


# == apps/notifications/views/trigger_event_view.py ==
from rest_framework.views import APIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from .dispatcher import handle_event_trigger

class TriggerEventView(APIView):
    permission_classes = [IsAdminUser]

    def post(self, request):
        event_type = request.data.get("event_type")
        payload = request.data.get("payload")
        handle_event_trigger(event_type, payload)
        return Response({"message": f"Event '{event_type}' triggered."})