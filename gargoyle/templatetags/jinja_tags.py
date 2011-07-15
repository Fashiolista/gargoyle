from coffin.template import Library
from django.conf import settings
from django.template.defaultfilters import slugify
from gargoyle import gargoyle
import logging

logger = logging.getLogger(__name__)
register = Library()

@register.object
def switch_is_active(switch_slug, *instances):
    '''
    Jinja implementation for the ifswitch
    Usage:
    {% if switch_is_active('myspecialfeature') %}
    {% endif %}

    providing a request object (for ip based switches)
    {% if switch_is_active('myspecialfeature', request) %}
    {% endif %}
    
    providing the user for user based switches
    {% if switch_is_active('myspecialfeature', user) %}
    {% endif %}
    '''
    assert slugify(switch_slug) == switch_slug, 'switch slug should be a valid slug'
    
    
    is_active = gargoyle.is_active(switch_slug, *instances)
    logger.info('Switch %s is active is %s, based on these instances %s', switch_slug, is_active, map(type,instances))
    
    return is_active

