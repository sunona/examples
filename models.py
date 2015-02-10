# -*- coding: utf-8 -*-
import datetime
import os
import re
from decimal import Decimal, ROUND_HALF_UP
import uuid

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from django.db import models
from django.db.models import Q 
from sorl.thumbnail.shortcuts import get_thumbnail
from django.db.models.signals import post_save, pre_save, \
                                     pre_delete, post_delete
from django.utils.translation import get_language, ugettext_lazy as _
from pytils.translit import translify

from airlines.models import Airline
from companies.models import Contragent, Company
from destination_stations.models import Airport
from exchange.models import Exchange
from hotels.managers import PeriodManager, HotelSupplierManager
from regions.models import Resort, Country, Area
from soapapp.models import CountryTourChange
from user_catalog.models import UserArea, UserResort
from userprofiles.models import Profile
from languages.models import Language



    
    
############################
# Отель     


class HotelStars(models.Model):
    title = models.CharField(_('title'), max_length=255)
    published = models.BooleanField(default=False)
    stars = models.SmallIntegerField()

    class Meta:
        verbose_name = _('hotel stars')
        verbose_name_plural = _('hotel stars')
        ordering = ['title']

    def __unicode__(self):
        return self.title


class Hotel(models.Model):
    title = models.CharField(_('title'), max_length=255)
    fax = models.CharField(_('fax'), max_length=100, blank=True,null=True)
    phone = models.CharField(_('phone'), max_length=100, blank=True,null=True)
    corona_id = models.IntegerField(_('id on corona.travel site'), default=0)
    resort = models.ForeignKey(Resort, verbose_name=_('resort'))
    user_resort = models.ForeignKey(UserResort, null=True, blank=True)
    area = models.ForeignKey(Area, verbose_name=_('area'), null=True, blank=True)
    user_area = models.ForeignKey(UserArea, null=True, blank=True)
    stars = models.ForeignKey(HotelStars, verbose_name=_('stars'),
                              null=True, blank=True)
    checkin = models.TimeField(null=True, blank=True)
    checkout = models.TimeField(null=True, blank=True)
    country = models.ForeignKey(Country)

    last_change = models.DateTimeField(null=True, auto_now=True)

    company = models.ForeignKey(Company, null=True, blank=True)
    user = models.ForeignKey(Profile, null=True)
    hidden = models.BooleanField(default=False)
    
    longitude = models.DecimalField(_(u'Долгота'),max_digits=24, decimal_places=15, null=True, blank=True)
    latitude = models.DecimalField(_(u'Широта'),max_digits=24, decimal_places=15, null=True, blank=True)
   
    # Компания (сам отель если он имеет личный кабинет) назначенная 
    # в качестве официального поставщика описаний, цен, комнат и т.д.
    # Это значит что к примеру CВОЙСТВА ОТЕЛЯ И КОМНАТ и т.д. заведенные таким отелем
    # являются приоритетными и показываются ВМЕСТО значений переданных
    # по цепи.
    company_official_supplier = models.ForeignKey(Company,null=True, related_name='hotel_official_supplier_set')
    is_closed = models.BooleanField(default=False)
    deleted_hotel = models.BooleanField(default=False)
    not_in_booking = models.BooleanField(default=False) 
    
    class Meta:
        verbose_name = _('hotel')
        verbose_name_plural = _('hotels')
        ordering = ('title',)
        permissions = (('profile_publish_hotel_price', 'profile publish hotel prices'),)

    def __unicode__(self):
        return self.title

    def get_resort(self):
        return self.resort

    def get_area(self):
        return self.area

    def can_approve(self):
        if self.hidden:
            return False
        if not self.company:
            return False
        if not self.user_area:
            if self.resort:
                return True
        else:
            if self.area and self.resort:
                return True
        return False

    def get_resort(self):
        if self.resort:
            return self.resort
        else:
            return self.user_resort

    def get_area(self):
        if self.area:
            return self.area
        else:
            return self.user_area

    def has_partner_rate_codes(self, own_company):
        from rate_codes.models import RateCode
        qs = RateCode.objects.filter(
            shared_companies=own_company,
            hotelsupplierratecode__hotel_supplier__hotel=self)
        return qs.exists()
        
    def get_children(self):
        return self._default_manager.filter(parent=self)


from hotels.signals import set_hotel_country
pre_save.connect(set_hotel_country, sender=Hotel)
   

class HotelDescription(models.Model):
    hotel = models.ForeignKey(Hotel)
    language = models.ForeignKey(Language)
    company = models.ForeignKey(Company)
    text = models.CharField(max_length=4000)
    def __unicode__(self):
        return u'%s' % (self.text)
    class Meta:
        unique_together = ('language','hotel','company')
        verbose_name = _(u'Описание отеля')
        verbose_name_plural = _(u'Описание отелей')

 
HOTEL_FEAUTURES_TYPE_CHOICES = (
    ('base', _(u'Base')), 
    ('general', _(u'General')), 
    ('activities', _(u'Activities')), 
    ('services', _(u'Services')), 
    ('spa', _(u'Spa')),
    ('conference', _(u'Conference')),
    ('beach', _(u'Beach')),
  )
     
          
HOTEL_FEAUTURES_DATA_TYPE = (
    ('integer','Integer'),   
    ('float', 'Float'),
    ('text','Text'),
    ('date','Date'),
    ('boolean','Boolean'),
    ('choice','Choice'),
    ('multiplechoice','MultipleChoice'),   
    ('ftandmetr','Foot and Metr (convertable)'),  
    ('ftandmetrsquare','Foot and Metr square (convertable)'),
  )


class HotelFeature(models.Model):
    feature_type = models.CharField(max_length=255, choices=HOTEL_FEAUTURES_TYPE_CHOICES)
    data_type = models.CharField(max_length=255, choices=HOTEL_FEAUTURES_DATA_TYPE)
    text = models.CharField(max_length=255)
    choice_text = models.CharField(_(u'Для типов данных Choice и MultipleChoice значения через ;'), max_length=2000, blank=True,null=True) # for choice field
    def __unicode__(self):
        return u'%s' % (self.text)  
    class Meta:
        verbose_name = _(u'Сервис в отеле')
        verbose_name_plural = _(u'Сервисы в отеле')

                           
class HotelFeatureLang(models.Model):
    hotel_feature = models.ForeignKey(HotelFeature)
    language = models.ForeignKey(Language)
    text = models.CharField(max_length=255) 
    choice_text = models.CharField(_(u'Для типов данных Choice и MultipleChoice значения через ;'), max_length=2000, blank=True,null=True) # for choice field 
    def __unicode__(self):
        return u'%s' % (self.text)
    class Meta:
        verbose_name = _(u'Используемый язык в сервисе отеля')
        verbose_name_plural = _(u'Используемые языки в сервисе отеля') 
        
        
