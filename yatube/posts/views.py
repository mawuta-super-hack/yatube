from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User

LIMIT = 10


def paginator(request, post_list):
    paginator = Paginator(post_list, LIMIT)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


def index(request):
    post_list = Post.objects.all().select_related('group', 'author')
    page_obj = paginator(request, post_list)
    context = {'page_obj': page_obj}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.select_related('group').filter(group=group)
    page_obj = paginator(request, post_list)
    context = {'group': group,
               'page_obj': page_obj}
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    user = request.user.id
    author = get_object_or_404(User, username=username)
    post_list = (Post.objects.select_related('author')
                 .filter(author_id=author.id))
    page_obj = paginator(request, post_list)
    following = False
    if Follow.objects.filter(
            author_id=author.id,
            user_id=request.user.id).exists():
        following = True
    context = {'page_obj': page_obj,
               'author': author,
               'post_list': post_list,
               'following': following,
               'user': user}
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post_d = get_object_or_404(Post, id=post_id)
    author = get_object_or_404(User, id=post_d.author_id)
    posts = Post.objects.select_related('author').filter(author_id=author.id)
    form = CommentForm()
    if form:
        add_comment(request, post_id)
    comments = Comment.objects.select_related('post').filter(
        post_id=post_d.id)
    context = {'post_d': post_d,
               'author': author,
               'posts': posts,
               'form': form,
               'comments': comments}
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            new_post = form.save(commit=False)
            new_post.author = request.user
            new_post.save()
            return redirect('posts:profile', new_post.author)
        form = PostForm()
        context = {'form': form}
        return render(request, 'posts/create_post.html', context)
    form = PostForm()
    context = {'form': form}
    return render(request, 'posts/create_post.html', context)


@login_required
def post_edit(request, post_id):
    edit_post = get_object_or_404(Post, id=post_id)
    author = get_object_or_404(User, id=edit_post.author_id)
    context = {'edit_post': edit_post,
               'author': author}
    if request.user.username != author.username:
        context['is_edit'] = False
        return redirect('posts:post_detail', post_id)
    else:
        context['is_edit'] = True
        if request.method == 'POST':
            form = PostForm(
                request.POST or None,
                instance=edit_post,
                files=request.FILES or None)
            if form.is_valid():
                edit_post = form.save(commit=False)
                edit_post.save()
                return redirect('posts:post_detail', post_id)
        form = PostForm(instance=edit_post)
        context['form'] = form
        return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    follow = Follow.objects.filter(user_id=request.user.id)
    post_list = Post.objects.select_related('author').filter(
        author__in=follow.values('author'))
    page_obj = paginator(request, post_list)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(author_id=author.id, user_id=request.user.id
                             ).exists():
        return redirect('posts:profile', username=author.username)
    if User.objects.get(username=username).id != request.user.id:
        follow = Follow.objects.create(
            author_id=author.id,
            user_id=request.user.id)
        follow.save()
    return redirect('posts:profile', username=author.username)


@login_required
def profile_unfollow(request, username):
    unfollow = get_object_or_404(
        Follow,
        author_id=User.objects.get(username=username).id,
        user_id=request.user.id)
    unfollow.delete()
    return redirect('posts:profile',
                    username=User.objects.get(username=username))
