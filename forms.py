# -*- coding: utf-8 -*-
import re
import datetime

from copy import copy
from django import forms
from django.db.models import Q
from django.forms.util import ErrorList
from django.forms.formsets import BaseFormSet
from django.template.defaultfilters import dictsort
from django.utils.translation import get_language, ugettext_lazy as _
from django.forms.models import BaseModelFormSet
from django.forms.widgets import CheckboxSelectMultiple    

from bonuses.models import Bonus, EarlyBird
from companies.models import Contragent, Company
from userprofiles.models import Profile
from exchange.models import Exchange
from hotels.models import Hotel, Accommodation, Room, Period, RestaurantAndBar,  \
                          Meal, HotelSupplier, Service, accommodation_types,   \
                          StayPay, ExtraBedRate, accommodation_types, \
                          CompanyRoomParams, RoomParams, StayPayBonus, \
                          PeriodDates, Holiday, \
                          HotelFeature, HotelFeatureCompany, HotelFeatureCompanySpecific, \
                          RoomFeature, RoomFeatureCompany, RoomFeatureCompanySpecific, \
                          RestaurantAndBarFeature, RestaurantAndBarFeatureCompany, \
                          RestaurantAndBarFeatureCompanySpecific, RESTAURANT_OR_BAR_CHOICES, \
                          HotelDescription, RoomDescription, \
                          HotelPhoto, HotelPhotoLang, HotelMostPopular, \
                          HotelFile, HotelFileDescriptionLang,  HotelSync,    \
                          HotelVideo, HotelVideoLang 
                          
from hotels.utils import check_ages_intervals, check_markup
from transfers.models import Transfer
from hotels.middleware import SelectTimeWidget
from xml_booking.models import Hotel as HotelBooking
from regions.models import Country

DATE_INPUT_FORMATS = (
    '%d.%m.%Y',
    '%d,%m,%Y',
    '%d-%m-%Y',
    '%d/%m/%Y',
    '%d\%m\%Y',
    '%d%m%Y',
)

TIME_INPUT_FORMATS = (
    '%H:%M',
    '%H-%M',
)

AGES_CHOICES = [('', '---')] + [(i, i) for i in range(1, 101)]   


class HotelMostPopularForm(forms.ModelForm): 
    class Meta:
        model = HotelMostPopular
        widgets = {             
            'company': forms.HiddenInput(),
            'profile': forms.HiddenInput()                    
        }   


class HotelPhotoForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):

        if 'company_id' and 'hotel_id' in kwargs:
            qs = Room.objects.filter(company_id=kwargs['company_id'], hotel_id = kwargs['hotel_id'])
            self.base_fields['room'] = forms.ModelChoiceField(queryset=qs,required=False)    
            del kwargs['company_id']
            del kwargs['hotel_id']
        super(HotelPhotoForm, self).__init__(*args, **kwargs) 

    room = forms.ModelChoiceField(queryset=Room.objects.none(),required=False)  
    photo = forms.ImageField(widget=forms.FileInput)       
    class Meta:
        model = HotelPhoto
        fields=('photo','room','is_plan')       


class BaseHotelPhotoFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):       
        super(BaseHotelPhotoFormSet, self).__init__(*args, **kwargs)


class HotelPhotoDescriptionForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={'cols': '60', 'rows': '8'})) 
    class Meta:
        model = HotelPhotoLang
        fields=('language','text')
               
                              
class BaseHotelPhotoDescriptionFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(BaseHotelPhotoDescriptionFormSet, self).__init__(*args, **kwargs)
    def clean(self):
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return
        languages = []
        for form in self.forms:
            language = form.cleaned_data.get('language')
            if language in languages:
                raise forms.ValidationError("You can use one language only once.")
            languages.append(language)

#############################################
# видео Отеля
        
class HotelVideoForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):
        if 'company_id' in kwargs and 'hotel_id' in kwargs:
            qs = Room.objects.filter(company_id=kwargs['company_id'], hotel_id = kwargs['hotel_id'])
            self.base_fields['room'] = forms.ModelChoiceField(queryset=qs,required=False)    
            del kwargs['company_id']
            del kwargs['hotel_id']
        super(HotelVideoForm, self).__init__(*args, **kwargs) 

    room = forms.ModelChoiceField(queryset=Room.objects.none(),required=False)
    video = forms.CharField(widget=forms.Textarea(attrs={'cols': '50', 'rows': '5'}))
    class Meta:
        model = HotelVideo
        fields=('video','room')       

class HotelVideoDescriptionForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={'cols': '60', 'rows': '8'})) 
    class Meta:
        model = HotelPhotoLang
        fields=('language','text')
        
class BaseHotelVideoDescriptionFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(BaseHotelVideoDescriptionFormSet, self).__init__(*args, **kwargs)
    def clean(self):
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return
        languages = []
        for form in self.forms:
            language = form.cleaned_data.get('language')
            if language in languages:
                raise forms.ValidationError("You can use one language only once.")
            languages.append(language)      

# конец Видео отеля
######################################################

class HotelFileForm(forms.ModelForm):
    def __init__(self,*args,**kwargs):

        if 'company_id' and 'hotel_id' in kwargs:
            del kwargs['company_id']
            del kwargs['hotel_id']
        super(HotelFileForm, self).__init__(*args, **kwargs) 
      
    class Meta:
        model = HotelFile
        fields=('file_path',)       


class BaseHotelFileFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):       
        super(BaseHotelFileFormSet, self).__init__(*args, **kwargs)


class HotelFileDescriptionForm(forms.ModelForm):
    description = forms.CharField(widget=forms.Textarea(attrs={'cols': '60', 'rows': '8'})) 
    class Meta:
        model = HotelFileDescriptionLang
        fields=('language','description')
               
                              
class BaseHotelFileDescriptionFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(BaseHotelFileDescriptionFormSet, self).__init__(*args, **kwargs)
    def clean(self):
        if any(self.errors):
            return
        languages = []
        for form in self.forms:
            language = form.cleaned_data.get('language')
            if language in languages:
                raise forms.ValidationError("You can use one language only once.")
            languages.append(language)
            

class HotelDescriptionForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={'cols': '60', 'rows': '8'})) 
    class Meta:
        model = HotelDescription
        fields=('language','text')

class BaseHotelDescriptionFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(BaseHotelDescriptionFormSet, self).__init__(*args, **kwargs)
        self.queryset = HotelDescription.objects.all()
    def clean(self):
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return
        languages = []
        for form in self.forms:
            language = form.cleaned_data.get('language')
            if language in languages:
                raise forms.ValidationError("You can use one language only once.")
            languages.append(language)        


class RoomDescriptionForm(forms.ModelForm):
    text = forms.CharField(widget=forms.Textarea(attrs={'cols': '60', 'rows': '8'})) 
    class Meta:
        model = RoomDescription
        fields=('language','text')
               
               
