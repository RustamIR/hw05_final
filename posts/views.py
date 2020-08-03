from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView
from .models import Group, Post, User, Follow
#from django.contrib.auth.models import User
from .forms import PostForm, CommentForm
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils.decorators import method_decorator
from django.core.paginator import Paginator
from django.views.decorators.cache import cache_page
from django.core.files import File


@cache_page(20, key_prefix='index_page')
def index(request):
        post_list = Post.objects.all()
        paginator = Paginator(post_list, 10)  
        page_number = request.GET.get('page') 
        page = paginator.get_page(page_number)  
        return render(
            request,
            'index.html',
            {'page': page, 'paginator': paginator}
       )


def group_post(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts =group.posts.all()
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number) 
    return render(request, "group.html", {"group": group, 
                                          "posts": posts,
                                          "paginator":paginator,
                                          "page": page
                                          }
    )


@method_decorator(login_required, name='dispatch')
class PostNew(CreateView):
    form_class = PostForm
    success_url = reverse_lazy("index")
    template_name = "new.html"
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        return super().form_valid(form)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    items = post.comments.all()
    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('post', username=username, post_id=post_id)
    return render(request, 'post.html', 
            {'form': form, 
            'post': post, 
            'items': items}
        )


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post = author.posts.all()
    paginator = Paginator(post, 10)
    count = paginator.count
    following = False
    if Follow.objects.filter(user=User.objects.get(username=username),
                             author=User.objects.get(username=username)).count() != 0:
        following = True
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request,
        "profile.html",
        {
            "following":following,
            "author": author,
            "paginator": paginator,
            "post": post,
            "count": count,
            "page": page,
        },
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    author = post.author
    count = author.posts.count()
    form = CommentForm()
    items = post.comments.all()
    return render(request, 'post.html', {'post': post,
                                         'author': author,
                                         'count': count,
                                         'form': form,
                                         'items': items
                                         }
                            )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, id=post_id)
    if post.author != request.user:
        return redirect("post", username=username, post_id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect("post", username=username, post_id=post_id)
    return render(request, "new.html", {"form": form, "post": post})


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
    """Посты автора на которого подписан пользователь"""
    author = Follow.objects.filter(user=request.user)
    posts_fan = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(posts_fan, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {
                                           'author': author,
                                           'posts': posts_fan,
                                           'paginator': paginator,
                                           'page':page
                                           }
    )

@login_required
def profile_follow(request, username):
    """Подписка"""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Дизлайк отписка"""
    author = get_object_or_404(User, username=username)
    user = request.user
    Follow.objects.filter(user=user, author=author).delete()
    return redirect('profile', username=username)
