from django import template
import re

register = template.Library()

@register.filter
def add_link(value):
    content = value.content
    tags = value.tag_set.all()
    for tag in tags:
        content = re.sub(r'\#'+tag.name+r'\b', 
                         '<a href="/post/explore/tags/'+tag.name+'">#'+tag.name+'</a>', 
                         content) #   #으로 시작함, \b 단어가 끝나는 지점
    return content