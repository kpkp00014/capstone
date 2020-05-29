from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Post, Tag
from .forms import PostForm

from django.contrib.auth.decorators import login_required
from django.db.models import Count

# Create your views here.
def post_list(request):
    
    post_list = Post.objects.all()
    
    if request.user.is_authenticated:
        username = request.user
        user = get_object_or_404(get_user_model(), username=username)
        user_profile = user.profile
                
        return render(request, 'post/post_list.html', {
            'user_profile' : user_profile,
            'posts' : post_list,
        })
    else:
        return render(request, 'post/post_list.html',{
            'posts':post_list,
        })
    
@login_required
def post_new(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            post.tag_save()
            messages.info(request, '새 글이 등록되었습니다')
            return redirect('post:post_list')
    else:
        form = PostForm()
    return render(request, 'post/post_new.html',{
        'form':form,
    })

def post_num(request, post_id):
    post =  get_object_or_404(Post, pk=post_id)
    return render(request, 'post/post_num.html', {
        'posts' : post,
    })

@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user or request.method =='GET':
        messages.warning(request, '잘못된 접근입니다.')
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, '삭제 성공!')
    
    return redirect('post:post_list')

@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        messages.warning(request, '잘못된 접근입니다.')
        return redirect('post:post_list')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()
            post.tag_set.clear()
            post.tag_save()
            messages.success(request, '수정완료')
            return redirect('post:post_list')
    else:
        form = PostForm(instance=post)
    return render(request, 'post/post_edit.html',{
        'post' : post,
        'form' : form,
    })

def post_search(request, tag):
    tag_all = Tag.objects.annotate(num_post=Count('post')).order_by('-num_post')
    
    if tag:
        post_list = Post.objects.filter(tag_set__name__iexact=tag) \
        .prefetch_related('tag_set', 'like_user_set__profile', 'comment_set__author__profile', 
                           'author__profile__follower_user', 'author__profile__follower_user__from_user')\
        .select_related('author__profile') 
        
        return redirect('post:post_search')
    else:
        return redirect('post:post_list')
