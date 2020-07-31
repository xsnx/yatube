from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from .models import Group, Post, User, Follow
from .forms import PostForm, CommentForm
from django.views.decorators.cache import cache_page


@cache_page(20, key_prefix='index_page')
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
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('/')
    return render(request, 'new.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    count = posts.count
    paginator = Paginator(posts, 5)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    follower = author.follower.all().count
    following = author.following.all().count
    context = {
        'page': page,
        'post': posts,
        "author": author,
        'paginator': paginator,
        'count': count,
        'follower': follower,
        'following': following,
    }
    return render(request, "profile.html", context)


def post_view(request, username, post_id):
    author = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=author)
    comments = post.comments.all()
    count = author.posts.all().count
    follower = author.follower.all().count
    following = author.following.all().count
    form_comment = CommentForm()
    context = {
        'post': post,
        'author': author,
        'comments': comments,
        'count': count,
        'follower': follower,
        'following': following,
        'form_comment': form_comment,
    }
    return render(request, 'post.html', context)


@login_required()
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if request.user != post.author:
        return redirect('post', username=username, post_id=post_id)
    form = PostForm(request.POST or None,
                    files=request.FILES or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect("post", username=request.user.username,
                        post_id=post_id)
    return render(request, 'new.html', {'post': post, 'form': form})


@login_required()
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        form.save()
        return redirect("post", username=username,
                        post_id=post_id)
    return render(request, 'comments.html', {'post': post, 'form': form})


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, 'follow.html',
                  {'page': page, 'paginator': paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if (request.user != author
            and not Follow.objects.filter(user=request.user,
                                          author=author).exists()):
        follow = Follow()
        follow.author = author
        follow.user = request.user
        follow.save()
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    un_follow = Follow.objects.get(user=request.user, author=author)
    un_follow.delete()
    return redirect("profile", username=username)
