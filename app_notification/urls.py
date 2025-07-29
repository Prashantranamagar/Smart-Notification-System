from django.urls import path
from . import views

urlpatterns = [
    # Notification endpoints
    path(
        "unread/", views.UnreadNotificationsView.as_view(), name="unread-notifications"
    ),
    path(
        "history/", views.NotificationHistoryView.as_view(), name="notification-history"
    ),
    path(
        "<int:pk>/", views.NotificationDetailView.as_view(), name="notification-detail"
    ),
    path("read/", views.mark_notifications_read, name="mark-notifications-read"),
    # Preference endpoints
    path(
        "preferences/",
        views.NotificationPreferencesView.as_view(),
        name="notification-preferences",
    ),
    path(
        "event-preferences/",
        views.UserEventPreferencesView.as_view(),
        name="user-event-preferences",
    ),
    path(
        "event-preferences/update/",
        views.update_event_preferences,
        name="update-event-preferences",
    ),
    # Event management
    path("event-types/", views.EventTypesView.as_view(), name="event-types"),
    path("trigger/", views.trigger_notification_event, name="trigger-event"),
    # Admin endpoints
    path(
        "admin/event-types/",
        views.CreateEventTypeView.as_view(),
        name="admin-create-event-type",
    ),
]
