from django.db import models

from django.contrib.auth import get_user_model
from django.utils.text import Truncator
from django.db.models import Q, F


User = get_user_model() 

class Group(models.Model):
    title = models.CharField(max_length = 200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    class Meta:
        verbose_name = "Группа"
        verbose_name_plural = "Группы"

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст'
    )
    pub_date = models.DateTimeField(
        "date published", 
        auto_now_add=True, 
        db_index=True
        )
    author = models.ForeignKey(User, 
        on_delete=models.CASCADE, 
        related_name='posts',
        verbose_name = 'Автор'
        )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name="posts",
        blank=True,
        null=True,
        verbose_name = 'Группа'
        )
    image = models.ImageField(upload_to='posts/', blank=True, null=True)

    def __str__(self):
        return Truncator(self.text).chars(100) 

    class Meta:
        ordering = ['-pub_date']
        verbose_name = "Пост"
        verbose_name_plural = "Посты"


class Comment(models.Model):
    post = models.ForeignKey(Post,
        on_delete=models.SET_NULL,
        related_name="comments", blank=True, null=True,
        verbose_name="Комментарий к посту",
        help_text="Добавьте комментарий к посту"
        )
    author = models.ForeignKey(User, 
        on_delete=models.CASCADE, 
        related_name='comments',
        verbose_name = 'Автор',
        help_text="Автор комментария"
        )
    text = models.TextField(
        verbose_name='Комментарий к посту'
        )
    created = models.DateTimeField("date published", auto_now_add=True)

    class Meta:
        ordering = ('created',)

class Follow(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='follower'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='following'
    )

    def save(self, **kwargs):
        if self.user != self.author:
            super(Follow, self).save(**kwargs)
    
    def __str__(self):
        return f"{self.user.username} follow to {self.author.username}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author'
            ),
            models.CheckConstraint(
                check=~Q(user=F('author')),
                name='user_not_author',
            )
        ]