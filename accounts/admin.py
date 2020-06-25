from django.contrib import admin
from .models import Profile, Follow, Scrap

# Register your models here.
class FollowInline(admin.TabularInline):
    model = Follow
    fk_name = 'from_user'
class ScrapInline(admin.TabularInline):
    model = Scrap

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'nickname', 'user']
    list_display_links = ['nickname', 'user']
    search_fields = ['nickname']
    inlines = [FollowInline, ScrapInline]
    
@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'created_at', 'follow_or_black']
    list_display_links = ['from_user', 'to_user', 'created_at']
    
@admin.register(Scrap)
class ScrapAdmin(admin.ModelAdmin):
    list_display = ['user', 'post', 'content', 'created_at', 'updated_at']
    list_display_links = ['user', 'post', 'content']