class HotelFeatureCompany(models.Model):
    # Свойства отелей уникальные для каждой компании 
    hotel_feature = models.ManyToManyField(HotelFeature, through="HotelFeatureCompanySpecific")
    hotel = models.ForeignKey(Hotel, verbose_name=_('hotel'))
    company = models.ForeignKey(Company, null=True)    
    def __unicode__(self):
        return u'%s - %s' % (self.hotel, self.company)
    class Meta:
        verbose_name = _(u'Сервис для каждой из компаний в отеле')
        verbose_name_plural = _(u'Сервисы для каждой из компаний в отеле') 
        unique_together = ("hotel", "company")
            
               
class HotelFeatureCompanySpecific(models.Model):
    hotel_feature = models.ForeignKey(HotelFeature)
    hotel_feature_company = models.ForeignKey(HotelFeatureCompany)
    text = models.CharField(max_length=1000, null=True, blank=True)
    choice_text = models.CharField(_(u'Для типов данных Choice и MultipleChoice значения через ;'), max_length=2000, null=True) 
    def __unicode__(self):
        return u'%s - %s' % (self.hotel_feature, self.hotel_feature_company.company)  
    class Meta:
        verbose_name = _(u'Спецификация сервиса в отеле')
        verbose_name_plural = _(u'Спецификация сервисов в отеле')    
        unique_together = ("hotel_feature", "hotel_feature_company")       

        
def get_file_path(instance, filename):
    company_name = u'%s' % instance.company
    file_name = filename.split('.')[0]
    file_name_trans = '%s' % (translify(file_name))    
    file_ext = filename.split('.')[-1]
    filename = "%s - %s.%s" % (company_name, file_name_trans, file_ext)
    return os.path.join('upload/hotel_files', filename)
    
        
class HotelFile(models.Model):
    hotel = models.ForeignKey(Hotel)
    company = models.ForeignKey(Company, verbose_name=_(u'Компания'))   
    file_path = models.FileField(upload_to=get_file_path, verbose_name=_(u'Файл компании')) 
    
    class Meta:
        verbose_name = _(u'Файлы отеля.')
        verbose_name_plural = _(u'Файлы отеля.')
        ordering = ['-id']             
   
    def __unicode__(self):
        return u'%s' % self.file_path  
    
    def get_file_name(self):
        file_path = '%s' % self.file_path
        return file_path.replace('upload/hotel_files/','')         
    
    def get_description_on_current_language(self):    
        language_code = get_language()
        language = Language.objects.get(code=language_code)
        try:
            description = u'%s' % self.hotelfiledescriptionlang_set.filter(language=language)[0] 
        except Exception,e:
            try:
                description = u'%s' % self.hotelfiledescriptionlang_set.filter(language=41)[0]
            except:
                description = None     
        return description 
         
                   
class HotelFileDescriptionLang(models.Model):
    hotel_file = models.ForeignKey(HotelFile)
    language = models.ForeignKey(Language) 
    description = models.CharField(max_length=255, blank = True, null=True) 
    class Meta:
        verbose_name = _(u'Описание файла отеля.')
        verbose_name_plural = _(u'Описание файла отеля.')
        ordering = ['-id']             
    def __unicode__(self):
        return u'%s' % self.description  
        
                                       
# конец Отель 
############################




############################ 
# Комната 

class CompanyRoomParams(models.Model):
    hotel = models.ForeignKey(Hotel, verbose_name=_('hotel'))
    company = models.ForeignKey(Company, verbose_name=_('company'))
    room_orders = models.CharField(max_length=100)
    
    class Meta :
        unique_together = (('hotel', 'company'),)
        
    def __unicode__(self):
        return self.room_orders

    def set_room_order(self, room_orders):
        """ set room_orders attr from self.get_room_order() """
        orders = []
        self.room_orders = ';'.join(['%d-%d' % \
            (item[0], item[1]) for item in room_orders.items()])

    def get_room_order(self):
        """ return dict. for each item key is room id, value is room order  """
        orders = {}
        for item in self.room_orders.split(';'):
            if item:
                order = item.split('-')
                orders[int(order[0])] = int(order[1])
        return orders

CALCULATION_METHOD_CHOICES = ((0, 'Per Room'), (1, 'Per Person'),)

class Room(models.Model):
    title = models.CharField(_('title'), max_length=255)
    corona_id = models.IntegerField(_('id on corona.travel site'), default=0)
    max_pax = models.PositiveIntegerField(_('maximum pax'), null=True)
    hotel = models.ForeignKey(Hotel, verbose_name=_('hotel'))
    calculation_method = models.PositiveSmallIntegerField(
        choices=CALCULATION_METHOD_CHOICES, default=0)

    company = models.ForeignKey(Company, null=True)
    user = models.ForeignKey(Profile, null=True)
    price_range = models.PositiveIntegerField(null=True) # сортировка по цене для калька

    # Показывает минимальную группу, которая может жить в номере
    # без взрослых, а также задает рамки минимального возраста
    # для проживания в данном номере 
    min_age_group = models.CharField(blank=True, null=True, max_length=4)
    
    # Отображает максимальное количество определенных возрастных групп
    # которые могут в этом номере
    # 3x3 or 2x3+1x2+1x1, т.е. 3 человека 3 возрастной группы (имеется
    # ввиду ChildPolicy) или 2 человека 3 возрастной группы + один человек
    # второй возрастной группы и один человек первой возрастной группы 
    occupancy = models.CharField(blank=True, null=True, max_length=255)
    
    class Meta:
        verbose_name = _('room')
        verbose_name_plural = _('rooms')
        ordering = ('title',)

    def __unicode__(self):
        return self.title

    def calc_per_room(self):
        return self.calculation_method == 0

    def calc_per_person(self):
        return self.calculation_method == 1


class RoomDescription(models.Model):
    room = models.ForeignKey(Room)
    language = models.ForeignKey(Language)
    company = models.ForeignKey(Company)
    text = models.CharField(max_length=4000)
    def __unicode__(self):
        return u'%s' % (self.text)
    class Meta:
        unique_together = ('language','room','company')
        verbose_name = _(u'Описание комнаты')
        verbose_name_plural = _(u'Описание комнат')

ROOM_FEAUTURES_TYPE_CHOICES = (
    ('base', _(u'Base')), 
    ('general', _(u'General')),
    ('bedroom', _(u'Bedroom')),
    ('bathroom', _(u'Bathroom')), 
  )

ROOM_FEAUTURES_DATA_TYPE = (
    ('integer','Integer'),   
    ('float', 'Float'),
    ('text','Text'),
    ('date','Date'),
    ('boolean','Boolean'),
    ('choice','Choice'),
    ('multiplechoice','MultipleChoice'),   
    ('ftandmetr','Foot and Metr (convertable)'),
    ('ftandmetrsquare','Foot and Metr square (convertable)'),      
  )


