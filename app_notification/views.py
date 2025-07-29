from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q
from .models import (
    Notification, NotificationPreference, EventType, UserEventPreference
)
from .serializers import (
    NotificationSerializer, NotificationListSerializer, NotificationPreferenceSerializer,
    MarkAsReadSerializer, EventTriggerSerializer, EventTypeSerializer,
    UserEventPreferenceSerializer, UpdateEventPreferenceSerializer
)
from .services import NotificationService
from app_notification.permissions import IsOwnerOrReadOnly
from drf_spectacular.utils import extend_schema

User = get_user_model()

class NotificationPagination(PageNumberPagination):
    """Custom pagination for notifications"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

@extend_schema(tags=["Notifications"])
class UnreadNotificationsView(generics.ListAPIView):
    """
    GET /api/v1/notifications/unread/
    List unread notifications for the current user
    """
    serializer_class = NotificationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event_type']
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user,
            is_read=False
        ).select_related('event_type').order_by('-created_at')

@extend_schema(tags=["Notifications"])
class NotificationHistoryView(generics.ListAPIView):
    """
    GET /api/v1/notifications/history/
    Full notification history for the current user
    """
    serializer_class = NotificationListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = NotificationPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['event_type', 'is_read']
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('event_type').order_by('-created_at')

@extend_schema(tags=["Notifications"])
class NotificationDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/notifications/{id}/
    Get detailed notification with delivery status
    """
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(
            user=self.request.user
        ).select_related('event_type').prefetch_related('deliveries')

@extend_schema(tags=["Notifications"])
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def mark_notifications_read(request):
    """
    POST /api/v1/notifications/read/
    Mark one or multiple notifications as read
    """
    serializer = MarkAsReadSerializer(data=request.data, context={'request': request})
    
    if serializer.is_valid():
        notification_ids = serializer.validated_data['notification_ids']
        updated_count = NotificationService.mark_as_read(request.user, notification_ids)
        
        return Response({
            'message': f'{updated_count} notifications marked as read',
            'updated_count': updated_count
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(tags=["Notifications"])
class NotificationPreferencesView(generics.RetrieveUpdateAPIView):
    """
    GET/PUT /api/v1/notifications/preferences/
    Get or update user's notification preferences
    """
    serializer_class = NotificationPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        preferences, created = NotificationPreference.objects.get_or_create(
            user=self.request.user,
            defaults={
                'in_app_enabled': True,
                'email_enabled': True,
                'sms_enabled': False,
            }
        )
        
        # Create default event preferences if user is new
        if created:
            NotificationService._create_default_event_preferences(self.request.user)
        
        return preferences

@extend_schema(tags=["Event Management"])
class EventTypesView(generics.ListCreateAPIView):
    """
    GET/POST /api/v1/notifications/event-types/
    List all active event types or create new ones (admin only)
    """
    serializer_class = EventTypeSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return EventType.objects.filter(is_active=True).order_by('name')
    
    def get_permissions(self):
        """Only allow POST for admin users"""
        if self.request.method == 'POST':
            return [permissions.IsAdminUser()]
        return [permissions.IsAuthenticated()]

@extend_schema(tags=["Event Management"])

class UserEventPreferencesView(generics.ListAPIView):
    """
    GET /api/v1/notifications/event-preferences/
    Get user's event-specific preferences
    """
    serializer_class = UserEventPreferenceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserEventPreference.objects.filter(
            user=self.request.user
        ).select_related('event_type').order_by('event_type__name')

@extend_schema(tags=["Event Management"])
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_event_preferences(request):
    """
    POST /api/v1/notifications/event-preferences/update/
    Update multiple event preferences at once
    """
    serializer = UpdateEventPreferenceSerializer(data=request.data)
    
    if serializer.is_valid():
        preferences_data = serializer.validated_data['preferences']
        updated_preferences = NotificationService.update_user_event_preferences(
            request.user, 
            preferences_data
        )
        
        response_serializer = UserEventPreferenceSerializer(updated_preferences, many=True)
        
        return Response({
            'message': f'Updated {len(updated_preferences)} event preferences',
            'preferences': response_serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(tags=["Event Management"])
@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def trigger_notification_event(request):
    """
    POST /api/v1/notifications/trigger/
    Trigger a notification event (for testing/simulation)
    """
    serializer = EventTriggerSerializer(data=request.data)
    
    if serializer.is_valid():
        event_type_code = serializer.validated_data['event_type_code']
        payload = serializer.validated_data['payload']
        target_users = serializer.validated_data.get('target_users')
        
        # Add current user to context if not specified
        if 'user_id' not in payload:
            payload['user_id'] = request.user.id
        
        notifications = NotificationService.dispatch_notification(
            event_type_code=event_type_code,
            context=payload,
            target_users=target_users
        )
        
        return Response({
            'message': f'Triggered {event_type_code} event',
            'notifications_created': len(notifications),
            'notification_ids': [n.id for n in notifications]
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@extend_schema(tags=["Event Management"])# Admin-only views for managing event types
class CreateEventTypeView(generics.CreateAPIView):
    """
    POST /api/v1/notifications/admin/event-types/
    Create new event type (admin only)
    """
    serializer_class = EventTypeSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def perform_create(self, serializer):
        event_type = serializer.save()
        # Create default preferences for all existing users
        NotificationService._create_default_preferences_for_event_type(event_type)