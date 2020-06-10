from django.urls import path
from .views import *

app_name = 'post'

urlpatterns = [
    path('', post_main, name='post_main'),
    path('new', post_new, name='post_new'),
    path('edit/<int:pk>/', post_edit, name='post_edit'),
    path('delete/<int:pk>/', post_delete, name='post_delete'),
    path('post_num/<int:post_id>/', post_num, name='post_num'),
    path('more/<str:about>', post_more, name='post_list'),
    path('explore/tags/<str:tag>/', post_search, name='post_list'),
]