class RoomFeature(models.Model):
    feature_type = models.CharField(max_length=255, choices=ROOM_FEAUTURES_TYPE_CHOICES)
    data_type = models.CharField(max_length=255, choices=ROOM_FEAUTURES_DATA_TYPE)
    text = models.CharField(max_length=255)
    choice_text = models.CharField(_(u'Для типов данных Choice и MultipleChoice значения через ;'), max_length=2000, blank=True,null=True) # for choice field
    def __unicode__(self):
        return u'%s' % (self.text)  
    class Meta:
        verbose_name = _(u'Сервис в комнате')
        verbose_name_plural = _(u'Сервисы в комнате')
           
                    
class RoomFeatureLang(models.Model):
    room_feature = models.ForeignKey(RoomFeature)
    language = models.ForeignKey(Language)
    text = models.CharField(max_length=255) 
    choice_text = models.CharField(_(u'Для типов данных Choice и MultipleChoice значения через ;'), max_length=2000, blank=True,null=True) # for choice field 
    def __unicode__(self):
        return u'%s' % (self.text)
    class Meta:
        verbose_name = _(u'Используемый язык в сервисе комнаты')
        verbose_name_plural = _(u'Используемые языки в сервисе комнаты') 
        
        
class RoomFeatureCompany(models.Model):
    # Свойства комнат уникальные для каждой компании 
    room_feature = models.ManyToManyField(RoomFeature, through="RoomFeatureCompanySpecific")
    room = models.ForeignKey(Room, verbose_name=_('room'))
    company = models.ForeignKey(Company, null=True)    
    def __unicode__(self):
        return u'%s - %s' % (self.room, self.company)
    class Meta:
        verbose_name = _(u'Сервис для каждой из компаний в комнате')
        verbose_name_plural = _(u'Сервисы для каждой из компаний в комнате') 
        unique_together = ("room", "company")
             
               
class RoomFeatureCompanySpecific(models.Model):
    room_feature = models.ForeignKey(RoomFeature)
    room_feature_company = models.ForeignKey(RoomFeatureCompany)
    text = models.CharField(max_length=1000, null=True, blank=True)
    choice_text = models.CharField(_(u'Для типов данных Choice и MultipleChoice значения через ;'), max_length=2000, null=True) 
    def __unicode__(self):
        return u'%s - %s' % (self.room_feature, self.room_feature_company.company)  
    class Meta:
        verbose_name = _(u'Спецификация сервиса в комнате')
        verbose_name_plural = _(u'Спецификация сервисов в комнате')    
        unique_together = ("room_feature", "room_feature_company") 

# конец Комнаты    
############################ 


############################
### Рестораны и бары

RESTAURANT_OR_BAR_CHOICES = (
  ('restaurant', _('Restaurant')),
  ('bar', _('Bar')),
)

class RestaurantAndBar(models.Model):
    title = models.CharField('title', max_length=255)
    restaurant_or_bar = models.CharField('restaurant or bar', max_length=255, choices=RESTAURANT_OR_BAR_CHOICES)
    hotel = models.ForeignKey(Hotel)
    company = models.ForeignKey(Company)
    def __unicode__(self):
        return u'%s' % (self.title)
    class Meta:
        verbose_name = _(u'Рестораны и бары для компании')
        verbose_name_plural = _(u'Рестораны и бары для компании')    
                              
RESTAURANT_AND_BAR_FEATURES_DATA_TYPE = (
    ('integer','Integer'),   
    ('float', 'Float'),
    ('text','Text'),
    ('date','Date'),
    ('boolean','Boolean'),
    ('choice','Choice'),
    ('multiplechoice','MultipleChoice'),   
    ('ftandmetr','Foot and Metr (convertable)'),  
    ('ftandmetrsquare','Foot and Metr square (convertable)'),
  )


class RestaurantAndBarFeature(models.Model):
    data_type = models.CharField(max_length=255, choices=RESTAURANT_AND_BAR_FEATURES_DATA_TYPE)
    text = models.CharField(max_length=255)
    choice_text = models.CharField(_(u'Для типов данных Choice и MultipleChoice значения через ;'), max_length=2000, blank=True,null=True) # for choice field
    def __unicode__(self):
        return u'%s' % (self.text)  
    class Meta:
        verbose_name = _(u'Сервис в ресторане или баре')
        verbose_name_plural = _(u'Сервисы в ресторане или баре')    


class RestaurantAndBarFeatureLang(models.Model):
    restaurant_and_bar_feature = models.ForeignKey(RestaurantAndBarFeature)
    language = models.ForeignKey(Language)
    text = models.CharField(max_length=255) 
    choice_text = models.CharField(_(u'Для типов данных Choice и MultipleChoice значения через ;'), max_length=2000, blank=True,null=True) # for choice field 
    def __unicode__(self):
        return u'%s' % (self.text)
    class Meta:
        verbose_name = _(u'Используемый язык в сервисе ресторана')
        verbose_name_plural = _(u'Используемые языки в сервисе ресторана')


class RestaurantAndBarFeatureCompany(models.Model):
    # Свойства ресторана или бара уникальные для каждой компании 
    restaurant_and_bar_feature = models.ManyToManyField(RestaurantAndBarFeature, through="RestaurantAndBarFeatureCompanySpecific")
    restaurant_and_bar = models.ForeignKey(RestaurantAndBar, verbose_name=_('restaurant_and_bar'))
    company = models.ForeignKey(Company, null=True)    
    def __unicode__(self):
        return u'%s - %s' % (self.restaurant_and_bar, self.company)
    class Meta:
        verbose_name = _(u'Сервис для каждой из компаний в ресторане или баре')
        verbose_name_plural = _(u'Сервисы для каждой из компаний в ресторане или баре') 
        unique_together = ("restaurant_and_bar", "company")    


class RestaurantAndBarFeatureCompanySpecific(models.Model):
    restaurant_and_bar_feature = models.ForeignKey(RestaurantAndBarFeature)
    restaurant_and_bar_feature_company = models.ForeignKey(RestaurantAndBarFeatureCompany)
    text = models.CharField(max_length=1000, null=True, blank=True)
    choice_text = models.CharField(_(u'Для типов данных Choice и MultipleChoice значения через ;'), max_length=2000, null=True) 
    def __unicode__(self):
        return u'%s - %s' % (self.restaurant_and_bar_feature, self.restaurant_and_bar_feature_company.company)  
    class Meta:
        verbose_name = _(u'Спецификация сервиса в ресторане или баре')
        verbose_name_plural = _(u'Спецификация сервисов в ресторане или баре')    
        unique_together = ("restaurant_and_bar_feature", "restaurant_and_bar_feature_company")

### Конец Рестораны и бары
############################


############################
# Фотографии   
 
def get_hotel_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    filename = "%s.%s" % (uuid.uuid4(), ext)
    return os.path.join('upload/hotel_photo', filename) 
 
 