class BaseRoomDescriptionFormSet(BaseModelFormSet):
    def __init__(self, *args, **kwargs):
        super(BaseRoomDescriptionFormSet, self).__init__(*args, **kwargs)
        self.queryset = RoomDescription.objects.all()
    def clean(self):
        if any(self.errors):
            # Don't bother validating the formset unless each form is valid on its own
            return
        languages = []
        for form in self.forms:
            language = form.cleaned_data.get('language')
            if language in languages:
                raise forms.ValidationError("You can use one language only once.")
            languages.append(language) 
   
        
class HotelFeatureCompanySpecificForm(forms.Form):
    def __init__(self,*args,**kwargs):
        if 'hotel_feature_company' in kwargs: 
            hotel_feature_company = kwargs['hotel_feature_company']    
            self.base_fields['hotel_feature_company'] = forms.ModelChoiceField(
                queryset=HotelFeatureCompany.objects.filter(pk=hotel_feature_company.id),empty_label=None)            
        del kwargs['hotel_feature_company'] 
        super(HotelFeatureCompanySpecificForm, self).__init__(*args, **kwargs)
    hotel_feature_company = forms.ModelChoiceField(queryset = HotelFeatureCompany.objects.none())
    hotel_feature = forms.ModelMultipleChoiceField(queryset = HotelFeature.objects.all())

    def clean(self):
        cleaned_data = self.cleaned_data
        data = self.data

        for key,value in data.items():
            
            if key.startswith('hotel_feature_integer') and value:
                try:
                    value = int(value)   
                except:
                    pk = int(key.split('_')[3])
                    hotel_feature = HotelFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in integer format.' % hotel_feature.text)

            if key.startswith('hotel_feature_float') and value:
                try:
                    value = float(value)   
                except:
                    pk = int(key.split('_')[3])
                    hotel_feature = HotelFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in float format.' % hotel_feature.text)

            if key.startswith('hotel_feature_text') and value:
                value = u'%s' % value
                if len(value) > 500:
                    pk = int(key.split('_')[3])
                    hotel_feature = HotelFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Too long.' % hotel_feature.text)

            if key.startswith('hotel_feature_date') and value:
                date = CheckDateForm({'date':value})
                if date.is_valid():
                    pass   
                else:
                    pk = int(key.split('_')[3])
                    hotel_feature = HotelFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in date format.' % hotel_feature.text)

            if key.startswith('hotel_feature_ftandmetr') \
            and not key.startswith('hotel_feature_ftandmetr_select') \
            and not key.startswith('hotel_feature_ftandmetrsquare') \
            and not key.startswith('hotel_feature_ftandmetrsquare_select') \
            and value:

                try:
                    value = float(value)   
                except:
                    pk = int(key.split('_')[3])
                    hotel_feature = HotelFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in float format.' % hotel_feature.text)

            if key.startswith('hotel_feature_ftandmetrsquare') and not key.startswith('hotel_feature_ftandmetrsquare_select') and value:

                try:
                    value = float(value)   
                except:
                    pk = int(key.split('_')[3])
                    hotel_feature = HotelFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in float format.' % hotel_feature.text)


        return cleaned_data        


class RoomFeatureCompanySpecificForm(forms.Form):

    def __init__(self,*args,**kwargs):
        if 'room_feature_company' in kwargs:
            room_feature_company = kwargs['room_feature_company'] 
            self.base_fields['room_feature_company'] = forms.ModelChoiceField(
                queryset=RoomFeatureCompany.objects.filter(pk=room_feature_company.id),empty_label=None)            
        del kwargs['room_feature_company'] 
        super(RoomFeatureCompanySpecificForm, self).__init__(*args, **kwargs)
    room_feature_company = forms.ModelChoiceField(queryset = RoomFeatureCompany.objects.none())
    room_feature = forms.ModelMultipleChoiceField(queryset = RoomFeature.objects.all())

    def clean(self):
        cleaned_data = self.cleaned_data
        data = self.data

        for key,value in data.items():
            
            if key.startswith('room_feature_integer') and value:
                try:
                    value = int(value)   
                except:
                    pk = int(key.split('_')[3])
                    room_feature = RoomFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in integer format.' % room_feature.text)

            if key.startswith('room_feature_float') and value:
                try:
                    value = float(value)   
                except:
                    pk = int(key.split('_')[3])
                    room_feature = RoomFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in float format.' % room_feature.text)

            if key.startswith('room_feature_text') and value:
                value = u'%s' % value
                if len(value) > 40:
                    pk = int(key.split('_')[3])
                    room_feature = RoomFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Too long.' % room_feature.text)

            if key.startswith('room_feature_date') and value:
                date = CheckDateForm({'date':value})
                if date.is_valid():
                    pass   
                else:
                    pk = int(key.split('_')[3])
                    room_feature = RoomFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in date format.' % room_feature.text)

            if key.startswith('room_feature_ftandmetr') \
            and not key.startswith('room_feature_ftandmetr_select') \
            and not key.startswith('room_feature_ftandmetrsquare') \
            and not key.startswith('room_feature_ftandmetrsquare_select') \
            and value:
            
                try:
                    value = float(value)   
                except:
                    pk = int(key.split('_')[3])
                    room_feature = RoomFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in float format.' % room_feature.text)

            if key.startswith('room_feature_ftandmetrsquare') and not key.startswith('room_feature_ftandmetrsquare_select') and value:

                try:
                    value = float(value)   
                except:
                    pk = int(key.split('_')[3])
                    room_feature = RoomFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in float format.' % room_feature.text)

        return cleaned_data


