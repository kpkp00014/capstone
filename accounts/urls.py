from django.urls import path
from .views import *

app_name = 'accounts'

urlpatterns = [
    path('signup/', signup, name = 'signup'),
    path('login/', login_check, name = 'login'),
    path('logout/', logout, name = 'logout' ),
    path('profile/<str:user>', user_profile, name = 'user_profile')
]