class HotelPhoto(models.Model):        
    hotel = models.ForeignKey(Hotel)
    company = models.ForeignKey(Company)
    photo = models.ImageField(upload_to=get_hotel_photo_path)
    room = models.ForeignKey(Room, null=True,blank=True)
    is_plan = models.BooleanField(default=False) # план комнаты или отеля
    public = models.BooleanField(default=False) # публичное фото от компании официального поставщика, которое будет отображено у всех поставщиков
    def __unicode__(self):
        return u'%s' % self.photo 
        
    class Meta:
        verbose_name = _(u'Фотография отеля')
        verbose_name_plural = _(u'Фотографии отеля')
        ordering = ['company']
    
   
    def get_photo_html(self):
        if self.photo:
            img = self.photo
            
            try:
                img_resize_url = get_thumbnail(img, '100x100').url
            except:
                img = 'no_photo.png'
                img_resize_url = get_thumbnail(img, '100x100').url                
        else:
            img = 'no_photo.png'
            img_resize_url = get_thumbnail(img, '100x100').url
        img = 'no_photo.png'   
        html = '<img src="%s">' % img_resize_url
        return html
                              
    get_photo_html.short_description = _(u'Photo')
    get_photo_html.allow_tags = True

    
class HotelPhotoLang(models.Model):
    hotel_photo = models.ForeignKey(HotelPhoto)
    language = models.ForeignKey(Language)
    text = models.CharField(max_length=1000) 
    def __unicode__(self):
        return '%s' % (self.text)
    class Meta:
        verbose_name = _(u'Название фотографии')
        verbose_name_plural = _(u'Названия фотографии') 

# конец Фотографии 
############################

############################
# Видео   

class HotelVideo(models.Model):        
    hotel = models.ForeignKey(Hotel)
    company = models.ForeignKey(Company)
    video = models.CharField(_('video'), max_length=1000)
    room = models.ForeignKey(Room, null=True,blank=True)
    public = models.BooleanField(default=False) # публичное видео от компании официального поставщика, которое будет отображено у всех поставщиков 
    
    def __unicode__(self):
        return u'%s' % self.hotel.title 
        
    class Meta:
        verbose_name = _(u'Ссылка на видео отеля')
        verbose_name_plural = _(u'Ссылки на видео отеля')
        ordering = ['company']
    
class HotelVideoLang(models.Model):
    hotel_video = models.ForeignKey(HotelVideo)
    language = models.ForeignKey(Language)
    text = models.CharField(max_length=1000) 
    
    def __unicode__(self):
        return '%s' % (self.text)
    
    class Meta:
        verbose_name = _(u'Название видео')
        verbose_name_plural = _(u'Названия видео') 

# конец Видео
############################

class HotelSupplier(models.Model):
    hotel = models.ForeignKey(Hotel, verbose_name=_('hotel'))
    supplier = models.ForeignKey(Contragent, verbose_name=_('contragent'))

    meals = models.CharField(blank=True, max_length=10)
    checkin = models.TimeField(null=True, blank=True)
    checkout = models.TimeField(null=True, blank=True)
    has_room_prices = models.BooleanField(default=False)
    exchange = models.ForeignKey(Exchange, null=True, blank=True)

    company = models.ForeignKey(Company, verbose_name=_('company'))

    active = models.BooleanField(default=False)

    # for EarlyBird
    # Поле для спецпредложений - показывает источник базовых цен  
    parent = models.ForeignKey('self', null=True, blank=True)

    # for publicate
    # При публикации hotelsupplier создается копия. 
    # В actual_hotel_supplier записывается источник цен (оригинал при копировании)
    # Первый элемент цепи
    actual_hotel_supplier = models.OneToOneField('self', 
        related_name='public_version', blank=True, null=True)
    last_publicated_date = models.DateTimeField(null=True, blank=True)
    rooms = models.CharField(max_length=255, blank=True)
    
    transfer_is_must = models.BooleanField(default=False) # Если стоит True, то без выбора трансфера невозможно 
 
    objects = HotelSupplierManager()

    class Meta:
        verbose_name = _('hotel supplier')
        verbose_name_plural = _('hotel supplier')
        permissions = (
            ('profile_view_hotel_prices', 
             'can view hotel prices in public site'), 
            ('profile_add_hotel_prices', 
             'can add hotel prices in public site'), 
            ('profile_change_hotel_prices', 
             'can change hotel prices in public site'), 
            ('profile_delete_hotel_prices', 
             'can delete hotel prices in public site'),)

    def is_base(self):
        return not self.parent_id

    def get_rooms_ids(self):
        return [int(room_id) for room_id in self.rooms.split(',') if room_id]

    def may_add_prices(self):
        from hotels.models import PeriodDates
        add_price = True
        #check meal
        if not self.meal_set.count():
            add_price = False

        #check periods continuity
        periods = PeriodDates.objects.filter(period__hotel_supplier=self, 
            date_to__gte=datetime.date.today())
        if len(periods) > 1:
            first_period = periods[0]
            prev_period = first_period
            time_delta = datetime.timedelta(days=1)
            for period in periods[1:]:
                if prev_period.date_to + time_delta < period.date_from:
                    add_price = False
                prev_period = period
        if not periods:
            add_price = False
        return add_price

    def __unicode__(self):
        return str(self.pk)

    def is_actual(self):
        return not self.actual_hotel_supplier

    def in_spo(self):
        return self.spowizardhotels_set.all().exists()

    def set_country_changes(self):
        country = self.hotels.resort.country
        company = self.company
        country_change, created = CountryTourChange.objects.get_or_create(
            country=country, company=company)
        return country_change
                                    
    def is_travco(self):
        # Travco xml supplier
        if self.company.id == 717:
            return True 
        else:
            return False 
                         
    def is_mtc_group(self):
        # MTC group
        if self.company.id == 721:
            return True 
        else:
            return False

    def is_connections(self):
        # Connections xml supplier
        if self.company.id == 751:
            return True 
        else:
            return False
            
    def is_asiaworld(self):
        # Connections xml supplier
        if self.company.id == 990:
            return True 
        else:
            return False

    def is_xml(self):
        if self.is_travco() or self.is_mtc_group() or self.is_connections() and self.is_asiaworld():
            return True
        return False


from hotels.signals import delete_hotel_supplier_data
pre_delete.connect(delete_hotel_supplier_data, sender=HotelSupplier)


HISTORY_ACTION_CHOICES = (
    ('A', 'Added'),
    ('C', 'Changed'),
    ('D', 'Deleted'),
)


class HotelSupplierHistory(models.Model):
    action = models.CharField(max_length=1, choices=HISTORY_ACTION_CHOICES)
    action_date = models.DateTimeField(auto_now_add=True)
    object_repr = models.CharField(max_length=200)
    hotel_supplier = models.ForeignKey(HotelSupplier)
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    user = models.ForeignKey(Profile)
    content_object = generic.GenericForeignKey('content_type', 'object_id')

    class Meta:
        ordering = ('-action_date', )

    def __unicode__(self):
        return '%s (%s)' % (self.object_repr, self.action)


