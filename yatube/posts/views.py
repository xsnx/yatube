from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Group, Post, User
from .forms import PostForm


def index(request):
    post_list = Post.objects.select_related('author', "group")
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        "group.html",
        {'page': page, "group": group, 'paginator': paginator}
    )


@login_required()
def new_post(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('/')
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.post_set.all()
    count = posts.count
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    context = {
        'page': page,
        'post': posts,
        "author": author,
        'paginator': paginator,
        'count': count,
    }
    return render(request, "profile.html", context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    #post = Post.objects.get(id=post_id)
    author = get_object_or_404(User, username=username)
    posts = author.post_set.all()
    count = posts.count
    form = PostForm(instance=post)
    context = {'post': post, 'form': form, 'author': author, 'count': count}
    return render(request, 'post.html', context)


@login_required()
def post_edit(request, username, post_id):
    #post = get_object_or_404(Post, pk=post_id, author__username=username)
    post = Post.objects.get(id=post_id)
    if request.user.username != username:
        return redirect(f'/{post.author}/{post_id}')
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect(f'/{username}/{post_id}')
    return render(request, 'new.html', {'post': post, 'form': form})