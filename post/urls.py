from django.urls import path
from . import views

urlpatterns = [
    # Posts
    path('posts/', views.PostListCreateView.as_view(), name='post-list-create'),         # GET list, POST create
    path('posts/<int:pk>/', views.PostRetrieveUpdateDeleteView.as_view(), name='post-detail'),  # GET, PUT, DELETE

    # Comments
    path('comments/', views.CommentListCreateView.as_view(), name='comment-list-create'),          # GET list, POST create
    path('comments/<int:pk>/', views.CommentRetrieveUpdateDeleteView.as_view(), name='comment-detail'),  # GET, PUT, DELETE
]