class ChildPolicy(models.Model):
    ages = models.TextField()
    hotel_supplier = models.OneToOneField(HotelSupplier)

    class Meta:
        verbose_name = _('child policy')
        verbose_name_plural = _('child policies')

    def __unicode__(self):
        return self.ages.strip(';')

    def get_ages(self):
        ages = []
        formuls = self.ages.split(';')
        formuls_re = re.compile(
                r'^([a-zA-z0-9 _\.-]+)=([0-9]+)-([0-9]+)$'
            )
        for formula in formuls:
            if formula:
                formuls_match = formuls_re.search(formula)
                ages.append({'title': formuls_match.group(1), 
                             'age_start': int(formuls_match.group(2)), 
                             'age_end': int(formuls_match.group(3))
                            }
                           )
        return ages

    def convert_ages_to_people_group(self, ages, as_list=True):
    # ages в формате list
    # Производим конвертацию данных вида [25,25,1,7,5,25] (набор возрастов)
    # в формат 1;2;3   1 младенец, 2 ребенка, 3 взрослых
     
        ages_cp = self.get_ages()
        
        # формируем заготовку people_group
        people_group = []
        for i in range(len(ages_cp)):
            people_group.append(0)

        for index, age_cp in enumerate(ages_cp):
            for age in ages:
                if age >= age_cp['age_start'] and age <= age_cp['age_end']:
                    people_group[index] += 1 

        if as_list:
            return people_group
        else:    
            people_group = ';'.join([str(i) for i in people_group])                     
            return people_group
        

from hotels.signals import delete_ages_linked_data
pre_save.connect(delete_ages_linked_data, sender=ChildPolicy)
pre_delete.connect(delete_ages_linked_data, sender=ChildPolicy)


class RoomParams(models.Model):
    max_pax = models.PositiveIntegerField(_('maximum pax'), null=True)
    room = models.ForeignKey(Room, verbose_name=_('room'))
    company = models.ForeignKey(Company, verbose_name=_('company'))
    hotel_supplier = models.ForeignKey(HotelSupplier)
    
    class Meta:
        verbose_name = _('room params')
        verbose_name_plural = _('room params')

    def __unicode__(self):
        return str(self.max_pax)

accommodation_types_r = ('R', '1R', '2R', '3R', '4R', '5R', '6R', '7R', '8R', '9R', '10R')
accommodation_types_extra = ('EB', 'RB')
accommodation_types = ('R', '1R', '2R', '3R', '4R', '5R', '6R', '7R', '8R', '9R', '10R', 'EB', 'RB')


class Accommodation(models.Model):
    all = models.PositiveIntegerField()
    age_types_count = models.CharField(max_length=255)
    formula = models.CharField(max_length=255)
    types = models.CharField(blank=True, max_length=255)
    room = models.ForeignKey(Room, verbose_name=_('room'))
    hotel_supplier = models.ForeignKey(HotelSupplier)
    parent = models.ForeignKey('self', null=True, blank=True)
    company = models.ForeignKey(Company, verbose_name=_('company'))
    
    class Meta:
        verbose_name = _('accommodation')
        verbose_name_plural = _('accommodations')
        ordering = ['hotel_supplier']

    def get_ages_count_list(self):
        ages_count_list = []
        if self.age_types_count:
            ages_count_list = self.age_types_count.strip(';').split(';')
            ages_count_list = [int(item) for item in ages_count_list]
        return ages_count_list

    def get_accommodation_types(self):
        types = self.types.strip(';').split(';')
        return types

    def get_accommodation_types_r(self):
        types = self.formula.strip(';').replace('+', ';'
            ).replace('*', ';').split(';')
        print types
        types = [type.strip() for type in types]
        types_r = []
        for type in accommodation_types_r:
            if type in types:
                types_r.append(type)
       
        return types_r

    def __unicode__(self):
        return self.formula

from hotels.signals import all_count_calculate
pre_save.connect(all_count_calculate, sender=Accommodation)


class Meal(models.Model):
    MEAL_TYPE_CHOICES = (('BB','Bad and breakfast'),
                         ('HB','Half board'),
                         ('FB','Full board'),
                         ('ALL','All inclusive'), 
                        )
    title = models.CharField(max_length=255)
    base_meal = models.BooleanField(default=False)
    hotel_supplier = models.ForeignKey(HotelSupplier)
    parent = models.ForeignKey('self', null=True, blank=True)
    active = models.BooleanField(default=True)
    type = models.CharField(choices = MEAL_TYPE_CHOICES, max_length=255, null=True)
    class Meta:
        verbose_name = _('meal')
        verbose_name_plural = _('meal')
        ordering = ('id',)

    def __unicode__(self):
        return self.title

from hotels.signals import control_base_meal
pre_save.connect(control_base_meal, sender=Meal)


SERVICE_TYPES = (
    ('-', _('-')),
    ('+', _('+')),
    ('++', _('++')),
    ('+/+', _('+/+')),
)

WEEK_DAYS = ['mo', 'tu', 'we', 
    'th', 'fr', 'sa', 'su']



