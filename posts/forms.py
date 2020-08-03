from django import forms
from .models import Post, Comment
from django.forms import ModelForm



class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['group', 'text', 'image']

        help_texts = {
            'group': 'Выберите группу для поста(необязательно)',
            'text': 'Введите текст'
        }
    
        labels = {
                'group': "Группа",
                'text': "Текст"
            }


class CommentForm(ModelForm):
    text = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = Comment
        fields = ['text']

        labels = {
            "text": "Текст",
        }
        
        help_texts = {
            "text": "Текст вашего комментария",
        }
