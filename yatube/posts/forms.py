from django.forms import ModelForm
from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'text': 'Текст',
            'group': 'Группа',
            'image': 'Изображение',
        }
        help_texts = {
            'text': 'Текст поста',
            'group': 'Выбери группу',
            'image': 'Картинка к посту',
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        labels = {'text': 'Текст'}
        help_texts = {'text': 'Текст комментария'}
