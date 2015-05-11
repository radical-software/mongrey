# -*- coding: utf-8 -*-

import json
import datetime

import arrow

from peewee import (Proxy, 
                    Model,
                    DataError, 
                    CharField, 
                    DateTimeField, 
                    IntegerField, 
                    FloatField, 
                    TextField, 
                    BooleanField,
                    fn)

try:
    from peewee import PostgresqlDatabase
    import psycopg2
    HAVE_PSYCOPG2 = True
except ImportError:
    HAVE_PSYCOPG2 = False

try:
    from peewee import MySQLDatabase
    import MySQLdb as mysql  # prefer the C module.
    HAVE_MYSQL = True
except ImportError:
    try:
        import pymysql as mysql
    except ImportError:
        HAVE_MYSQL = False

from ... import utils
from ... import validators
from ... import constants
from ...policy import generic_search, search_mynetwork

database_proxy = Proxy()

class ValidationError(AssertionError):

    def __init__(self, message="", **kwargs):
        self.field_name = kwargs.get('field_name')
        self.message = message
        
    def __str__(self):
        return unicode(self.message)

    def __unicode__(self):
        return self.message

class DateTimeFieldExtend(DateTimeField):

    def python_value(self, value):
        return arrow.get(value).datetime


class Domain(Model):
    
    name = CharField(unique=True, index=True)

    def _clean(self):
        validators.clean_domain(self.name, field_name="name", error_class=ValidationError)
    
    def save(self, force_insert=False, only=None, validate=True):
        if validate:
            self._clean()
        return Model.save(self, force_insert=force_insert, only=only)

    @classmethod
    def search(cls, protocol):
        
        sender = protocol.get('sender', None)
        sender_domain = utils.parse_domain(sender)
        recipient = protocol.get('recipient')
        recipient_domain = utils.parse_domain(recipient)

        if sender_domain:
            if cls.select().where(fn.Lower(cls.name)==sender_domain).first():
                return constants.DOMAIN_SENDER_FOUND 

        if recipient_domain:
            if cls.select().where(fn.Lower(cls.name)==recipient_domain).first():
                return constants.DOMAIN_RECIPIENT_FOUND 
        
        return constants.DOMAIN_NOT_FOUND


    def __unicode__(self):
        return self.name
    
    class Meta:
        database = database_proxy
        order_by = ('name',)
        
class Mynetwork(Model):
    
    value = CharField(unique=True, index=True)

    def _clean(self):
        validators.clean_ip_address_or_network(self.value, field_name="value", error_class=ValidationError)
    
    def save(self, force_insert=False, only=None, validate=True):
        if validate:
            self._clean()
        return Model.save(self, force_insert=force_insert, only=only)
    
    @classmethod
    def search(cls, protocol):
        client_address = protocol['client_address']
        return search_mynetwork(client_address, 
                              objects=cls.select())

    def __unicode__(self):
        return self.value    

    class Meta:
        database = database_proxy
        order_by = ('value',)


class BaseSearchField(Model):
    
    _valid_fields = []
    _cache_key = None

    value = CharField(unique=True, max_length=255, index=True)

    @classmethod
    def search(cls, protocol, cache_enable=True, return_instance=False):
        
        return generic_search(protocol=protocol, 
                              objects=cls.select().order_by('field_name'), 
                              valid_fields=cls._valid_fields, 
                              cache_key=cls._cache_key, 
                              cache_enable=cache_enable, 
                              return_instance=return_instance)

    def _clean(self):

        #TODO: helo_name and country validators

        if self.field_name == "client_address":
            validators.clean_ip_address_or_network(self.value, field_name="value", error_class=ValidationError)

        elif self.field_name == "client_name" and not "*" in self.value:
            validators.clean_hostname(self.value, field_name="value", error_class=ValidationError)
        
        elif self.field_name in ["sender", "recipient"]:
            if not "*" in self.value:
                validators.clean_email_or_domain(self.value, field_name="value", error_class=ValidationError)
            pass
        
    def save(self, force_insert=False, only=None, validate=True):
        if validate:
            self._clean()
        return Model.save(self, force_insert=force_insert, only=only)

    class Meta:
        database = database_proxy

