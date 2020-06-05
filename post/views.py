from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from .models import Post, Tag
from .forms import PostForm

from django.contrib.auth.decorators import login_required
from django.db.models import Count

#from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

#web crawlling
import ssl, urllib, requests
from bs4 import BeautifulSoup


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
    tag = post.tag_set.all()
    
    if tag:
        info = post_info(tag[0].name)
    else:
        info = post_info()
            
    return render(request, 'post/post_num.html', {
        'posts' : post,
        'info' : info
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
    tag =  get_object_or_404(Tag, name=tag)
    tag_all = Tag.objects.annotate(num_post=Count('post')).order_by('-num_post')
    
    if tag:
        post_list = Post.objects.filter(tag_set__name__iexact=tag) \
        .prefetch_related('tag_set', 'like_user_set__profile', 'comment_set__author__profile', 
                           'author__profile__follower_user', 'author__profile__follower_user__from_user')\
        .select_related('author__profile') 
        return redirect('post:post_list')
        #return render(request, 'post/post_search.html',{
        #    'post' : post_list,
        #})
    else:
        return redirect('post:post_list')
    
def post_main(request):
    hottest_list = Post.objects.all()
    hottest_list = hottest_list[:5]
    friend_list = Post.objects.all()
    friend_list = friend_list[:5]
    """
    paginator = Paginator(recent_list, 6)
    page_num = request.POST.get('page')
    
    try:
        recent_list = paginator.page(page_num)
    except PageNotAnInteger:
        recent_list = paginator.page(1)
    except EmptyPage:
        recent_list = paginator.page(paginator.num_pages)
    """
    recent_list = Post.objects.all()[:5]
    if request.is_ajax():
        return render(request, 'post/post_list_ajax.html',{
            'posts': recent_list
        })
    
    return render(request, 'post/post_main.html', {
        'hottest_list': hottest_list,
        'friend_list': friend_list,
        'recent_list': recent_list,
    })
