"""
gargoyle.builtins
~~~~~~~~~~~~~~~~~

:copyright: (c) 2010 DISQUS.
:license: Apache License 2.0, see LICENSE for more details.
"""

from gargoyle import gargoyle
from gargoyle.conditions import ModelConditionSet, RequestConditionSet, Percent, String, Boolean, \
                                ConditionSet, OnOrAfterDate, Setting

from django.contrib.auth.models import AnonymousUser, User
from django.core.validators import validate_ipv4_address
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.utils.html import escape

import socket
import iptools

class UserConditionSet(ModelConditionSet):
    percent = Percent()
    username = String()
    email = String()
    is_anonymous = Boolean(label='Anonymous')
    is_staff = Boolean(label='Staff')
    is_superuser = Boolean(label='Superuser')
    date_joined = OnOrAfterDate(label='Joined on or after')

    def can_execute(self, instance):
        return isinstance(instance, (User, AnonymousUser))

    def is_active(self, instance, conditions):
        """
        value is the current value of the switch
        instance is the instance of our type
        """
        if isinstance(instance, User):
            return super(UserConditionSet, self).is_active(instance, conditions)
        
        # HACK: allow is_authenticated to work on AnonymousUser
        condition = conditions.get(self.get_namespace(), {}).get('is_anonymous')
        return bool(condition)

gargoyle.register(UserConditionSet(User))

class IPAddress(String):
    def clean(self, value):
        validate_ipv4_address(value)
        return value

class IPRange(String):

    def _validate_cidr(self, value):
        if not iptools.validate_cidr(value):
            raise ValidationError('not a valid ip cidr notation', code='invalid')

    def validate(self, data):
        value = self.clean(data.get(self.name))
        self._validate_cidr(value)
        return value

    def is_active(self, condition, value):
        iprange = iptools.IpRangeList(condition)
        return value in iprange

    def display(self, value):
        iprange = iptools.IpRangeList(value)
        return "%r" % iprange

class IPRangeBulk(IPRange):

    def unpack(self, value):
        return value.replace("\n"," ").split(" ")

    def validate(self, data):
        data = self.clean(data.get(self.name, ""))
        for line in self.unpack(data):
            self._validate_cidr(line)
        return data

    def is_active(self, condition, value):
        conditions = self.unpack(condition)
        return any([IPRange.is_active(self, c, value) for c in conditions])

    def display(self,value):
        values = self.unpack(value)
        return mark_safe("<br />".join([" ".join(values[i:i+5]) for i in xrange(0, len(values), 5)]))

    def render(self, value):
        return mark_safe('<textarea name="%s"></textarea>' % (escape(self.name),))

class IPAddressConditionSet(RequestConditionSet):
    percent = Percent()
    ip_address = IPAddress(label='IP Address')

    def get_namespace(self):
        return 'ip'

    def get_field_value(self, instance, field_name):
        # XXX: can we come up w/ a better API?
        # Ensure we map ``percent`` to the ``id`` column
        if field_name == 'percent':
            return sum([int(x) for x in instance.META['REMOTE_ADDR'].split('.')])
        elif field_name == 'ip_address':
            return instance.META['REMOTE_ADDR']
        return super(IPAddressConditionSet, self).get_field_value(instance, field_name)

    def get_group_label(self):
        return 'IP Address'

gargoyle.register(IPAddressConditionSet())

class IPRangeConditionSet(RequestConditionSet):
    iprange = IPRange()

    def get_namespace(self):
        return 'iprange'
    
    def get_field_value(self, instance, field_name):
        return instance.META['REMOTE_ADDR']

    def get_group_label(self):
        return 'IP Range'

gargoyle.register(IPRangeConditionSet())

class IPRangeBulkConditionSet(RequestConditionSet):
    iprangebulk = IPRangeBulk()

    def get_namespace(self):
        return 'iprange'

    def get_group_label(self):
        return 'IP Range'

    def get_field_value(self, instance, field_name):
        return instance.META['REMOTE_ADDR']

gargoyle.register(IPRangeBulkConditionSet())

class HostConditionSet(ConditionSet):
    hostname = String()

    def get_namespace(self):
        return 'host'
    
    def can_execute(self, instance):
        return instance is None
    
    def get_field_value(self, instance, field_name):
        if field_name == 'hostname':
            return socket.gethostname()

    def get_group_label(self):
        return 'Host'
gargoyle.register(HostConditionSet())

class SettingConditionSet(ConditionSet):
    setting = Setting()

    def get_namespace(self):
        return "setting"

    def can_execute(self, instance):
        return instance is None

    def get_field_value(self, instance, field_name):
        if field_name == "setting":
            from django.conf import settings
            return settings
        else:
            return ConditionSet.get_field_value(self, instance, field_name)

    def get_group_label(self):
        return 'Setting'

gargoyle.register(SettingConditionSet())