class Period(models.Model):
    title = models.CharField(max_length=255)
    date_from = models.DateField()
    date_to = models.DateField()
    crushed = models.BooleanField(default=False)
    ms = models.IntegerField(default=1)
    service_type = models.CharField(max_length=3, choices=SERVICE_TYPES, 
                                    default='-')
    parts = models.CharField(max_length=25, blank=True)
    base_meal = models.ForeignKey(Meal, null=True, blank=True)
    base_meals = models.TextField(blank=True)
    commission = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    commission_request = models.BooleanField(default=False)
    hotel_supplier = models.ForeignKey(HotelSupplier)

    #for F
    f_rates = models.CharField(max_length=100, blank=True)
    f_exchange = models.ForeignKey(Exchange,
                                   related_name='period_f', 
                                   null=True, blank=True)
    
    parent = models.ForeignKey('self', null=True, blank=True)

    objects = PeriodManager()

    class Meta:
        verbose_name = _('period')
        verbose_name_plural = _('periods')
        ordering = ['date_from']


    def __unicode__(self):
        return self.title

    def get_base_meals(self):
        """ return dict. for each item key is room id, value is meal id """
        base_meals = {}
        for pair_str in self.base_meals.split(';'):
            pair = pair_str.split('-')
            if len(pair) == 2:
                room_id = int(pair[0])
                meal_id = int(pair[1])
                base_meals[room_id] = meal_id
        return base_meals


    def set_base_meals(self, base_meals):
        """ set base_meals attribute from base_meals dict. 
            base_meals dict is in self.get_base_meals() format  """

        self.base_meals = u';'.join([u'%d-%d' % (item[0], item[1]) \
                                     for item in base_meals.items()])
        return self.base_meals


    def get_base_meal_for_room(self, room):
        """ return base meal id for room """
        base_meals = self.get_base_meals()
        if isinstance(room, Room):
            return base_meals.get(room.pk, self.base_meal_id)
        if isinstance(room, int):
            return base_meals.get(room, self.base_meal_id)


    def get_rates_eb_for_room(self, room):
        from hotels.models import ExtraBedRate
        try:
            extra_bed_rate = ExtraBedRate.objects.select_related('exchange'
                ).get(period=self, room=room, type=u'E')
        except ExtraBedRate.DoesNotExist:
            return None
        return extra_bed_rate


    def get_rates_rb_for_room(self, room):
        from hotels.models import ExtraBedRate
        try:
            extra_bed_rate = ExtraBedRate.objects.select_related('exchange'
                ).get(period=self, room=room, type=u'R')
        except ExtraBedRate.DoesNotExist:
            return None
        return extra_bed_rate


    def get_all_week_days(self):
        all_week_days = []
        parts = self.parts.replace(' ', '').lower()
        for week_days in parts.split(';'):
            for week_day in week_days.split('+'):
                all_week_days.append(week_day)
        return all_week_days

    def get_parts(self):
        parts = self.parts.replace(' ', '').lower()
        return [part for part in parts.split(';') if part]

    def get_full_parts(self):
        week_days_all = ['mo', 'tu', 'we', 
                         'th', 'fr', 'sa', 'su'
                        ]

        parts = self.get_parts()
        for part in parts:
            for week_day in part.split('+'):
                week_days_all.remove(week_day)

        return ['BASE: %s' % '+'.join(week_days_all)] + parts


    def get_calc_parts(self):
        week_days_all = ['mo', 'tu', 'we', 
            'th', 'fr', 'sa', 'su']

        parts = self.get_parts()
        for part in parts:
            for week_day in part.split('+'):
                week_days_all.remove(week_day)

        return ['%s' % '+'.join(week_days_all)] + parts


    def set_new_parts(self, week_days):
        old_parts = self.get_parts()
        new_part = '+'.join(week_days)
        old_parts.append(new_part)
        self.parts = ';'.join(old_parts)

    def get_rates_f(self):
        if self.f_exchange_id:
            return [Decimal(rate) for rate in self.f_rates.split(';') if rate]
        else:
            return Decimal(self.f_rates)

    def get_rates_f_type(self):
        if self.f_exchange_id:
            return 'abs'
        else:
            return '%'


from hotels.signals import delete_period_data
pre_delete.connect(delete_period_data, sender=Period)
            

class PeriodDates(models.Model):
    date_from = models.DateField()
    date_to = models.DateField()

    period = models.ForeignKey(Period, verbose_name=_('period'))

    class Meta:
        verbose_name = _('period dates')
        verbose_name_plural = _('period dates')
        ordering = ['date_from']


from hotels.signals import set_period_dates, set_perioddates_crosses, \
                           delete_empty_periods
post_save.connect(set_period_dates, sender=PeriodDates)
pre_save.connect(set_perioddates_crosses, sender=PeriodDates)
post_delete.connect(delete_empty_periods, sender=PeriodDates)
        

SERVICE_TYPE_CHOICES = (
    ('pp', _('per person')),
    ('pr', _('per room')),
)

SERVICE_TYPE_CHOICES2 = (
    ('AND', _('AND')),
    ('OR', _('OR')),
)

PAY_TYPE_CHOICES = (
    ('D', _('Per Day')),
    ('A', _('On Arrival')),
)

class Service(models.Model):
    day_type = models.CharField(max_length=3, 
                                choices=SERVICE_TYPE_CHOICES2, 
                                default='AND')
    related_services = models.ManyToManyField('self', symmetrical=False, 
                                              blank=True)
    type = models.CharField(max_length=3, 
                            choices=SERVICE_TYPE_CHOICES2, 
                            default='AND')
    title = models.CharField(max_length=255)
    date = models.DateField(null=True, blank=True)
    pay_type = models.CharField(choices=PAY_TYPE_CHOICES, blank=True, max_length=1)
    per_type = models.CharField(max_length=2, choices=SERVICE_TYPE_CHOICES, 
                                default='pp')
    period = models.ForeignKey(Period, verbose_name=_('period'), 
                               null=True, blank=True)
    hotel_supplier = models.ForeignKey(HotelSupplier, null=True, blank=True)

    rates = models.CharField(max_length=255, blank=True)

    exchange = models.ForeignKey(Exchange, verbose_name=_('exchange'), 
                                 related_name='service_exchange', 
                                 null=True, blank=True)
    is_tax = models.BooleanField(default=False)

    parent = models.ForeignKey('self', null=True, blank=True, 
                               related_name='child_service_set')

    class Meta:
        verbose_name = _('service')
        verbose_name_plural = _('services')

    def __unicode__(self):
        return self.title

    def get_rates(self, hs_rate_codes=[]):
        rates = self.rates.split(';')
        decimal_rates = []
        for rate in rates:
            if rate:
                decimal_rates.append(Decimal(rate))
        if not hs_rate_codes:
            return decimal_rates
        else:
            res = []
            for rate in decimal_rates:
                for hs_rate_code in hs_rate_codes:
                    markups = hs_rate_code.get_cs_markups()
                    markup = markups['value']
                    type = markups['type']
                    if rate and markup:
                        if type == u'%':
                            rate += rate * markup / Decimal('100')
                        else:
                            rate += markup
                        if hs_rate_code.cs_commission:
                            if hs_rate_code.cs_commission_type == u'%':
                                rate -= rate * hs_rate_code.cs_commission / Decimal('100')
                            else:
                                rate -= hs_rate_code.cs_commission
                res.append(rate.quantize(Decimal('1'), ROUND_HALF_UP))
            return res


    def make_free(self):
        if self.rates:
            self.rates = ';'.join(['0' for rate in self.get_rates()])
        hotel_supplier = self.hotel_supplier or self.period.hotel_supplier
        self.rates = ';'.join(['0' for age in range(hotel_supplier.childpolicy.get_ages)])
        return self.rates


    def recalc_for_bird(self, early_bird):
        """ recalc rate depanding on early bird discount """

        if early_bird.cs_discount and early_bird.cs_expanding:
            rates_cs = self.get_rates()
            if early_bird.discount_type == 1:
                if rates_cs:
                    rates = []
                    for rate in rates_cs:
                        if early_bird.cs_discount > 0:
                            rate *= Decimal(str(early_bird.cs_discount)) / 100
                        else:
                            rate += rate * Decimal(str(early_bird.cs_discount)) / 100
                        rates.append(str(rate))
                    self.rates = u';'.join(rates)

            if early_bird.discount_type == 0:
                if rates_cs:
                    rates = []
                    for rate in rates_cs:
                        rate += Decimal(str(early_bird.cs_discount))
                        rates.append(str(rate))
                    self.rates = u';'.join(rates)
        return self.rates


