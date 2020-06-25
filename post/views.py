from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Post, Tag, Like
from accounts.models import Scrap
from .forms import PostForm

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q, F, Count

from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

#web crawlling
import ssl, urllib, requests
from bs4 import BeautifulSoup

import json
from django.http import HttpResponse

# Create your views here.
def post_list(request, tag):
    
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
            return redirect('post:post_main')
    else:
        form = PostForm()
    return render(request, 'post/post_new.html',{
        'form':form,
    })

def post_num(request, post_id):
    post =  get_object_or_404(Post, pk=post_id)
    tag = post.tag_set.all()
    
    if tag:
        info = post_info(tag[0].name)
    else:
        info = post_info()
    user = request.user
    if user.is_authenticated:
        scrap = user.profile.scrap_set
        if scrap.filter(post=post):
            scrap = scrap.filter(post=post)[0]
        else:
            scrap = None
    else:
        scrap = None
    return render(request, 'post/post_num.html', {
        'posts' : post,
        'info' : info,
        'scrap': scrap,
    })

def post_info(tag=None):
    if tag==None:
        return False
    tag = urllib.parse.quote(tag)
    url = "https://www.10000recipe.com/recipe/list.html?q="+tag
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as response:
        html = response.read()
    soup = BeautifulSoup(html.decode('utf-8'), 'html.parser')
    
    result = soup.find_all("div", "col-xs-3")
    if len(result) > 1:
        if len(result)>5:
            result = result[:5]
        else:
            result = result[:len(result)-1]
    else: 
        return False
    
    infoData = []
    for post in result:
        data = {
        'link': post.a['href'],
        'img': post.select('a.thumbnail > img')[0]['src'],
        'title': post.select('div.caption > h4')[0].string,
        'author': post.select('div.caption > p')[0].string,
    }
        infoData.append(data)
    return infoData


@login_required
def post_delete(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user or request.method =='GET':
        messages.warning(request, '잘못된 접근입니다.')
        print(messages.warning)
    if request.method == 'POST':
        post.delete()
        messages.success(request, '삭제 성공!')
    
    return redirect('post:post_main')

@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author != request.user:
        messages.warning(request, '잘못된 접근입니다.')
        return redirect('post:post_main')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save()
            post.tag_set.clear()
            post.tag_save()
            messages.success(request, '수정완료')
            return redirect('post:post_main')
    else:
        form = PostForm(instance=post)
    return render(request, 'post/post_edit.html',{
        'post' : post,
        'form' : form,
    })

def post_search(request, tag):
    tag_all = Tag.objects.annotate(num_post=Count('post')).order_by('-num_post')
    
    if Tag.objects.filter(name = tag):
        post_list = Post.objects.filter(tag_set__name__iexact=tag)\
        .prefetch_related('tag_set', 'like_user_set__profile', 
                           'author__profile__follower_user', 'author__profile__follower_user__from_user')\
        .select_related('author__profile') 
        print(post_list)
        return render(request, 'post/post_list.html', {
            'post_list' : post_list,
            'about' : '#'+tag+'의 검색 결과'
        })
    else:
        return redirect('post:post_main')
    
def post_more(request, about):
    if about=='hottest':
        post_list = Like.objects.values('post')\
    .annotate(Count('user'), content=F('post__content'), url=F('post__photo__url'))\
    .order_by('-user__count')
    elif about == 'friend':
        if not request.user:
            return redirect('post:post_main')
        post_list = Post.objects.filter()\
        .prefetch_related()\
        .select_related('post__follow')
    elif about == 'recents':
        post_list = Post.objects.all()
    elif about == 'friends':
        if request.user.is_authenticated:
            user = request.user
        else:
            user = None
            post_list = None
        if user:
            post_list = Post.objects.exclude(
                ~Q(author__profile__follow_user__from_user__profile__id=user.profile.id,
                                             author__profile__follower_user__follow_or_black=True))
        else:
            friend_list = None
    else:
        return redirect('post:post_main')
    
    
    paginator = Paginator(post_list, 4)
    page_num = request.POST.get('page')
    
    try:
        posts = paginator.page(page_num)
    except PageNotAnInteger:
        posts = paginator.page(1)
    except EmptyPage:
        posts = paginator.page(paginator.num_pages)


        
    if request.is_ajax():
        return render(request, 'post/post_more_ajax.html', {
            'post_list': posts,
        })
    
    return render(request, 'post/post_list.html', {
            'post_list': posts,
            'about': about,
        })
    
    
    
    
def post_main(request):
    if request.user.is_authenticated:
        user = request.user
    else:
        user = None
    hottest_list = Like.objects.values('post')\
    .annotate(Count('user'), content=F('post__content'), url=F('post__photo__url'))\
    .order_by('-user__count')[:5]
    if user:
        friend_list = Post.objects.exclude(
            ~Q(author__profile__follow_user__from_user__profile__id=user.profile.id,
                                         author__profile__follower_user__follow_or_black=True))
        paginator = Paginator(friend_list, 4)
        page_num = request.POST.get('page')
        print(page_num)
        try:
            posts = paginator.page(page_num)
        except PageNotAnInteger:
            posts = paginator.page(1)
        except EmptyPage:
            posts = paginator.page(paginator.num_pages)
    else:
        friend_list = None
        posts = None



    recent_list = Post.objects.filter(~Q(author__profile__follow_user__from_user__profile__user=user,
                                       author__profile__follow_user__follow_or_black=False
                                      ))[:5]
    
    if request.is_ajax():
        return render(request, 'post/post_more_ajax.html',{
            'post_list': posts
        })
    
    return render(request, 'post/post_main.html', {
        'hottest_list': hottest_list,
        'post_list': posts,
        'recent_list': recent_list,
    })

@login_required
@require_POST
def post_like(request):
    pk = request.POST.get('pk', None)
    post = get_object_or_404(Post, pk=pk)
    post_like, post_like_created = post.like_set.get_or_create(user=request.user)
    
    if not post_like_created:
        post_like.delete()
        message = '좋아요 삭제'
    else:
        message = "좋아요"

    context = {
        'like_count' : post.like_count,
        'message' : message,
    }
    return HttpResponse(json.dumps(context), content_type="application/json")

@login_required
@require_POST
def post_scrap(request):
    pk = request.POST.get('pk', None)
    post = get_object_or_404(Post, pk=pk)
    user = request.user.profile
    if(user.user == post.author):
        return HttpResponse("<script>alert('잘못된 요청입니다');</script>")
    content = request.POST.get('content', None)
    s, s_created = Scrap.objects.get_or_create(post=post, user=user)
    if not s_created:
        s.content = content
        s.save()
        message = "스크랩 수정"
    else:
        s.content = content
        s.save()
        message = "스크랩 등록 성공"
    context = {
        'message' : message
    }
    return HttpResponse(json.dumps(context), content_type="application/json")

@login_required
@require_POST
def post_scrap_delete(request):
    post = request.POST.get('pk')
    user = request.user.profile
    scrap = Scrap.objects.filter(post=post, user=user)
    scrap.delete()
    context = {
        'message' : '삭제 성공'
    }
    return HttpResponse(json.dumps(context), content_type="application/json")
    if post.author != request.user or request.method =='GET':
        messages.warning(request, '잘못된 접근입니다.')
        print(messages.warning)
    if request.method == 'POST':
        post.delete()
        messages.success(request, '삭제 성공!')
    