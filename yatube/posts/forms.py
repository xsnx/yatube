from django.forms import ModelForm
from .models import Post


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