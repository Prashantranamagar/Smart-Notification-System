from django.urls import path
from .views import UnreadNotificationsView, NotificationHistoryView, MarkAsReadView
from .views import PreferenceListCreateView
from .views import TriggerEventView

urlpatterns = [
    path('unread/', UnreadNotificationsView.as_view()),
    path('read/', MarkAsReadView.as_view()),
    path('history/', NotificationHistoryView.as_view()),
    path('preferences/', PreferenceListCreateView.as_view()),
    path('trigger/', TriggerEventView.as_view()),
]