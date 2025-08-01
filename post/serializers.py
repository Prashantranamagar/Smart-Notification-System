from rest_framework import serializers
from .models import Post, Comment


class CommentSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source="author.username")

    class Meta:
        model = Comment
        fields = ["id", "post", "author", "author_username", "content", "created_at"]
        read_only_fields = ["id", "author", "created_at"]


class PostSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source="author.username")
    comments = CommentSerializer(many=True, read_only=True)  # nested comments

    class Meta:
        model = Post
        fields = [
            "id",
            "author",
            "author_username",
            "title",
            "content",
            "created_at",
            "comments",
        ]
        read_only_fields = ["id", "author", "created_at"]