class RestaurantAndBarFeatureCompanySpecificForm(forms.Form):

    def __init__(self,*args,**kwargs):
        if 'restaurant_and_bar_feature_company' in kwargs:            
            restaurant_and_bar_feature_company = kwargs['restaurant_and_bar_feature_company'] 
            self.base_fields['restaurant_and_bar_feature_company'] = forms.ModelChoiceField(
                queryset=RestaurantAndBarFeatureCompany.objects.filter(pk=restaurant_and_bar_feature_company.id),empty_label=None)            
        del kwargs['restaurant_and_bar_feature_company'] 
        super(RestaurantAndBarFeatureCompanySpecificForm, self).__init__(*args, **kwargs)
    restaurant_and_bar_feature_company = forms.ModelChoiceField(queryset = RestaurantAndBarFeatureCompany.objects.none())
    restaurant_and_bar_feature = forms.ModelMultipleChoiceField(queryset = RestaurantAndBarFeature.objects.all())

    def clean(self):
        cleaned_data = self.cleaned_data
        data = self.data

        for key,value in data.items():
            
            if key.startswith('restaurant_and_bar_feature_integer') and value:
                try:
                    value = int(value)   
                except:
                    pk = int(key.split('_')[5])
                    restaurant_and_bar_feature = RestaurantAndBarFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in integer format.' % restaurant_and_bar_feature.text)

            if key.startswith('restaurant_and_bar_feature_float') and value:
                try:
                    value = float(value)   
                except:
                    pk = int(key.split('_')[5])
                    restaurant_and_bar_feature = RestaurantAndBarFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in float format.' % restaurant_and_bar_feature.text)

            if key.startswith('restaurant_and_bar_feature_text') and value:
                value = u'%s' % value
                if len(value) > 40:
                    pk = int(key.split('_')[5])
                    restaurant_and_bar_feature = RestaurantAndBarFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Too long.' % restaurant_and_bar_feature.text)

            if key.startswith('restaurant_and_bar_feature_date') and value:
                date = CheckDateForm({'date':value})
                if date.is_valid():
                    pass   
                else:
                    pk = int(key.split('_')[5])
                    restaurant_and_bar_feature = RestaurantAndBarFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in date format.' % restaurant_and_bar_feature.text)

            if key.startswith('restaurant_and_bar_feature_ftandmetr') \
            and not key.startswith('restaurant_and_bar_feature_ftandmetr_select') \
            and not key.startswith('restaurant_and_bar_feature_ftandmetrsquare') \
            and not key.startswith('restaurant_and_bar_feature_ftandmetrsquare_select') \
            and value:
            
                try:
                    value = float(value)   
                except:
                    pk = int(key.split('_')[5])
                    restaurant_and_bar_feature = RestaurantAndBarFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in float format.' % restaurant_and_bar_feature.text)

            if key.startswith('restaurant_and_bar_feature_ftandmetrsquare') and not key.startswith('restaurant_and_bar_feature_ftandmetrsquare_select') and value:

                try:
                    value = float(value)   
                except:
                    pk = int(key.split('_')[5])
                    restaurant_and_bar_feature = RestaurantAndBarFeature.objects.get(pk = pk)
                    raise forms.ValidationError('Error with %s. Input correct value in float format.' % restaurant_and_bar_feature.text)

        return cleaned_data


class AddRestaurantOrBarForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        if 'hotel_pk' in kwargs:
            hotel_pk = kwargs['hotel_pk']
            self.base_fields['hotel'] = forms.ModelChoiceField(
                queryset=Hotel.objects.filter(pk=hotel_pk), empty_label=None)
            del kwargs['hotel_pk']
        if 'company_pk' in kwargs:
            company_pk = kwargs['company_pk']
            self.base_fields['company'] = forms.ModelChoiceField(
                queryset=Company.objects.filter(pk=company_pk), empty_label=None)
            del kwargs['company_pk']

        super(AddRestaurantOrBarForm, self).__init__(*args, **kwargs)
    company = forms.ModelChoiceField(queryset=Company.objects.none())
    hotel = forms.ModelChoiceField(queryset=Hotel.objects.none())
    restaurant_or_bar = forms.ChoiceField(choices=RESTAURANT_OR_BAR_CHOICES)
    class Meta:
        model = RestaurantAndBar


class CheckDateForm(forms.Form):
    date = forms.DateField(input_formats=DATE_INPUT_FORMATS)
          
               
class FilterForm(forms.Form):
    query = forms.CharField(widget=forms.TextInput(attrs={'size': 20}))


class PeriodForm(forms.ModelForm):
    class Meta:
        model = Period
        fields = ('title', 'ms')


class PeriodDatesForm(forms.ModelForm):
    date_from = forms.DateField(
                    input_formats=DATE_INPUT_FORMATS,
                    widget=forms.TimeInput(format='%d.%m.%Y'))
    date_to = forms.DateField(
                    input_formats=DATE_INPUT_FORMATS,
                    widget=forms.TimeInput(format='%d.%m.%Y'))
    class Meta:
        model = PeriodDates
        fields = ('date_from', 'date_to')
        
    def clean(self):
        cleaned_data = self.cleaned_data
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        if date_from and date_to and date_from > date_to:
             raise forms.ValidationError('Invalid interval') 
        return cleaned_data


class RoomChoiceField(forms.ModelChoiceField):
    def __init__(self, queryset, empty_label=u"---------", cache_choices=False,
                 required=True, widget=None, label=None, initial=None,
                 help_text=None, to_field_name=None, *args, **kwargs):
        if 'choices' in kwargs:
            self.choices = kwargs['choices']
            del kwargs['choices']
        super(RoomChoiceField, self).__init__(queryset, empty_label=u'---------', 
                                              cache_choices=cache_choices, required=required, 
                                              widget=widget, label=label, 
                                              initial=initial, help_text=help_text, 
                                              to_field_name=to_field_name, *args, **kwargs)


class CaculationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        
        hotel_supplier = kwargs['hotel_supplier']
        room_qs = kwargs['rooms']
        max_pax = kwargs['max_pax']

        self.base_fields['meal'] = forms.ModelChoiceField(
            queryset=Meal.objects.filter(hotel_supplier=hotel_supplier))
                
        #get rooms in company order
        company = hotel_supplier.company
        hotel = hotel_supplier.hotel

        try:
            company_room_params = CompanyRoomParams.objects.get(company=company, 
                                                                hotel=hotel)
        except CompanyRoomParams.DoesNotExist:
            company_room_params = None
        if company_room_params:
            room_orders = company_room_params.get_room_order()
        else:
            room_orders = {}

        if room_orders:
            rooms_tmp = []
            for room in room_qs:
                rooms_tmp.append({'room': room, 'order': room_orders.get(room.pk, 0)})
            rooms = [room_item['room'] for room_item in dictsort(rooms_tmp, 'order')]
            choices = [('', '---')] + [(room.pk, room) for room in rooms]
            self.base_fields['room_1'] = RoomChoiceField(queryset=room_qs, 
                                                         choices=choices)
            self.base_fields['room_2'] = RoomChoiceField(queryset=room_qs, 
                                                         choices=choices,
                                                         required=False)
        else:
            self.base_fields['room_1'] = forms.ModelChoiceField(queryset=room_qs)
            self.base_fields['room_2'] = forms.ModelChoiceField(queryset=room_qs, 
                                                                required=False)

        #only availible exchanges
        '''
        exchange_qs = Exchange.objects.filter(
                Q(contragentrate__contragent=hotel_supplier.supplier_id) |
                Q(exportexchangerate__company=hotel_supplier.company_id) |
                Q(in_cbr=True)
            ).distinct()
        self.base_fields['exchange'] = forms.ModelChoiceField(queryset=exchange_qs)
        '''
               
        #age types for
        for counter in range(max_pax+1):
            if counter > 0:
                required = False
            else:
                required = False
            self.base_fields['age1_%d' % counter] = forms.ChoiceField(choices=AGES_CHOICES, 
                                                                      required=required)
            self.base_fields['age2_%d' % counter] = forms.ChoiceField(choices=AGES_CHOICES, 
                                                                      required=False)

        del kwargs['hotel_supplier']
        del kwargs['max_pax']
        del kwargs['rooms']
        super(CaculationForm, self).__init__(*args, **kwargs)
    
    meal = forms.ModelChoiceField(
                queryset=Meal.objects.none())
    exchange = forms.ModelChoiceField(queryset=Exchange.objects.all())
    date_start = forms.DateField(input_formats=DATE_INPUT_FORMATS)
    nights_count = forms.IntegerField()
    just_married_1 = forms.BooleanField(required=False)
    just_married_2 = forms.BooleanField(required=False)

    def clean_nights_count(self):
        nights_count = self.cleaned_data['nights_count']
        if nights_count and nights_count <= 0:
            self._errors['nights_count'] = self.error_class(['Input positive number'])
        return nights_count


class RoomOrderForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'hotel_supplier' in kwargs:
            hotel_supplier = kwargs['hotel_supplier']

            self.base_fields['room'] = forms.ModelChoiceField(
                queryset=Room.objects.filter(hotel=hotel_supplier.hotel), 
                widget=forms.HiddenInput)
            del kwargs['hotel_supplier']

        super(RoomOrderForm, self).__init__(*args, **kwargs)

    room = forms.ModelChoiceField(queryset=Room.objects.none())
    order = forms.IntegerField(min_value=0, max_value=100)


class HotelSupplierItemsFormset(forms.models.BaseFormSet):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, **kwargs):
        if 'hotel_supplier' in kwargs:
            self.hotel_supplier = kwargs['hotel_supplier']
            del kwargs['hotel_supplier']
        else:
            self.hotel_supplier = None

        super(HotelSupplierItemsFormset, self).__init__(data, files, auto_id, prefix,
                 initial, error_class)

    def _construct_forms(self):
        if self.hotel_supplier:
            self.forms = []
            for i in xrange(self.total_form_count()):
                self.forms.append(self._construct_form(i, hotel_supplier=self.hotel_supplier))
        else:
            super(HotelSupplierItemsFormset, self)._construct_forms()


class EarlyBirdAddForm(forms.ModelForm):

    bron_date_from = forms.DateField(input_formats=('%d%m%y',), required=False)
    bron_date_to = forms.DateField(input_formats=('%d%m%y',), required=False)
    accommodation_date_from = forms.DateField(input_formats=('%d%m%y',))
    accommodation_date_to = forms.DateField(input_formats=('%d%m%y',))

    def clean(self):
        cleaned_data = self.cleaned_data

        bron_date_from = cleaned_data.get('bron_date_from')
        bron_date_to = cleaned_data.get('bron_date_to')
        bron_period = cleaned_data.get('bron_period', 0)
        bron_period_type = cleaned_data.get('bron_period_type')
        if not (bron_date_from and bron_date_to) and \
            not bron_period_type:
                self._errors['bron_period'] = self.error_class(['This field is required'])

        if bron_date_from and bron_date_to:
            if bron_date_from > bron_date_to:
                self._errors['bron_date_from'] = \
                    self.error_class(['Start date must be earlier then end date'])

        accommodation_date_from = cleaned_data.get('accommodation_date_from')
        accommodation_date_to = cleaned_data.get('accommodation_date_to')
        if accommodation_date_from and accommodation_date_to:
            if accommodation_date_from > accommodation_date_to:
                self._errors['accommodation_date_from'] = \
                    self.error_class(['Start date must be earlier then end date'])

        discount = cleaned_data.get('discount')
        if discount > 100 or discount < -100:
            self._errors['discount'] = self.error_class(['Error'])

        return cleaned_data

    class Meta:
        model = EarlyBird
        fields = ('bron_date_from', 'bron_date_to', 'bron_period',
                  'bron_period_type', 'accommodation_date_from', 
                  'accommodation_date_to', 'discount', 'tourcode',
                  'discount_type', 'eb_expanding', 'cs_expanding',
                  'meal_expanding', 
                 )


class BirdCopyOptionsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'hotel_supplier' in kwargs:
            hotel_supplier = kwargs['hotel_supplier']

            self.base_fields['rooms'] = forms.ModelMultipleChoiceField(
                queryset=Room.objects.filter(hotel=hotel_supplier.hotel), 
                required=False)

            self.base_fields['meals'] = forms.ModelMultipleChoiceField(
                queryset=Meal.objects.filter(hotel_supplier=hotel_supplier), 
                required=False)

            self.base_fields['staypays'] = forms.ModelMultipleChoiceField(
                queryset=StayPay.objects.filter(hotel_supplier=hotel_supplier),
                required=False)

            self.base_fields['services'] = forms.ModelMultipleChoiceField(
                queryset=Service.objects.filter(Q(hotel_supplier=hotel_supplier) |
                                                Q(period__hotel_supplier=hotel_supplier)),
                required=False)

            del kwargs['hotel_supplier']

        super(BirdCopyOptionsForm, self).__init__(*args, **kwargs)

    rooms = forms.ModelMultipleChoiceField(queryset=Room.objects.none(), 
                                           required=False)
    meals = forms.ModelMultipleChoiceField(queryset=Meal.objects.none(), 
                                           required=False)
    staypays = forms.ModelMultipleChoiceField(queryset=StayPay.objects.none(), 
                                              required=False)
    services = forms.ModelMultipleChoiceField(queryset=Service.objects.none(), 
                                              required=False)


class ServiceAddForm(forms.ModelForm):
    date = forms.DateField(input_formats=('%d%m%y',), required=False)
    class Meta:
        model = Service
        fields = ('per_type', 'title', 'date', 'pay_type')

    def clean(self):
        cleaned_data = self.cleaned_data
        date = self.cleaned_data.get('date')
        pay_type = self.cleaned_data.get('pay_type')
        if not date and not pay_type:
            raise forms.ValidationError('Error')
        return cleaned_data


STAY_PAY_MEAL_CHOICES = (
    ('y', 'yes'), 
    ('n', 'no'), 
    ('c', 'choosen'), 
    )


class StayPayForm(forms.Form):
    date_from = forms.DateField(input_formats=('%d%m%y',))
    date_to = forms.DateField(input_formats=('%d%m%y',))
    stay_nights = forms.CharField()
    discount_nights = forms.IntegerField()
    count = forms.IntegerField(required=False)
    eb_expanding = forms.BooleanField(required=False)
    cs = forms.BooleanField(required=False)
    meal_type = forms.ChoiceField(choices=STAY_PAY_MEAL_CHOICES)
    tour_code = forms.CharField(required=False)

    def clean(self):
        cleaned_data = self.cleaned_data
        stay_nights = cleaned_data.get('stay_nights')
        discount_nights = cleaned_data.get('discount_nights')
        date_to = cleaned_data.get('date_to')
        date_from = cleaned_data.get('date_from')

        stay_nights_lst = stay_nights.split(',')
        if discount_nights:
            discount_nights = abs(discount_nights)
            for stay_nights_item in stay_nights_lst:
                if stay_nights_item:
                    try:
                        stay_nights_item = int(stay_nights_item)
                    except:
                        raise forms.ValidationError('Error in stay nights digits')
                        break

                    if stay_nights_item <= discount_nights:
                        raise forms.ValidationError('Stay Nights must be less then pay nights')
                else:
                    raise forms.ValidationError('Error in stay nights str')

        if date_to and date_to:
            if date_from > date_to:
                raise forms.ValidationError('Start date must be before end date')
        return cleaned_data