class ServiceRate(models.Model):
    service = models.ForeignKey(Service)
    meal = models.ForeignKey(Meal, null=True)
    room = models.ForeignKey(Room, null=True)
    rates = models.CharField(max_length=150)
    exchange = models.ForeignKey(Exchange)

    def get_rates(self, hs_rate_codes=[]):
        rates = self.rates.split(';')
        decimal_rates = []
        for rate in rates:
            if rate:
                decimal_rates.append(Decimal(rate))
        if not hs_rate_codes:
            return decimal_rates
        else:
            res = []
            for rate in decimal_rates:
                for hs_rate_code in hs_rate_codes:
                    markups = hs_rate_code.get_cs_markups()
                    markup = markups['value']
                    type = markups['type']
                    if rate and markup:
                        if type == u'%':
                            rate += rate * markup / Decimal('100')
                        else:
                            rate += markup
                        if hs_rate_code.cs_commission:
                            if hs_rate_code.cs_commission_type == u'%':
                                rate -= rate * hs_rate_code.cs_commission / Decimal('100')
                            else:
                                rate -= hs_rate_code.cs_commission
                res.append(rate.quantize(Decimal('1'), ROUND_HALF_UP))
            return res


    def make_free(self):
        self.rates = ';'.join(['0' for rate in self.get_rates()])
        return self.rates


    def recalc_for_bird(self, early_bird):
        """ recalc rate depanding on early bird discount """

        if early_bird.cs_discount and early_bird.cs_expanding:
            rates_cs = self.get_rates()
            if early_bird.discount_type == 1:
                if rates_cs:
                    rates = []
                    for rate in rates_cs:
                        if early_bird.cs_discount > 0:
                            rate *= Decimal(str(early_bird.cs_discount)) / 100
                        else:
                            rate += rate * Decimal(str(early_bird.cs_discount)) / 100
                        rates.append(str(rate))
                    self.rates = u';'.join(rates)

            if early_bird.discount_type == 0:
                if rates_cs:
                    rates = []
                    for rate in rates_cs:
                        rate += Decimal(str(early_bird.cs_discount))
                        rates.append(str(rate))
                    self.rates = u';'.join(rates)
        return self.rates



class MealRate(models.Model):
    rates = models.CharField(max_length=255)
    exchange = models.ForeignKey(Exchange, verbose_name=_('exchange'))

    period = models.ForeignKey(Period)
    meal = models.ForeignKey(Meal, verbose_name=_('meal'))

    class Meta:
        verbose_name = _('meal rate')
        verbose_name_plural = _('meal rates')
        unique_together = ('period', 'meal')

    def __unicode__(self):
        return str(self.rates)

    def get_rates(self, hs_rate_codes=[]):
        rates = self.rates.split(';')
        if not rates:
            return None
        if not hs_rate_codes:
            return [Decimal(rate) for rate in rates]
        else:
            res = []
            for rate in [Decimal(rate) for rate in rates]:
                for hs_rate_code in hs_rate_codes:
                    markups = hs_rate_code.get_meals_markups()
                    markup = markups['value']
                    type = markups['type']
                    if rate and markup:
                        if type == u'%':
                            rate += rate * markup / Decimal('100')
                        else:
                            rate += markup
                        if hs_rate_code.meals_commission:
                            if hs_rate_code.meals_commission_type == u'%':
                                rate -= rate * hs_rate_code.meals_commission / Decimal('100')
                            else:
                                rate -= hs_rate_code.meals_commission
                res.append(rate.quantize(Decimal('1'), ROUND_HALF_UP))
            return res


    def is_more_expensive_then(self, exchange_rate, other_meal_rate, other_exchange_rate):
        """ return True if summ of rate for this rate is more then summ of other_meal_rate rate """
        this_amount = 0
        other_amount = 0
        for rate in self.get_rates():
            this_amount += rate * exchange_rate
        for rate in other_meal_rate.get_rates():
            other_amount += rate * other_exchange_rate
        return this_amount > other_amount


    def recalc_for_bird(self, early_bird):
        """ recalc rate depanding on early bird discount """
        
        if early_bird.meal_discount and early_bird.meal_expanding:
            rates_ml = self.get_rates()
            if early_bird.discount_type == 1:
                if rates_ml:
                    rates = []
                    for rate in rates_ml:
                        if early_bird.meal_discount > 0:
                            rate *= Decimal(str(early_bird.meal_discount)) / 100
                        else:
                            rate += rate * Decimal(str(early_bird.meal_discount)) / 100
                        rates.append(str(rate))
                    self.rates = u';'.join(rates)

            if early_bird.discount_type == 0:
                if rates_ml:
                    rates = []
                    for rate in rates_ml:
                        rate += Decimal(str(early_bird.meal_discount))
                        rates.append(str(rate))
                    self.rates = u';'.join(rates)
        return self.rates


    def recalc_for_combo_birds(self, early_birds):
        """ recalc rate depanding on percent early birds discounts """
        for early_bird in early_birds:
            if early_bird.price_type == 1:
                self.recalc_for_bird(early_bird)
        return self.rates


ACCOMMODATION_TYPE_CHOICES = (
    ('R', _('R')),
    ('1R', _('1R')),
    ('2R', _('2R')),
    ('3R', _('3R')),
    ('4R', _('4R')),
    ('EB', _('EB')),
    ('RB', _('RB')),
)


class RoomRate(models.Model):
    """
    Method "recalc_by_rate_codes" change "value" property of room rate
    """

    value = models.DecimalField(max_digits=10, decimal_places=2)
    room = models.ForeignKey(Room, verbose_name=_('room'))
    period = models.ForeignKey(Period, verbose_name=_('period'))
    accommodation_type = models.CharField(max_length=2, 
                                          choices=ACCOMMODATION_TYPE_CHOICES)
    period_part = models.CharField(max_length=25, blank=True)
    with_tax = models.BooleanField(default=False)

    class Meta:
        verbose_name = _('room rate')
        verbose_name_plural = _('room rates')
         


    def __unicode__(self):
        return str(self.value)


    def recalc_by_rate_code(self, hs_rate_code):
        room_markups = hs_rate_code.get_room_markups()
        room_commission = hs_rate_code.get_room_commission(self.room_id)

        #calc markup
        if self.room_id in room_markups:
            type = room_markups[self.room_id]['type']
            markup = room_markups[self.room_id]['value']
        else:
            type = hs_rate_code.markup_type
            markup = hs_rate_code.markup

        if type == u'%':
            self.value += self.value * markup / Decimal('100')
        else:
            self.value += markup

        #calc commission
        if room_commission:
            commission = room_commission['value']
            commission_type = room_commission['type']
            if commission:
                if commission_type == u'%':
                    self.value -= self.value * commission / Decimal('100')
                else:
                    self.value -= commission

        self.value = self.value.quantize(Decimal('1'), rounding=ROUND_HALF_UP)


    def recalc_by_rate_codes(self, hs_rate_codes):
        for hs_rate_code in hs_rate_codes:
            self.recalc_by_rate_code(hs_rate_code)


    def recalc_for_bird(self, early_bird):
        if early_bird.discount_type == 1:
            room_discount = early_bird.get_room_discount(self.room)
            if room_discount > 0:
                self.value *= Decimal(str(room_discount)) / 100
            else:
                self.value += \
                    self.value * Decimal(str(room_discount)) / 100
        if early_bird.discount_type == 0:
            self.value += Decimal(str(early_bird.discount))
        return self.value


    def recalc_for_combo_birds(self, early_birds):
        """ recalc rate depanding on percent early birds discounts """

        for early_bird in early_birds:
            if early_bird.price_type == 1:
                self.recalc_for_bird(early_bird)
        return self.value



