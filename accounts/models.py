from django.conf import settings
from django.db import models
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
from post.models import Post
# Create your models here.

def user_path(instance, filename):
    from random import choice
    import string
    arr = [choice(string.ascii_letters) for _ in range(8)]
    pid = ''.join(arr)
    extension = filename.split('.')[-1]
    return 'accounts/{}/{}.{}'.format(instance.user.username, pid, extension)

class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    nickname = models.CharField('닉네임', max_length=20, unique=True)
    
    picture = ProcessedImageField(upload_to=user_path,
                                 processors=[ResizeToFill(150,150)],
                                 format='JPEG',
                                 options={'quality':90},
                                 blank=True
                                 )
    
    about = models.CharField(max_length=300, blank=True)
    GENDER_C = (
        ('선택안함', '선택안함'),
        ('여성', '여성'),
        ('남성', '남성'),
    )
    
    gender = models.CharField('성별(선택사항)',
                             max_length=10,
                             choices=GENDER_C,
                             default='N')
    
    scraped_set = models.ManyToManyField('post.Post',
                               blank = True,
                               through = 'Scrap',
                               )
    follow_set = models.ManyToManyField('self',
                                blank = True,
                                through = 'Follow',
                                symmetrical = False,
                                )
    def __str__(self):
        return self.nickname    
        
    @property
    def get_follower(self):
        return [i.from_user for i in self.follower_user.filter(follow_or_black=True)]
    @property
    def get_following(self):
        return [i.to_user for i in self.follow_user.filter(follow_or_black=True)]
    @property
    def get_blacklist(self):
        return [i.to_user for i in self.follow_user.filter(follow_or_black=False)]
    
    @property
    def follower_count(self):
        return len(self.get_follower)
    @property
    def following_count(self):
        return len(self.get_following)
    @property
    def blacklist_count(self):
        return len(self.get_blacklist)
    
    @property
    def is_follower(self, user):    #user가 나의 팔로워인가1
        return user in self.get_follower
    @property
    def is_following(self, user):    #내가 user를 팔로잉 하고 있는가
        return user in self.get_following
    @property
    def is_blacklist(self, user):    #user가 내 블랙리스트에 있는가
        return user in self.get_blacklist
    
    
    
class Follow(models.Model):
    from_user = models.ForeignKey(Profile,
                                related_name = 'follow_user',
                                on_delete=models.CASCADE)
    to_user = models.ForeignKey(Profile,
                              related_name = 'follower_user',
                              on_delete = models.CASCADE)
    follow_or_black = models.BooleanField(default=True)    # true = 팔로잉, False = 블랙리스트
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return "{} -> {} | {}".format(self.from_user, self.to_user, self.follow_or_black)
    class Meta:
        unique_together = (
            ('from_user', 'to_user')
        )

class Scrap(models.Model):
    user = models.ForeignKey('Profile', on_delete=models.CASCADE, default='')
    post = models.ForeignKey('post.Post', on_delete=models.CASCADE, default='')
    content = models.CharField(max_length=200, 
                               help_text='200자 이내의 메모를 남길 수 있습니다',
                               blank = True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    
    class Meta:
        unique_together = (
            ('user', 'post')
        )