class StayPayBonusForm(forms.ModelForm):
    date_from = forms.DateField(input_formats=('%d%m%y',))
    date_to = forms.DateField(input_formats=('%d%m%y',))
    up_to_nights = forms.IntegerField()
    pay_nights = forms.CharField()

    class Meta:
        model = StayPay
        fields = ('date_from', 'date_to', 'count', 
                  'eb_expanding', 'cs', 'meal_type', 
                  'tour_code',)

    def clean(self):
        cleaned_data = self.cleaned_data
        date_to = cleaned_data.get('date_to')
        date_from = cleaned_data.get('date_from')
        up_to_nights = cleaned_data.get('up_to_nights')
        pay_nights = cleaned_data.get('pay_nights')

        if date_to and date_to:
            if date_from > date_to:
                raise forms.ValidationError('Start date must be before end date')

        pay_nights_lst = pay_nights.split(',')
        for pay_nights_item in pay_nights_lst:
            if pay_nights_item:
                try:
                    pay_nights_item = int(pay_nights_item)
                except:
                    raise forms.ValidationError('Error in pay nights digits')
                    break
            else:
                raise forms.ValidationError('Error in psy nights str')

        if up_to_nights  and up_to_nights  < 1:
            raise forms.ValidationError('Up to nights must be >=1')

        return cleaned_data


class StayPaysForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'hotel_supplier' in kwargs:
            hotel_supplier = kwargs['hotel_supplier']
            qs = StayPay.objects.filter(hotel_supplier=hotel_supplier)
            self.base_fields['staypays'] = forms.ModelMultipleChoiceField(
                queryset=qs)
            del kwargs['hotel_supplier']            
        super(StayPaysForm, self).__init__(*args, **kwargs)

    staypays = forms.ModelMultipleChoiceField(queryset=StayPay.objects.none())

class StayPaysBonusesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'hotel_supplier' in kwargs:
            hotel_supplier = kwargs['hotel_supplier']
            qs = StayPayBonus.objects.filter(hotel_supplier=hotel_supplier)
            self.base_fields['staypay_bonuses'] = forms.ModelMultipleChoiceField(
                queryset=qs)
            del kwargs['hotel_supplier']            
        super(StayPaysBonusesForm, self).__init__(*args, **kwargs)

    staypay_bonuses = forms.ModelMultipleChoiceField(queryset=StayPayBonus.objects.none())


class EBRatesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'hotel_supplier' in kwargs:
            hotel_supplier = kwargs['hotel_supplier']
            qs = ExtraBedRate.objects.filter(period__hotel_supplier=hotel_supplier)
            self.base_fields['extra_bed_rates'] = forms.ModelMultipleChoiceField(
                queryset=qs)
            del kwargs['hotel_supplier']            
        super(EBRatesForm, self).__init__(*args, **kwargs)

    extra_bed_rates = forms.ModelMultipleChoiceField(queryset=ExtraBedRate.objects.none())

        
class HotelSupplierAddForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'contragents' in kwargs:
            self.base_fields['supplier'] = forms.ModelChoiceField(queryset=kwargs['contragents'])
            del kwargs['contragents']            
        super(HotelSupplierAddForm, self).__init__(*args, **kwargs)
        
    supplier = forms.ModelChoiceField(queryset=Contragent.objects.none())


class FlightCalcForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'hotel_supplier' in kwargs:
            hotel_supplier = kwargs['hotel_supplier']
            qs1 = hotel_supplier.transfers.all()
            self.base_fields['transfers'] = forms.ModelChoiceField(
                queryset=qs1, required=False)
            qs2 = Meal.objects.filter(hotel_supplier=hotel_supplier)
            self.base_fields['meals'] = forms.ModelChoiceField(
                queryset=qs2, required=False)
            del kwargs['hotel_supplier']            
        super(FlightCalcForm, self).__init__(*args, **kwargs)

    formula = forms.CharField()
    transfers = forms.ModelChoiceField(queryset=Transfer.objects.none(), 
        required=False)
    meals = forms.ModelChoiceField(queryset=Meal.objects.all())
    rooms = forms.ModelChoiceField(queryset=Room.objects.all())


class PeriodsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'hotel_supplier' in kwargs:
            hotel_supplier = kwargs['hotel_supplier']
            qs = Period.objects.filter(hotel_supplier=hotel_supplier)
            self.base_fields['periods'] = forms.ModelMultipleChoiceField(
                queryset=qs)
            del kwargs['hotel_supplier']            
        super(PeriodsForm, self).__init__(*args, **kwargs)
        
    periods = forms.ModelMultipleChoiceField(queryset=Period.objects.all())


class HotelsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'company' in kwargs:
            company = kwargs['company']
            qs = HotelSupplier.objects.actual().filter(company=company)
            self.base_fields['hotels'] = forms.ModelMultipleChoiceField(
                queryset=qs)
            del kwargs['company']            
        super(HotelsForm, self).__init__(*args, **kwargs)
        
    hotels = forms.ModelMultipleChoiceField(queryset=HotelSupplier.objects.all())


class HotelSuppliersForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'company' in kwargs:
            hotel_supplier = kwargs['company']
            qs = HotelSupplier.objects.actual().select_related(
                    'public_version').filter(company=company)
            self.base_fields['hotel_suppliers'] = forms.ModelMultipleChoiceField(
                queryset=qs)
            del kwargs['company']            
        super(HotelSuppliersForm, self).__init__(*args, **kwargs)

    hotel_suppliers = forms.ModelMultipleChoiceField(queryset=HotelSupplier.objects.none())


class HotelSupllierChooseForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'company' in kwargs:
            company = kwargs['company']
            qs = HotelSupplier.objects.filter(company=company)
            self.base_fields['hotels'] = forms.ModelMultipleChoiceField(
                queryset=qs, required=False)
            del kwargs['company']            
        super(HotelSupllierChooseForm, self).__init__(*args, **kwargs)
        
    hotels = forms.ModelMultipleChoiceField(queryset=HotelSupplier.objects.all(), required=False)
    

class ServicesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'hotel_supplier' in kwargs:
            hotel_supplier = kwargs['hotel_supplier']
            qs = Service.objects.filter(Q(period__hotel_supplier=hotel_supplier) |
                                        Q(hotel_supplier=hotel_supplier))
            self.base_fields['services'] = forms.ModelMultipleChoiceField(
                queryset=qs)
            del kwargs['hotel_supplier']            
        super(ServicesForm, self).__init__(*args, **kwargs)

    services = forms.ModelMultipleChoiceField(queryset=Service.objects.none())


class ServicesMealsRoomsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'hotel_supplier' in kwargs:
            hotel_supplier = kwargs['hotel_supplier']
            service_qs = Service.objects.filter(period__hotel_supplier=hotel_supplier)
            self.base_fields['services'] = forms.ModelMultipleChoiceField(
                queryset=service_qs)
            meal_qs = Meal.objects.filter(hotel_supplier=hotel_supplier)
            self.base_fields['meals'] = forms.ModelMultipleChoiceField(
                queryset=meal_qs, required=False)
            room_qs = Room.objects.filter(Q(hotel=hotel_supplier.hotel_id), 
                                          Q(company__isnull=True) |
                                          Q(company=hotel_supplier.company_id))
            self.base_fields['rooms'] = forms.ModelMultipleChoiceField(
                queryset=room_qs, required=False)
            del kwargs['hotel_supplier']

        super(ServicesMealsRoomsForm, self).__init__(*args, **kwargs)

    services = forms.ModelMultipleChoiceField(queryset=Service.objects.none())
    meals = forms.ModelMultipleChoiceField(queryset=Meal.objects.none(), required=False)
    rooms = forms.ModelMultipleChoiceField(queryset=Room.objects.none(), required=False)

SERVICE_TYPE_CHOICES = (
    ('AND', 'AND'),
    ('OR', 'OR'),
    )
    
class RelatedServicesForm(forms.Form):
    def __init__(self, *args, **kwargs):
        
        hotel_supplier = kwargs['hotel_supplier']
        qs = Service.objects.filter(period__hotel_supplier=hotel_supplier)
        base_service = kwargs['service']
        qs = qs.filter(date=base_service.date)

        self.base_fields['services'] = forms.ModelMultipleChoiceField(
             queryset=qs)

        del kwargs['hotel_supplier']
        del kwargs['service']
        super(RelatedServicesForm, self).__init__(*args, **kwargs)
        
    services = forms.ModelMultipleChoiceField(queryset=Service.objects.all())
    type = forms.ChoiceField(choices=SERVICE_TYPE_CHOICES)
    

class FormulaRoomsMealsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'hotel_supplier' in kwargs:
            hotel_supplier = kwargs['hotel_supplier']
            qs1 = Meal.objects.filter(hotel_supplier=hotel_supplier)
            self.base_fields['meals'] = forms.ModelMultipleChoiceField(
                queryset=qs1, required=False)
            qs2 = Room.objects.filter(hotel=hotel_supplier.hotel)
            self.base_fields['rooms'] = forms.ModelMultipleChoiceField(
                queryset=qs2)
            del kwargs['hotel_supplier']            
        super(FormulaRoomsMealsForm, self).__init__(*args, **kwargs)
        
    meals = forms.ModelMultipleChoiceField(queryset=Meal.objects.all(), required=False)
    rooms = forms.ModelMultipleChoiceField(queryset=Room.objects.all())
    formula = forms.CharField()
    

class MealsPeriodsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'hotel_supplier' in kwargs:
            hotel_supplier = kwargs['hotel_supplier']
            qs1 = Meal.objects.filter(hotel_supplier=hotel_supplier)
            self.base_fields['meals'] = forms.ModelMultipleChoiceField(
                queryset=qs1)
            qs2 = Period.objects.filter(hotel_supplier=hotel_supplier)
            self.base_fields['periods'] = forms.ModelMultipleChoiceField(
                queryset=qs2)
            del kwargs['hotel_supplier']            
        super(MealsPeriodsForm, self).__init__(*args, **kwargs)
        
    meals = forms.ModelMultipleChoiceField(queryset=Meal.objects.all())
    periods = forms.ModelMultipleChoiceField(queryset=Period.objects.all())

    
class MealsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'hotel_supplier' in kwargs:
            hotel_supplier = kwargs['hotel_supplier']
            qs = Meal.objects.filter(hotel_supplier=hotel_supplier)
            self.base_fields['meals'] = forms.ModelMultipleChoiceField(
                queryset=qs)
            del kwargs['hotel_supplier']            
        super(MealsForm, self).__init__(*args, **kwargs)

    meals = forms.ModelMultipleChoiceField(queryset=Meal.objects.none())


class RoomsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'company' in kwargs:
            company = kwargs['company']
            qs = Room.objects.filter(Q(company=company) | Q(company__isnull=True))
            self.base_fields['rooms'] = forms.ModelMultipleChoiceField(
                queryset=qs)
            del kwargs['company']            
        super(RoomsForm, self).__init__(*args, **kwargs)

    rooms = forms.ModelMultipleChoiceField(queryset=Room.objects.all())


class CompanyRoomsForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'company' in kwargs:
            company = kwargs['company']
            qs = Room.objects.filter(Q(company=company) | Q(company__isnull=True))
            self.base_fields['rooms'] = forms.ModelMultipleChoiceField(
                queryset=qs)
            del kwargs['company']            
        super(CompanyRoomsForm, self).__init__(*args, **kwargs)

    rooms = forms.ModelMultipleChoiceField(queryset=Room.objects.all())
    
    
class TransfersForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'hotel_supplier' in kwargs:
            hotel_supplier = kwargs['hotel_supplier']
            qs = hotel_supplier.transfers.all()
            self.base_fields['transfers'] = forms.ModelMultipleChoiceField(
                queryset=qs)
            del kwargs['hotel_supplier']            
        super(TransfersForm, self).__init__(*args, **kwargs)

    transfers = forms.ModelMultipleChoiceField(queryset=Transfer.objects.all())
    
class HotelPkForm(forms.Form):
    hotel_pk = forms.IntegerField()
    
class IntDigForm(forms.Form):
    digit = forms.IntegerField()

    
class HotelDatesEditForm(forms.ModelForm):
    checkin = forms.TimeField(
        #input_formats=TIME_INPUT_FORMATS,
        #widget=forms.TimeInput(format='%H:%M')
        widget=SelectTimeWidget(minute_step=30, second_step=30)
        )
    checkout = forms.TimeField(
        #input_formats=TIME_INPUT_FORMATS,
        #widget=forms.TimeInput(format='%H:%M')
        widget=SelectTimeWidget(minute_step=30, second_step=30)
        )
        
    class Meta:
        model = HotelSupplier
        fields = ('checkin', 'checkout')


class AccommodationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        self.childpolicy = kwargs['childpolicy']
        del kwargs['childpolicy']            
        super(AccommodationForm, self).__init__(*args, **kwargs)

    formula = forms.CharField(required=False, widget=forms.TextInput(attrs={'style': 'width: 200px'}))
    all = forms.IntegerField(widget=forms.HiddenInput, required=False)
    age_type_1_count = forms.IntegerField(widget=forms.HiddenInput, required=False)
    age_type_2_count = forms.IntegerField(widget=forms.HiddenInput, required=False)
    age_type_3_count = forms.IntegerField(widget=forms.HiddenInput, required=False)
    age_type_4_count = forms.IntegerField(widget=forms.HiddenInput, required=False)


    def clean_formula(self):
        formula = self.cleaned_data.get('formula')
        if formula:
            for operand_str in formula.replace('+', ';').replace('-', ';').split(';'):
                if operand_str in accommodation_types:
                    continue
 
                # for 1R, 2R etc (R)
                item_re = re.compile(r'^([0-9]+)R$')
                item_match = item_re.search(operand_str)
                if item_match:
                    continue

                # for EB|RB
                item_re = re.compile(r'^(EB|RB)$')
                item_match = item_re.search(operand_str)
                if item_match:
                    continue

                # for 1R*5, 2R*2,  etc (R)
                item_re = re.compile(r'^([0-9]+)R\*([0-9]+)$')
                item_match = item_re.search(operand_str)
                if item_match:
                    continue

                # for 2EB, 2RB etc 
                item_re = re.compile(r'^([0-9]+)(EB|RB)$')
                item_match = item_re.search(operand_str)
                if item_match:
                    continue

                # for EB*5, RB*2 etc (R)
                item_re = re.compile(r'^(RB|EB)\*([0-9]+)$')
                item_match = item_re.search(operand_str)
                if item_match:
                    continue


                # for EB(1,0,1), RB(0,0,1)
                item_re = re.compile(r'^(EB|RB)\((.+)\)$')
                item_match = item_re.search(operand_str)
                if item_match:
                    try:
                        age_counts = [int(item) for item in item_match.group(2).split(',')]
                    except ValueError:
                        age_counts = None
                    if age_counts and len(age_counts) == len(self.childpolicy.get_ages()):
                        continue

                # for +25%
                item_re = re.compile(r'^([0-9]+)%$')
                item_match = item_re.search(operand_str)
                if item_match:
                    continue

                # for +25.5%
                item_re = re.compile(r'^(\d+)\.(\d+)%$')
                item_match = item_re.search(operand_str.replace(',', '.'))
                if item_match:
                    continue

                # for M - ignore
                item_re = re.compile(r'^(\d*)M$')
                item_match = item_re.search(operand_str)
                if item_match:
                    continue

                # for M(1,0,1)
                item_re = re.compile(r'^(\d*)M\((.+)\)$')
                item_match = item_re.search(operand_str)
                if item_match:
                    try:
                        age_counts = [int(item) for item in item_match.group(2).split(',')]
                    except ValueError:
                        age_counts = None
                    if age_counts and len(age_counts) == len(self.childpolicy.get_ages()):
                        continue

                # for F - ignore
                item_re = re.compile(r'^(\d*)(\*{1}|)F$')
                item_match = item_re.search(operand_str)
                if item_match:
                    continue

                self._errors['formula'] = self.error_class([_(u'Incorrect format')])
                break

        return formula


class AccommodationFormset(BaseFormSet):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, childpolicy=None):
        self.childpolicy = childpolicy
        super(AccommodationFormset, self).__init__(data, files, auto_id, 
                                                   prefix, initial, error_class)

    def _construct_forms(self):
        self.forms = []
        for i in xrange(self.total_form_count()):
            self.forms.append(self._construct_form(i, childpolicy=self.childpolicy))


class FormulaForm(forms.Form):
    formula = forms.CharField()


class CommandForm(forms.Form):
    command = forms.CharField()

    
CALCULATION_METHOD_CHOICES=[(0, 'Per Room'), (1, 'Per Person'),]
    
class PaxForm(forms.ModelForm):
    min_age_group = forms.CharField(required=False)
    occupancy = forms.CharField(required=False)
    def __init__(self, *args, **kwargs):

        self.base_fields['calculation_method'] = forms.ChoiceField(choices=CALCULATION_METHOD_CHOICES, widget=forms.RadioSelect())
        super(PaxForm, self).__init__(*args, **kwargs)

    class Meta:
        model = Room
        fields = ('max_pax','calculation_method')
        
 
class FormulaEditForm(forms.Form):
    flight_rates = forms.CharField()
    flight_markup = forms.CharField()
    
    def clean_flight_rates(self):
        flight_rates = self.cleaned_data['flight_rates']
        if len(flight_rates.split(',')) > 1:
            error = check_ages_intervals(flight_rates)
        else:
            error = True
        exchange_code = flight_rates.split(',')[-1].strip()
        try:
            exchange = Exchange.objects.get(char_code__iexact=exchange_code)
        except:
            error = True
        if error:
            self._errors['flight_rates'] = ErrorList(['Error'])                        
        return flight_rates

    def clean_flight_markup(self):
        flight_markup = self.cleaned_data['flight_markup']
        if len(flight_markup.split(';')) == 1:
            error = not check_markup(flight_markup)
        else:
            error = True
        if error:
            self._errors['flight_markup'] = ErrorList(['Error'])
        return flight_markup
        


def get_child_ages():

    val_1 = u'%s' % _(u'года')
    val_2 = u'%s' % _(u'лет')
    
    CHILD_AGES = (('',_(u'нет')),)
    for age in range(0,19):
        if age == 0:
            CHILD_AGES += ((age,_(u'меньше года')),) 
        if age == 1:
            CHILD_AGES += ((age,_(u'1 год')),)    
        elif age > 1 and age < 5:
            CHILD_AGES += ((age,u'%s %s' % (age,val_1)),)                     
        elif age >= 5:
            CHILD_AGES += ((age,u'%s %s' % (age,val_2)),)  
       
    return CHILD_AGES 


         
def get_stars():

    val_1 = u'%s' % (_(u'звезды'))
    val_2 = u'%s' % (_(u'звезд'))

    STARS = (('ALL',_(u'не важно')),)   
    for stars in range(2,7):
        if stars in [2,3,4]:       
            STARS += ((stars,u'%s %s' % (stars,val_1)),)             
        if stars in [5,6]:
            STARS += ((stars,u'%s %s' % (stars,val_2)),)         
    return STARS 
    
MEALS = (
         ('ALL','не важно'),
         ('RO',_(u'RO - только комната')),
         ('BB',_(u'ВВ - завтраки')),
         ('HB',_(u'HB - завтрак/ужин')),
         ('FB',_(u'FB - завтрак/обед/ужин')),
         ('AI',_(u'ALL - Все включено')),
         )      
                      

