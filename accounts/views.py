from django.shortcuts import render
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import logout as django_logout
from django.contrib.auth import authenticate, login
from .forms import SignupForm, LoginForm, EditForm
from .models import Profile, Follow, Scrap
from post.models import Post, Like
import json
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import F

# Create your views here.
def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            return redirect('accounts:login')
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {
        'form' : form,
    })


def login_check(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        name = request.POST.get('username')
        pwd = request.POST.get('password')

        user = authenticate(username=name, password=pwd)

        if user is not None:
            login(request, user)
            return redirect('/')
        else:
            return render(request, 'accounts/login.html')
    else:
        form = LoginForm()
        return render(request, 'accounts/login.html', {
            'form': form,
        })
    
def logout(request):
    django_logout(request)
    return redirect('/')


def user_profile(request, user, menu):
    target_user = get_object_or_404(Profile, pk=user)
    user_list = None
    post_list = None
    if menu == 'main':
        post_list = Post.objects.filter(author = target_user.user)
        title ="사진들"
    elif menu == 'following':
        user_list = target_user.get_following
        title = "팔로잉"
    elif menu == 'follower':
        user_list = target_user.get_follower
        title = "팔로워"
    elif menu == 'blacklist':
        user_list = target_user.get_blacklist
        title = "블랙리스트"
    elif menu == 'like':
        if request.user == target_user.user:
            post_list = Like.objects.filter(user=target_user.user).annotate(
                pid=F('post__id'), content=F('post__content'))
            title = "좋아요"
        else:
            print(request.user, target_user, target_user.user)
            title = "좋아요의 접근권한이 없습니다"
    elif menu == 'scrap':
        if request.user == target_user.user:
            post_list = Scrap.objects.filter(user=target_user).annotate(pid=F('post__id'))
            title = "스크랩"
        else:
            title = "스크랩의 접근권한이 없습니다"
    else:
        title = "잘못된 요청"
    return render(request, 'accounts/profile.html', {
        'title' : title,
        'target_user': target_user,
        'post_list' : post_list,
        'user_list' : user_list,
    })

@login_required
@require_POST
def follow(request):
    from_user = request.user.profile
    pk = request.POST.get('pk')
    to_user = get_object_or_404(Profile, pk=pk)
    print(from_user, to_user)
    follow, created = Follow.objects.get_or_create(from_user=from_user, to_user=to_user)
    
    if created:
        message = '팔로우 성공'
        follow.follow_or_black = True
        follow.save()
    else:
        follow.delete()
        message = '팔로우 취소'
        
    print(message)
    context = {
        'message': message,
    }
    
    return HttpResponse(json.dumps(context), content_type = "application/json")

@login_required
@require_POST
def blacklist(request):
    from_user = request.user.profile
    pk = request.POST.get('pk')
    to_user = get_object_or_404(Profile, pk=pk)
    follow, created = Follow.objects.get_or_create(from_user=from_user, to_user=to_user)
    
    print(from_user, to_user)
    if created:
        message = '블랙리스트 추가'
        follow.follow_or_black = False
        follow.save()
    else:
        follow.delete()
        message = '블랙리스트 해제'
    print(message)
    context = {
        'message': message,
    }
    
    return HttpResponse(json.dumps(context), content_type = "application/json")

@login_required
def profile_edit(request):
    user = get_object_or_404(Profile, pk = request.user.profile.id)
    
    if request.method == 'POST':
        form = EditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.id = user.id
            profile.user = user.user
            if not request.FILES:
                profile.picture = user.picture
            profile.save()
        return redirect('post:post_main')
    else:
        form = EditForm(instance=user)
        return render(request, 'accounts/profile_edit.html',{
            'user_info' : user,
            'form': form,
        })
    