class Policy(BaseSearchField):

    _valid_fields = ['country', 'client_address', 'client_name', 'sender', 'recipient', 'helo_name']
    _cache_key = 'greypolicy'
    
    name = CharField(unique=True, max_length=20)
    
    #value_type = IntegerField(choices=constants.POLICY_TYPE, default=constants.POLICY_TYPE_COUNTRY)
    field_name = CharField(choices=constants.POLICY_FIELDS, default='client_address')
    
    mynetwork_vrfy = BooleanField(default=True)

    domain_vrfy = BooleanField(default=True)

    spoofing_enable = BooleanField(default=True)

    greylist_enable = BooleanField(default=True)
    
    greylist_key = IntegerField(choices=constants.GREY_KEY, default=constants.GREY_KEY_MED)
    
    greylist_remaining = IntegerField(default=10)#, min_value=1)

    greylist_expire = IntegerField(default=35*86400)#s, min_value=1)
    
    comments = CharField(max_length=100, null=True)
    
    @classmethod
    def search(cls, protocol, cache_enable=True):
        return BaseSearchField.search(cls, protocol, cache_enable=cache_enable, return_instance=True)

    class Meta:
        #database = database_proxy
        order_by = ('name',)

    def __unicode__(self):
        return self.name    

class GreylistEntry(Model):
    
    key = CharField(index=True)
    
    timestamp = DateTimeFieldExtend(default=utils.utcnow)
    
    expire_time = DateTimeFieldExtend(null=True)
    
    rejects = IntegerField(default=0)
    
    accepts = IntegerField(default=0)
    
    last_state = DateTimeFieldExtend(null=True)
    
    delay = FloatField(default=0.0)
    
    #protocol = fields.DictField()
    protocol = TextField()
    
    policy = CharField(max_length=20, default='policy')

    def accept(self, now=None, expire=35*86400):
        now = now or utils.utcnow()
        self.accepts += 1
        self.last_state = now
        
        if self.accepts == 1:
            value = now - self.timestamp 
            self.delay = round(value.total_seconds(), 2)
            
        if not self.expire_time:
            self.expire_time = now + datetime.timedelta(seconds=expire)
            
        self.save()

    def reject(self, now=None):
        now = now or utils.utcnow()
        self.rejects += 1
        self.last_state = now
        self.save()

    def expire(self, delta=60, now=None):
        now = now or utils.utcnow()
        expire_date = self.timestamp + datetime.timedelta(seconds=delta)
        value = expire_date - now 
        return round(value.total_seconds(), 2)

    @classmethod
    def create_entry(cls, key=None, protocol=None, policy='default', timestamp=None, last_state=None, now=None, **kwargs):        
        now = now or utils.utcnow()
        datas = json.dumps(protocol)

        with database_proxy.transaction():
            return cls.create(key=key, 
                              rejects=1,
                              timestamp=timestamp or now,
                              last_state=last_state or now,
                              policy=policy,
                              protocol=datas,
                              **kwargs)

    @classmethod
    def search_entry(cls, key=None, now=None):
        """
        expire_time is None or greater than or equal to now AND key == key
        """
        now = now or utils.utcnow()
        
        try:
            return cls.select().where(
                    ((cls.expire_time==None) | (cls.expire_time>now)) & (cls.key==key)).get()
        except:
            pass
        
    @classmethod
    def last_metrics(cls):
        last_24_hours = arrow.utcnow().replace(hours=-24).datetime
        
        objects = cls.select().where(cls.timestamp >= last_24_hours)

        last_1_hour = arrow.utcnow().replace(hours=-1).datetime
        
        metrics = {
            'count': objects.count(),
            'accepted': cls.select(fn.Sum(cls.accepts)).where(cls.timestamp >= last_24_hours),
            'rejected': cls.select(fn.Sum(cls.rejects)).where(cls.timestamp >= last_24_hours),
            'delay': cls.select(fn.Avg(cls.delay)).where(cls.timestamp >= last_24_hours, cls.accepts>=0, cls.delay>=0),
            'abandoned': objects.filter(cls.accepts==0, cls.timestamp<=last_1_hour).count(),
            #'count_accepts': objects.filter(accepts__gte=1).count(),
        }
        
        metrics['requests'] = metrics['accepted'] + metrics['rejected']
        
        return metrics
    

        
    def __unicode__(self):
        return self.key

    class Meta:
        database = database_proxy
        order_by = ('-timestamp',)