class HotelsSearchForm(forms.Form):
    def __init__(self, *args, **kwargs):
    
        # supplier
        hs_choices = kwargs.pop('hs_choices', None)  
        
        # exchange
        exchange_choices = ()
        for exchange in Exchange.objects.all().order_by('id'):
            exchange_choices += ((exchange.pk,exchange.char_code),)  
                   
        super(HotelsSearchForm, self).__init__(*args, **kwargs)
    
        self.fields['destination'].widget.attrs['class'] = 'class_destination'
        
        # если форма не получила массив request.GET, то задаем диапазон дат - текущая дата + 7 дней
        if not args:
            self.fields['date_arrival'].initial=(datetime.datetime.now() + datetime.timedelta(days=14)).strftime('%d.%m.%Y')                   
            self.fields['date_departure'].initial=(datetime.datetime.now() + datetime.timedelta(days=28)).strftime('%d.%m.%Y')           

        self.fields['stars'].choices = get_stars()
        self.fields['child1'].choices = get_child_ages()
        self.fields['child2'].choices = get_child_ages()
        self.fields['child3'].choices = get_child_ages()
        self.fields['child4'].choices = get_child_ages()
        self.fields['child5'].choices = get_child_ages()
        
        if hs_choices:
            self.fields['supplier'].choices = (('ALL','*'),) + hs_choices 
        else:       
            self.fields['supplier'].choices = (('ALL','*'),)
            
        if exchange_choices:
            self.fields['exchange'].choices = exchange_choices 
            self.fields['exchange'].initial = 2
        else:       
            self.fields['exchange'].choices = (('2','USD'),)            
            
        self.fields['request_with'].widget=forms.HiddenInput()
        self.fields['request_value'].widget=forms.HiddenInput()             
        #self.fields['date_arrival'].widget.attrs['class'] = 'date_arrival'
        #self.fields['date_departure'].widget.attrs['class'] = 'date_departure'        
     
        #self.fields['date_arrival'].widget.attrs.update({'id' : 'datepicker5'})        
        #self.fields['date_departure'].widget.attrs.update({'id' : 'datepicker6'})  
 

    destination = forms.CharField(label=_(u'Место / название отеля'),error_messages={'required': _(u'Введите какой-либо текст, чтобы мы могли начать поиск.')},widget=forms.TextInput(attrs={'size':'70'}) )
    date_arrival = forms.DateField(label=_(u'Дата заезда'),widget=forms.TextInput(attrs={'size':'12'}),error_messages={'required': _(u'Введите дату заезда')},input_formats=('%d.%m.%Y',)) #widget=forms.DateInput(format='%d/%m/%Y')  
    date_departure = forms.DateField(label=_(u'Дата выезда'),widget=forms.TextInput(attrs={'size':'12'}),error_messages={'required': _(u'Введите дату выезда')},input_formats=('%d.%m.%Y',) )    
    quantity_adult = forms.ChoiceField(label=_(u'Взрослых'),choices=((x, x) for x in range(1,6)),error_messages={'required': _(u'Введите количество взрослых')}, initial=2)      
    quantity_child = forms.ChoiceField(label=_(u'Детей'),choices=((str(x), x) for x in range(0,6)),error_messages={'required': _(u'Введите количество детей')},required=False ) 
    child1 = forms.ChoiceField(required=False) 
    child2 = forms.ChoiceField(required=False)
    child3 = forms.ChoiceField(required=False)
    child4 = forms.ChoiceField(required=False)
    child5 = forms.ChoiceField(required=False)
    meal = forms.ChoiceField(label=_(u'Питание'),choices=MEALS,required=False)   
    stars = forms.MultipleChoiceField(label=_(u'Категория'), required=False) 
    supplier = forms.ChoiceField(label=_(u'Поставщик'),choices=(('ALL','*'),),)  
    exchange = forms.ChoiceField(label=_(u'Валюта'),choices=(('2','USD'),)) # pk 2 is USD in Exchange model     
    request_with = forms.CharField(widget=forms.TextInput(attrs={'size':'10','val':''}),label='',required=False,initial='RequestWith',)
    request_value = forms.CharField(widget=forms.TextInput(attrs={'size':'10'}),label='',required=False,initial='RequestValue',)
    
   
    def clean(self):
        
        cleaned_data = super(HotelsSearchForm, self).clean()
        quantity_child = cleaned_data.get('quantity_child')
        child1 = cleaned_data.get('child1', None)
        child2 = cleaned_data.get('child2', None) 
        child3 = cleaned_data.get('child3', None)   
        child4 = cleaned_data.get('child4', None)
        child5 = cleaned_data.get('child5', None) 

        if child1==None or child2==None or child3==None or child4==None or child5==None:
            self._errors['quantity_child'] = _(u'Укажите возраст детей.')        
        
        if quantity_child not in ['',0,None]:                                    
            if child1 in ['',0,None] and \
            child2 in ['',0,None] and \
            child3 in ['',0,None] and \
            child4 in ['',0,None] and \
            child5 in ['',0,None]:
                self._errors['quantity_child'] = _(u'Укажите возраст детей.')                            
        return cleaned_data            
    
       
class FormErrorList(ErrorList):
    def __unicode__(self):
        return self.as_divs()
    def as_divs(self):
        if not self: return u''
        error = u'<div class="hotel_search_form_errors">%s</div>' % ''.join([u'<div class="error">%s</div>' % e for e in self])
        return error   

        
class HolidayForm(forms.ModelForm):

    date = forms.DateField(input_formats=DATE_INPUT_FORMATS)
    class Meta:
        exclude = ('company')
        model = Holiday  

class HotelChoseForSync(forms.Form):
    
    hotel = forms.CharField(widget=forms.Select, label= '')
    hotel_booking = forms.CharField(required=False, widget=forms.Select, label= '')
    hotel_booking_id = forms.CharField(required=False, label= '') 
    approve = forms.BooleanField(required=False) 

class CountryChoseForSync(forms.ModelForm):
    class Meta:
        model = Hotel
        fields = ('country',)     


class HotelLoadForm(forms.Form):
    count = forms.IntegerField(required=False)
    start_index = forms.IntegerField(required=False)
    q = forms.CharField(required=False)
    
class HotelPages(forms.Form):
    page = forms.IntegerField()

CHILDPOLICY_COUNT_CHOICES = tuple([('', '')]+[(x, x) for x in xrange(1, 11)])

class RestrictionAccommodationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'childpolicy' in kwargs:
            ages = kwargs['childpolicy'].get_ages()
            for age in ages:
                self.base_fields.update({ age['title']: forms.ChoiceField(choices=CHILDPOLICY_COUNT_CHOICES, required=False) })
            del kwargs['childpolicy']
        super(RestrictionAccommodationForm, self).__init__(*args, **kwargs)
    
    
class AddRestrictionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if kwargs.get('for_obj') == 'B':
            self.base_fields.update({'restr_type': forms.ChoiceField(choices=(
                                                  ('', '--------'), 
                                                  ('minstay', 'Minstay'), 
                                                  ('guests', 'Guests'),
                                                  ('acc', 'Accommodation'),
                                                 ), label='Restriction type') })
            del kwargs['for_obj']
        if kwargs.get('for_obj') == 'EB':
            self.base_fields.update({'restr_type': forms.ChoiceField(choices=(
                                                  ('', '--------'), 
                                                  ('minstay', 'Minstay'), 
                                                  ('guests', 'Guests'),
                                                  ('d_type', 'Large text'), # в бонусах нет
                                                  ('acc', 'Accommodation'),
                                                 ), label='Restriction type') })
            del kwargs['for_obj']
        super(AddRestrictionForm, self).__init__(*args, **kwargs)
    
    minstay = forms.IntegerField(required=False)
    guests = forms.MultipleChoiceField(choices=(('HG', 'Honeymooner Guests'), ('JM', 'Just Married'),), required=False, widget=CheckboxSelectMultiple())
 
class HotelSyncForm(forms.Form):
    old_hotel = forms.IntegerField(label='', required=False)
    new_hotel = forms.IntegerField(label='', required=False)   
    
    
        