EXTRA_BED_TYPE_CHOICES = (
    ('E', 'EB'),
    ('R', 'RB')
    )

class ExtraBedRate(models.Model):
    rates = models.CharField(max_length=255)
    exchange = models.ForeignKey(Exchange)
    room = models.ForeignKey(Room)
    period = models.ForeignKey(Period)
    type = models.CharField(max_length=1, choices=EXTRA_BED_TYPE_CHOICES)

    class Meta:
        verbose_name = _('extra bed rate')
        verbose_name_plural = _('extra bed rates')
        unique_together = ('room', 'period', 'type')
        ordering = ('period', )

    def __unicode__(self):
        return str(self.rates)

    def get_rates(self, hs_rate_codes=[]):
        rates = self.rates.split(';')
        if not rates:
            return None
        if not hs_rate_codes:
            return [Decimal(rate) for rate in rates]
        else:
            res = []
            for rate in [Decimal(rate) for rate in rates]:
                for hs_rate_code in hs_rate_codes:
                    markups = hs_rate_code.get_eb_markups()
                    commissions = hs_rate_code.get_eb_commission()
                    markup = markups['value']
                    type = markups['type']
                    commission = commissions['value']
                    commission_type = commissions['type']
                    if rate and markup:
                        if type == u'%':
                            rate += rate * markup / Decimal('100')
                        else:
                            rate += markup
                        if commission:
                            if commission_type == u'%':
                                rate -= rate * commission / Decimal('100')
                            else:
                                rate -= commission
                res.append(rate.quantize(Decimal('1'), ROUND_HALF_UP))
            return res


    def recalc_for_bird(self, early_bird):
        """ recalc rate depanding on early bird discount """
        
        if early_bird.eb_discount and early_bird.eb_expanding:
            rates_eb = self.get_rates()
            if early_bird.discount_type == 1:
                if rates_eb:
                    rates = []
                    for rate in rates_eb:
                        if early_bird.eb_discount > 0:
                            rate *= Decimal(str(early_bird.eb_discount)) / 100
                        else:
                            rate += rate * Decimal(str(early_bird.eb_discount)) / 100
                        rates.append(str(rate))
                    self.rates = u';'.join(rates)

            if early_bird.discount_type == 0:
                if rates_eb:
                    rates = []
                    for rate in rates_eb:
                        rate += Decimal(str(early_bird.eb_discount))
                        rates.append(str(rate))
                    self.rates = u';'.join(rates)
        return self.rates


    def recalc_for_combo_birds(self, early_birds):
        """ recalc rate depanding on percent early birds discounts """

        for early_bird in early_birds:
            if early_bird.price_type == 1:
                self.recalc_for_bird(early_bird)
        return self.rates


STAY_PAY_MEAL_CHOICES = (
    ('y', 'yes'), 
    ('n', 'no'), 
    ('c', 'choosen'), 
    )


class StayPayBonus(models.Model):
    pay_nights = models.PositiveIntegerField()
    up_to_nights = models.PositiveIntegerField()
    hotel_supplier = models.ForeignKey(HotelSupplier)

    def __unicode__(self):
        return 'Stay %d + bonus up to %d' % (self.pay_nights, self.up_to_nights)


class StayPay(models.Model):
    stay_nights = models.PositiveIntegerField()
    pay_nights = models.PositiveIntegerField()
    date_from = models.DateField()
    date_to = models.DateField()
    count = models.PositiveIntegerField(null=True, blank=True)
    eb_expanding = models.BooleanField(default=False, blank=True)
    cs = models.BooleanField(default=False, blank=True)
    meal_type = models.CharField(max_length=1, choices=STAY_PAY_MEAL_CHOICES)
    meal = models.ForeignKey(Meal, null=True, blank=True, 
                             related_name='old_stay_pay')
    meals = models.ManyToManyField(Meal, null=True, blank=True)
    room = models.ForeignKey(Room)
    bonus = models.ForeignKey(StayPayBonus, null=True, blank=True)
    tour_code = models.CharField(max_length=50, blank=True)
    hotel_supplier = models.ForeignKey(HotelSupplier)

    class Meta:
        verbose_name = _('stay pay')
        verbose_name_plural = _('stay pays')
        ordering = ('date_from',)

    def __unicode__(self):
        return self.tour_code

    def meal_is_discount(self, meal):
       
        if self.meal_type == 'n':
            return False
        if self.meal_type == 'y':
            return True            
        for meal in self.meals.all():
            print meal.id
        if self.meal_type == 'c' and meal in self.meals.all():
            return True
        return False     
    
        
class Holiday(models.Model):
    date = models.DateTimeField() 
    name = models.CharField(max_length=500)
    company = models.ForeignKey(Company)
    def __unicode__(self):
        return '%s %s' % (self.date, self.name)    
        
        
class HotelMostPopular(models.Model):
    hotel = models.ForeignKey(Hotel) 
    company = models.ForeignKey(Company)        
    best = models.BooleanField(default=False) 
    number = models.PositiveSmallIntegerField(default=0)
    
    def __unicode__(self):
        return '%s' % (self.hotel)
    
    class Meta:
        unique_together = (('company','hotel'),)     
        ordering = ['number']  

    
class HotelInWork(models.Model):
     hotel = models.ForeignKey(Hotel)
     country = models.ForeignKey(Country, null=True)
     supplier =  models.ForeignKey(Contragent, null=True) 

            
class HotelSync(models.Model):
    hotel = models.ForeignKey(Hotel)
    hotel_booking = models.ForeignKey('xml_booking.Hotel', null=True, blank=True)
    user = models.ForeignKey(Profile, null=True)
    search_type = models.CharField(max_length=4, null=True)
    sync_true = models.BooleanField(default=False)
    def __unicode__(self):
        return '%s ' % (self.hotel)           

'''
class HotelSyncBooking(models.Model):
    hotel = models.ForeignKey(HotelSync)
    hotel_title = models.CharField(max_length=255, null=True)
    hotel_country = models.CharField(max_length=255, null=True) 
    hotel_booking_title = models.CharField(max_length=255, null=True)
    hotel_booking = models.ForeignKey('xml_booking.Hotel', null=True)
    hotel_booking_country = models.CharField(max_length=255, null=True)
    
    def __unicode__(self):
        return '%s // %s' % (self.hotel_booking.name, self.hotel_booking_country) 
'''  