class GreylistMetric(Model):

    timestamp = DateTimeFieldExtend(default=utils.utcnow)
    
    count = IntegerField(default=0)

    accepted = IntegerField(default=0)

    rejected = IntegerField(default=0)

    requests = IntegerField(default=0)

    abandoned = IntegerField(default=0)

    delay = FloatField(default=0.0)

    class Meta:
        database = database_proxy
        order_by = ('-timestamp',)

class WhiteList(BaseSearchField):

    _valid_fields = ['country', 'client_address', 'client_name', 'sender', 'recipient', 'helo_name']
    _cache_key = 'wlist'

    #value_type = IntegerField(choices=constants.WL_TYPE, default=constants.WL_TYPE_IP)
    field_name = CharField(choices=constants.WL_FIELDS, default='client_address')
    
    comments = CharField(max_length=100, null=True)

    class Meta:
        database = database_proxy
        order_by = ('value',)

class BlackList(BaseSearchField):

    _valid_fields = ['country', 'client_address', 'client_name', 'sender', 'recipient', 'helo_name']
    _cache_key = 'blist'

    field_name = CharField(choices=constants.BL_FIELDS, default='client_address')
    
    comments = CharField(max_length=100, null=True)

    class Meta:
        database = database_proxy
        order_by = ('value',)

        
def query_for_purge():
    
    cls = GreylistEntry
    
    last_24_hours = arrow.utcnow().replace(hours=-24).datetime
    
    #pp(query.to_query(GreylistEntry))
    query = (((cls.expire_time!=None) & (cls.expire_time<utils.utcnow())) | ((cls.expire_time==None) & (cls.timestamp<=last_24_hours)))
    
    return GreylistEntry.delete().where(query)
        


def connect(url, **options):

    """
    sqlite:///:memory:
    sqlite:////this/is/absolute.path
    
    TODO: postgresql://localhost/db1?option=..
    TODO: mysql://localhost/db1?option=..
    
    """
    
    from peewee import SqliteDatabase
    
    schemes = {
        #'apsw': APSWDatabase,
        #'berkeleydb': BerkeleyDatabase,
        #'mysql': MySQLDatabase,
        #'postgres': PostgresqlDatabase,
        #'postgresql': PostgresqlDatabase,
        #'postgresext': PostgresqlExtDatabase,
        #'postgresqlext': PostgresqlExtDatabase,
        'sqlite': SqliteDatabase,
        #'sqliteext': SqliteExtDatabase,
    }
    if HAVE_PSYCOPG2:
        schemes['postgres'] = PostgresqlDatabase
        schemes['postgresql'] = PostgresqlDatabase

    if HAVE_MYSQL:
        schemes['mysql'] = MySQLDatabase
    
    from urlparse import urlparse
    parsed = urlparse(url)
    database_class = schemes.get(parsed.scheme)
    
    if database_class is None:
        if database_class in schemes:
            raise RuntimeError('Attempted to use "%s" but a required library '
                               'could not be imported.' % parsed.scheme)
        else:
            raise RuntimeError('Unrecognized or unsupported scheme: "%s".' %
                               parsed.scheme)

    options['database'] = parsed.path[1:]
    if parsed.username:
        options['user'] = parsed.username
    if parsed.password:
        options['password'] = parsed.password
    if parsed.hostname:
        options['host'] = parsed.hostname
    if parsed.port:
        options['port'] = parsed.port

    try:
    # Adjust parameters for MySQL.
        if database_class is MySQLDatabase and 'password' in options:
            options['passwd'] = options.pop('password')
    except:
        pass

    return database_class(**options)

def configure_peewee(db_name='sqlite:///:memory:', db_options=None, drop_before=False):
    
    from peewee import create_model_tables, drop_model_tables
    
    db_options = db_options or {}

    database = connect(db_name, **db_options)
    database_proxy.initialize(database)

    tables = [Domain,
              Mynetwork,
              Policy, 
              GreylistEntry, 
              GreylistMetric, 
              WhiteList, 
              BlackList]
    if drop_before:
        drop_model_tables(tables, fail_silently=True)

    create_model_tables(tables, fail_silently=True)
