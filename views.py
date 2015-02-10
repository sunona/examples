# -*- coding: utf-8 -*-
import datetime
from datetime import timedelta
import time
import random
import re
import os
import base64, urllib2
import json
from copy import copy
from operator import itemgetter
from django.utils import simplejson     
from decimal import Decimal, ROUND_CEILING
from xml.etree.cElementTree import iterparse
from urllib import urlopen, unquote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.paginator import Paginator, EmptyPage
from django.core.urlresolvers import reverse
from django.db import connection
from django.db.models import Q
from django import forms
from django.forms.models import inlineformset_factory, modelformset_factory
from django.forms.formsets import formset_factory
from django.http import HttpResponseRedirect, Http404, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.defaultfilters import dictsort
from django.template.loader import render_to_string
from django.views.generic import list_detail
from django.utils.translation import ugettext_lazy as _
from django.utils.functional import curry
from django.views.generic.base import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from math import cos, degrees, radians

from bonuses.forms import PriceTypeForm
from bonuses.models import Bonus, EarlyBird, ComboBonus
from cancellation_policy.models import CancellationPolicy
from comments.models import Comment
from companies.models import Contragent, Company
from destination_stations.models import Airport
from exchange.models import Exchange 
from hotels.create_early_bird import CreateEarlyBird
from rate_codes.models import RateCode

from hotels.make_public_version import make_public_version
from hotels.make_dublicate import make_dublicate
from hotels.models import Hotel, Room, ChildPolicy, Accommodation, HotelStars, \
                          Period, Service, PeriodDates, Meal, HotelSupplier, \
                          accommodation_types, MealRate, RoomParams, StayPay, \
                          RoomRate, CompanyRoomParams, HotelSupplierHistory, \
                          ExtraBedRate, ServiceRate,  StayPayBonus, \
                          HOTEL_FEAUTURES_TYPE_CHOICES , ROOM_FEAUTURES_TYPE_CHOICES, \
                          HotelFeature, HotelFeatureCompany, HotelFeatureCompanySpecific, \
                          RoomFeature, RoomFeatureCompany, RoomFeatureCompanySpecific, \
                          HotelDescription, RoomDescription, HotelPhoto, HotelPhotoLang, \
                          HotelMostPopular, RestaurantAndBar, RestaurantAndBarFeature, \
                          RestaurantAndBarFeatureCompany, RestaurantAndBarFeatureCompanySpecific, \
                          HotelFile, HotelFileDescriptionLang, HotelSync, HotelVideo, \
                          HotelVideoLang, Company
                          
                          
from hotels.forms import HotelDatesEditForm, FormulaForm,\
                         AccommodationForm, CommandForm, PaxForm, HotelsForm, \
                         PeriodsForm, ServicesForm, MealsPeriodsForm, \
                         MealsForm, TransfersForm, HotelSupplierAddForm, \
                         StayPayForm, FormulaRoomsMealsForm, StayPaysForm, \
                         ServiceAddForm, RoomOrderForm, StayPayBonusForm, \
                         RelatedServicesForm, EarlyBirdAddForm, BirdCopyOptionsForm, \
                         HotelSupplierItemsFormset, CompanyRoomsForm, RoomsForm, \
                         EBRatesForm, AccommodationFormset, ServicesMealsRoomsForm, \
                         StayPaysBonusesForm, PeriodForm, PeriodDatesForm, FilterForm, \
                         HotelFeatureCompanySpecificForm, RoomFeatureCompanySpecificForm, \
                         HotelDescriptionForm, BaseHotelDescriptionFormSet, \
                         RoomDescriptionForm, BaseRoomDescriptionFormSet, \
                         HotelPhotoForm, BaseHotelPhotoFormSet, \
                         HotelPhotoDescriptionForm, BaseHotelPhotoDescriptionFormSet, \
                         AddRestaurantOrBarForm, RestaurantAndBarFeatureCompanySpecificForm, \
                         HotelFileForm, BaseHotelFileFormSet, HotelFileDescriptionForm, BaseHotelFileDescriptionFormSet, \
                         HotelChoseForSync, CountryChoseForSync, HotelLoadForm, \
                         HotelPages, AddRestrictionForm, RestrictionAccommodationForm, \
                         HotelVideoForm, HotelVideoDescriptionForm, \
                         BaseHotelVideoDescriptionFormSet , HotelSyncForm
                                                  
from hotels.formula_parsers import SetRateCSConditionedParser, \
                                   AddMealParser, ChMealParser, \
                                   AddRestrParser, SetRateCSParser, \
                                   ChildPolicyParser, AddSurchParser, \
                                   AddEarlyBirdParser, AddStayPayParser,  \
                                   AddServiceTaxParser, SetRateMlParser, \
                                   AddStayPayBonusParser, AddServiceParser
from xml_booking.models import Hotel as HotelBooking, Region as RegionBooking,\
                               City as CityBooking                                                                                               
from orders.models import  Accommodation as OrderAccommodation, Service as OrderService                           
from rate_codes.forms import AddHotelSupplierRateCodeForm
from rate_codes.models import HotelSupplierRateCode
from regions.models import Country, Resort, Area
from taxes.models import SalesTax, ConditionalTax
from transfers.models import Transfer
from user_catalog.models import UserCountry, UserResort, UserArea
from userprofiles.decorators import profile_permission_required 
from statistic.decorators import console_command_statistics
from hotels.search import get_companies_from_rate_code_chain
from hotels.cron import sync_booking_hotels, update_hotel_stars_info, \
                        fill_hotel_stars_info, fill_resort_parent
from regions.cron import add_multilang_resort_title, add_districts_to_resorts
from exchange.models import Exchange
from bonuses.forms import EarlyBirdsBonusForm
from partners.views import get_user_and_template


from regions.forms import ResortsSyncForm
from regions.models import Region, Resort, Country, Area, CountryPhoto
from trip.models import TripPoint
from xml_booking.models import Hotel as HotelBooking, Region as RegionBooking, City as CityBooking, \
                               District as DistrictBooking
from statistic.models import RequestStatistic     
from django.utils import simplejson                          
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.db import models
from models import * 
from django.db import connection, transaction
from django.db.models import get_model
from django.http import QueryDict 

def stat_country(request):                 #СТАТИСТИКА ПО СТРАНАМ
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
    
    begin=request.POST.get("begin")             #входной параметр для расчетов статистики по всем странам
    choosee=request.POST.get("country")         #входной параметр для расчетов статистики по одной стране
    country_iso=request.POST.get("country_iso") #входной параметр для расчета id страны (в шаблоне hotel_stat_country идет запрос на sync_hotels)
    
    if country_iso:                      # Получение id страны для отправки на sync_hotels
        country_iso = str(country_iso)
        country_iso = country_iso.strip()
        chosen_country = Country.objects.get(iso=country_iso)
        country_id = simplejson.dumps( chosen_country.id )
        return HttpResponse(country_id,
                mimetype='application/javascript') 
                 
    if request.method == 'POST' and begin:    # получение статистики по всем странам.
        i = int(request.POST['begin'])
        country_list = Country.objects.order_by('id')[i:i+1]
        if country_list:
            for country in country_list:
                list_stat_country = get_list_stat_country(country)
            if int(request.POST['begin'])==0:
                rendered = render_to_string('hotels/hotel_stat_country_first.html', {'list_stat_country':list_stat_country})
            else:
                rendered = render_to_string('hotels/hotel_stat_country_row.html', {'list_stat_country':list_stat_country}) 
            list_stat_country  = simplejson.dumps( rendered )
        else:
            rendered = 0  
            list_stat_country  = simplejson.dumps( rendered )
        return HttpResponse(list_stat_country,
                mimetype='application/javascript')  
                
    if request.method == 'POST' and choosee:                  #получение статистики по одной стране. Данные по старане берутся из формы
        form = CountryChoseForSync(request.POST)
        if form.is_valid():
            chosen_country = form.cleaned_data['country']
            country = Country.objects.get(title=chosen_country)
            list_stat_country = get_list_stat_country(country)
            rendered = render_to_string('hotels/hotel_stat_country_first.html', {'list_stat_country':list_stat_country})
            list_stat_country  = simplejson.dumps( rendered )
            return HttpResponse(list_stat_country,
                    mimetype='application/javascript')
        else:
            form = CountryChoseForSync()  
            return render_to_response('hotels/hotel_stat_country.html', 
                              {'form':form             
                               },                                            
                              context_instance=RequestContext(request))               
    form = CountryChoseForSync()  
    return render_to_response('hotels/hotel_stat_country.html', 
                              {'form':form             
                               },                                            
                              context_instance=RequestContext(request))
                              
def get_list_stat_country(country):          # Получаем статистику по стране
    list_stat_country = {}
    stat_country = {}
    hotel_unihotel = Hotel.objects.filter(country_id=country.id)
    hotel_booking = HotelBooking.objects.filter(cc1=country.iso)
    hotel_unihotel_count = hotel_unihotel.count()
    hotel_booking_count = hotel_booking.count()
    stat_country['hotel_unihotel_count'] = hotel_unihotel_count
    stat_country['hotel_booking_count'] = hotel_booking_count
    stat_country['country_title'] = country.title
    stat_country['country_iso'] = country.iso
    hotel_sinc_count = 0
    for hotel in hotel_unihotel:
        hotel_sinc = HotelBooking.objects.filter(hotel_id=hotel.id).count()
        hotel_sinc_count = hotel_sinc_count+hotel_sinc
    stat_country['hotel_unihotel_unique'] = hotel_unihotel_count-hotel_sinc_count
    stat_country['hotel_booking_unique'] = hotel_booking_count-hotel_sinc_count
    stat_country['hotel_sinc_count'] = hotel_sinc_count
    list_stat_country[0] = stat_country
    return list_stat_country
                           
                         
 

def del_all_restr(request, hotel_supplier_pk, for_obj=None):    
    # for_obj указывает тип ограничения: EB - earlybird или B - bonus
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
    
    try:
        hotel_supplier = HotelSupplier.objects.get(pk=hotel_supplier_pk)
    except:
        raise Http404
    
    if request.method == 'POST' and for_obj == 'EB':
        eb_ids = []
        eb_ids_post = request.POST.getlist('earlybirds')
        if eb_ids_post:
            for eb_id_post in eb_ids_post:
                try:
                    eb_id = int(eb_id_post)
                    eb_ids.append(eb_id)
                except:
                    pass
        earlybirds = EarlyBird.objects.filter(pk__in=eb_ids, \
                              hotel_supplier__company=hotel_supplier.company)
        if earlybirds.count(): 
            earlybirds.update(d_type=0, accommodation='', minstay=None, guests='')
            messages.success(request, 'Restrictions removed successfully')
            return HttpResponseRedirect(reverse('hotel_edit', args=[hotel_supplier_pk]))
    if request.method == 'POST' and for_obj == 'B':
        b_ids = []
        b_ids_post = request.POST.getlist('bonuses')
        if b_ids_post:
            for b_id_post in b_ids_post:
                try:
                    b_id = int(b_id_post)
                    b_ids.append(b_id)
                except:
                    pass
        bonuses = Bonus.objects.filter(pk__in=b_ids, \
                              hotel_supplier__company=hotel_supplier.company)
        if bonuses.count(): 
            bonuses.update(accommodation='', minstay=None, guests='')
            messages.success(request, 'Restrictions removed successfully')
            return HttpResponseRedirect(reverse('hotel_edit', args=[hotel_supplier_pk]))
    raise Http404

CHILDPOLICY_COUNT_CHOICES = tuple([(x, x) for x in xrange(1, 11)])

def add_restr_form(request, hotel_supplier_pk, for_obj=None):
    
    # for_obj указывает тип ограничения: EB - earlybird или B - bonus
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
    
    try:
        hotel_supplier = HotelSupplier.objects.get(pk=hotel_supplier_pk)
    except:
        return HttpResponse('Server error')
    
    childpolicy = hotel_supplier.childpolicy
    ages = childpolicy.get_ages()
    
    AccommodationFormset = formset_factory(form=RestrictionAccommodationForm, extra=3, max_num=3)
    AccommodationFormset.form = staticmethod(curry(RestrictionAccommodationForm, childpolicy=childpolicy))
    
    earlybirds = []
    bonuses = []
    
    if request.method == 'POST':
        form = AddRestrictionForm(request.POST, for_obj=for_obj)
        formset = AccommodationFormset(request.POST)
        if form.is_valid() and formset.is_valid():
            form_cd = form.cleaned_data
            formset_cd = formset.cleaned_data
            restr_type = form_cd['restr_type']
            if for_obj == 'EB':
                eb_ids = []
                eb_ids_post = request.POST.getlist('earlybirds')
                if eb_ids_post:
                    for eb_id_post in eb_ids_post:
                        try:
                            eb_id = int(eb_id_post)
                            eb_ids.append(eb_id)
                        except:
                            pass
                earlybirds = EarlyBird.objects.filter(pk__in=eb_ids, hotel_supplier__company=hotel_supplier.company)
            if for_obj == 'B':
                b_ids = []
                b_ids_post = request.POST.getlist('bonuses')
                if b_ids_post:
                    for b_id_post in b_ids_post:
                        try:
                            b_id = int(b_id_post)
                            b_ids.append(b_id)
                        except:
                            pass
                bonuses = Bonus.objects.filter(pk__in=b_ids, hotel_supplier__company=hotel_supplier.company)    
                
            if earlybirds or bonuses:
                if restr_type == 'minstay':
                    try:
                        minstay = int(form_cd.get('minstay'))
                    except:
                        minstay = None
                    if minstay:
                        if earlybirds:
                            earlybirds.update(minstay=minstay)
                        if bonuses:
                            bonuses.update(minstay=minstay)
                    return HttpResponse(simplejson.dumps({'success': 'reload'}), mimetype='application/json')
                elif restr_type == 'guests':
                    guests = form_cd.get('guests')
                    if guests:
                        guests_str = '+'.join(guests)
                        if earlybirds:
                            earlybirds.update(guests=guests_str)
                        if bonuses:
                            bonuses.update(guests=guests_str)
                    return HttpResponse(simplejson.dumps({'success': 'reload'}), mimetype='application/json')
                elif restr_type == 'd_type':
                    # только для earlybird
                    if earlybirds:
                        earlybirds.update(d_type=1)   
                    return HttpResponse(simplejson.dumps({'success': 'reload'}), mimetype='application/json')
                elif restr_type == 'acc':
                    cp_list = childpolicy.ages.split(';')
                    cp_dict = {}
                    # справочник соответствия названия и индекса возрастной политики
                    for index, cp in enumerate(cp_list, 1):
                        title, age = cp.split('=')
                        cp_dict[title] = index
                    cp_post = formset_cd
                    restr_list = []
                    for childpolicy in cp_post:
                        childpolicy_list = []
                        for key, value in cp_dict.items():
                            if key in childpolicy:
                                # количество представителей определенной
                                # возрастной политики
                                quantity = childpolicy[key]
                                # индекс возрасной политики
                                index = value
                                if quantity:
                                    cp_str = 'x'.join([str(quantity), str(index)])
                                    childpolicy_list.append(cp_str)
                        if childpolicy_list:
                            childpolicy_str = '+'.join(childpolicy_list)
                            restr_list.append(childpolicy_str)
                    accommodation = 'or'.join(restr_list)
                    if earlybirds:
                        earlybirds.update(accommodation=accommodation)
                    if bonuses:
                        bonuses.update(accommodation=accommodation)
                    return HttpResponse(simplejson.dumps({'success': 'reload'}), mimetype='application/json')           
                return HttpResponse(simplejson.dumps({'success': 'success'}), mimetype='application/json')
            else:
                return HttpResponse(simplejson.dumps({'errors': 'Server error'}), mimetype='application/json')
            
        else:
            return HttpResponse(simplejson.dumps({'errors': form.errors}), mimetype='application/json')
        
    else:
        form = AddRestrictionForm(for_obj=for_obj)
        formset = AccommodationFormset()
       
    hotel = hotel_supplier.hotel
    
    return render_to_response('hotels/add_restr_form.html',
                             {'hotel_supplier_pk': hotel_supplier_pk,
                              'form': form, 'formset': formset,
                              'childpolicy': childpolicy, 'for_obj': for_obj,
                              }, 
                              context_instance=RequestContext(request))

def add_bonus_form(request, hotel_supplier_pk):
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    try:
        hotel_supplier = HotelSupplier.objects.get(pk=hotel_supplier_pk)
    except:
        raise Http404
        
    hotel = hotel_supplier.hotel
    
    rooms = hotel.room_set.filter(Q(company__isnull=True)|Q(company=company))  \
                          .order_by('id')
    
    meals = Meal.objects.filter(hotel_supplier=hotel_supplier, active=True)  
    
    currency_qs = Exchange.objects.all()
    currency_list = currency_qs.values_list('char_code', flat=True)
    hs_exchange = hotel_supplier.exchange.char_code or None
    
    return render_to_response('hotels/add_bonus_form.html',
                             {'hotel_supplier_pk': hotel_supplier_pk,
                              'rooms': rooms, 'meals': meals,
                              'currency_list': currency_list,
                              'hs_exchange': hs_exchange}, 
                              context_instance=RequestContext(request)) 

def add_compulsory_service(request, hotel_supplier_pk):
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
    
    return render_to_response('hotels/add_compulsory_service.html',
                             {'hotel_supplier_pk': hotel_supplier_pk}, 
                              context_instance=RequestContext(request))
                              
def add_compulsory_service_rate(request, hotel_supplier_pk, service_pk):
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
    
    try:
        hotel_supplier = HotelSupplier.objects.get(pk=hotel_supplier_pk)
        service = Service.objects.get(pk=service_pk)
    except:
        return HttpResponse('')
    
    rates = service.rates
    if rates:
        rates = rates.split(';')
    else:
        rates = []
    
    currency_qs = Exchange.objects.all()
    currency_list = currency_qs.values_list('char_code', flat=True)
    hs_exchange = hotel_supplier.exchange.char_code or None
    cs_exchange = service.exchange or hs_exchange
        
    childpolicy = hotel_supplier.childpolicy
    
    if childpolicy:
        ages = childpolicy.ages.split(';')
    else:
        ages = []
    
    rates_dict = []    
    for i, age in enumerate(ages):
        rate = ''
        if len(ages) == len(rates):
            rate = rates[i]
        rates_dict.append((age, rate))
    return render_to_response('hotels/add_compulsory_service_rate.html',
                             {'hotel_supplier_pk': hotel_supplier_pk,
                              'currency_list': currency_list, 
                              'cs_exchange': cs_exchange,
                              'ages': ages, 'rates_dict': rates_dict }, 
                              context_instance=RequestContext(request))

def add_bird_form(request, hotel_supplier_pk):
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    return render_to_response('hotels/add_bird_form.html',
                             {"hotel_supplier_pk": hotel_supplier_pk}, 
                              context_instance=RequestContext(request))
               
                              
def set_stay_pay_form(request, hotel_supplier_pk):

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    return render_to_response('hotels/set_stay_pay_form.html',
                             {"hotel_supplier_pk": hotel_supplier_pk}, 
                              context_instance=RequestContext(request))


def show_popular_hotels_ajax(request, page=1, start=False):
    
    arrival_date = datetime.date.today() + datetime.timedelta(days=14)
    departure_date = arrival_date + datetime.timedelta(days=14)
    
    context_dict = {'arrival_date': arrival_date, 
                    'departure_date': departure_date} 
    
    if start:
        # стартовый результат рекомендуемых отелей
        
        if not request.partner:
            return HttpResponse('')
            
        partner = request.partner
        company_id = partner.company_id
        
        try:
            company = Company.objects.get(pk=company_id)
        except:
            return HttpResponse('')
            
        hotels = HotelMostPopular.objects.filter(company=company)
        
        if not hotels:
            return HttpResponse('')
            
        country_ids = hotels.values_list('hotel__resort__country__id', flat=True)
        country_ids = list(set(country_ids))
         
        resort_ids = []
        
        if len(country_ids) != 1:
            country_ids_for_random = country_ids  
            random.shuffle(country_ids_for_random)
            country_ids = country_ids_for_random[0:4]
            for country_id in country_ids:
                country_hotels = hotels.filter(hotel__resort__country__id=country_id)
                country_resort_ids = country_hotels.values_list('hotel__resort__id', flat=True)
                resort_ids_for_random = list(set(country_resort_ids))
                random.shuffle(resort_ids_for_random)
                resort_id = resort_ids_for_random[0]
                resort_ids.append(resort_id)
        else:
            country_id = country_ids[0]
            country_hotels = hotels.filter(hotel__resort__country__id=country_id)
            country_resort_ids = country_hotels.values_list('hotel__resort__id', flat=True)
            resort_ids_for_random = list(set(country_resort_ids))
            random.shuffle(resort_ids_for_random)
            resort_ids = resort_ids_for_random[0:4]         
        
        resorts = []
        
        for resort_id in resort_ids:
            resort = Resort.objects.get(pk=resort_id)
            resort_hotels = hotels.filter(hotel__resort=resort)[0:2]
            resorts.append({'resort': resort, 'hotels': resort_hotels})
        
        context_dict['company'] = company
        context_dict['resorts'] = resorts
        
        return render_to_response('hotels/hotels_search/show_popular_hotels_ajax_start.html',
                                  context_dict, 
                                  context_instance=RequestContext(request))
        
    else:
        # результат по выбранному курорту
        if request.method == "POST" and "resort_id" in request.POST and "company_id" in request.POST:
            if "page" in request.POST:
                page = int(request.POST["page"])
            resort_id = int(request.POST["resort_id"])
            company_id = int(request.POST["company_id"])
            try: 
                resort = Resort.objects.get(id=resort_id)
                company = Company.objects.get(id=company_id)
                hotels = HotelMostPopular.objects.filter(hotel__resort__id=resort.id, company=company).order_by('hotel__title')
            except:
                return HttpResponse('')
        else:
            return HttpResponse('')
                    
        page_obj = Paginator(hotels, 8)
        try:
            object_list = page_obj.page(page)
        except EmptyPage:
            return HttpResponse('')
        object_list = list(object_list.object_list)
    
        context_dict['hotels'] = object_list
        context_dict['resort'] = resort
        context_dict['company'] = company
        context_dict['page_obj'] = page_obj
        context_dict['current_page_num'] = page
    
        return render_to_response('hotels/hotels_search/show_popular_hotels_ajax.html',
                                  context_dict, 
                                  context_instance=RequestContext(request))
                         
        
def set_checkinout(request, hotel_supplier_pk):
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
    
    try:
        hotel_supplier = HotelSupplier.objects.actual(
                ).select_related('childpolicy', 'hotel', 
                                 'supplier', 'rate_code'
                ).get(pk=hotel_supplier_pk, company=company)
    except HotelSupplier.DoesNotExist:
        raise Http404

    form = HotelDatesEditForm(instance=hotel_supplier)
    return render_to_response('hotels/set_checkinout_form.html', 
                             {'hotel_supplier_pk': hotel_supplier_pk,
                              'form': form},                               
                              context_instance=RequestContext(request))


def set_agepolicy_form(request, hotel_supplier_pk):

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
    
    hotel_supplier = HotelSupplier.objects.get(pk=hotel_supplier_pk)
    
    try:
        childpolicy = hotel_supplier.childpolicy.ages
        childpolicy_splitted = childpolicy.split(';')
    except:
        childpolicy_splitted = None
        messages.error(request, _(u'Add childpolicy first'))    
    
    return render_to_response('hotels/set_agepolicy_form.html', 
                             {'hotel_supplier_pk': hotel_supplier_pk,
                              'childpolicy_splitted': childpolicy_splitted
                              },                               
                              context_instance=RequestContext(request))

def add_meal_form(request, hotel_supplier_pk):

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    return render_to_response('hotels/add_meal_form.html', 
                              {'hotel_supplier_pk': hotel_supplier_pk},                               
                              context_instance=RequestContext(request))

def add_room_form(request, hotel_supplier_pk):

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    hotel_supplier=HotelSupplier.objects.get(pk=hotel_supplier_pk)
    return render_to_response('hotels/add_room_form.html', 
                              {'hotel_supplier_pk': hotel_supplier_pk,
                               'hotel_supplier': hotel_supplier},                               
                              context_instance=RequestContext(request))

###############################################
### Hotel Photo

def hotel_photo(request, hotel_pk, company_pk):       
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404
    company = user.company
    
    try:
        hotel = Hotel.objects.get(pk=hotel_pk)
        company_created_photos = Company.objects.get(pk=company_pk) # компания которая завела photos
    except:
        raise Http404
        
    company_official_supplier = hotel.company_official_supplier    
        
    HotelPhotoFormSet = modelformset_factory(HotelPhoto, 
                                             formset=BaseHotelPhotoFormSet,
                                             form = HotelPhotoForm,
                                             extra=1) 

    HotelPhotoFormSet.form = staticmethod(curry(HotelPhotoForm, 
                                                company_id = company.id, 
                                                hotel_id = hotel.id))
    
    hotel_photo_qs = HotelPhoto.objects.filter(hotel=hotel,company=company_created_photos)
    
    hotel_photo_scroll_qs = HotelPhoto.objects.filter(hotel=hotel)
    
    formset = HotelPhotoFormSet(prefix='photo', queryset=hotel_photo_qs)
                                                        
    if request.method == 'POST' and company_created_photos == company:
        
        formset = HotelPhotoFormSet(request.POST, request.FILES, prefix='photo',queryset=hotel_photo_qs)
        if formset.is_valid():
            for form in formset.forms:
                if form.is_valid():
                    instance = form.save(commit=False) 
                    instance.hotel = hotel
                    instance.company = company

                    if instance.photo:
                        instance.save()
                else:
                    break   
            else:        
                messages.success(request, u'Photo saved successfully.')
                return HttpResponseRedirect('')
    
    photo_form = HotelPhotoForm(prefix='photo-##')
    photo_form_text = render_to_string('hotels/hotel_photo_form.html',{'form': photo_form})        
    photo_form_text = photo_form_text.replace('\n', '').replace('\r', '').replace('"', "'")
    
    return render_to_response('hotels/hotel_photo.html', 
                              {
                              'formset':formset,
                              'company':company,
                              'company_created_photos':company_created_photos,
                              'hotel':hotel,  
                              'photo_form_text':photo_form_text,
                              'hotel_photo_scroll_qs':hotel_photo_scroll_qs,                                                                                   
                              },                               
                              context_instance=RequestContext(request))

def hotel_photo_delete(request,hotel_photo_pk):

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    if request.method != u'POST':
        return HttpResponse(u'Error')
   
    try:
        hotel_photo = HotelPhoto.objects.get(pk = hotel_photo_pk, company=company) 
    except:
       raise Http404
             
    hotel_photo.delete()
    
    return HttpResponse('Success')

def hotel_photo_description(request, hotel_pk, company_pk, hotel_photo_pk):       
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    try:
        hotel = Hotel.objects.get(pk=hotel_pk)
        company_created_descriptions = Company.objects.get(pk = company_pk) # компания которая завела description    
        hotel_photo = HotelPhoto.objects.get(pk=hotel_photo_pk)
    except:
        raise Http404

    HotelPhotoDescriptionFormSet = modelformset_factory(HotelPhotoLang, 
                                                  formset=BaseHotelPhotoDescriptionFormSet,
                                                  form = HotelPhotoDescriptionForm,
                                                  extra=1)  
                                                  
    qs = HotelPhotoLang.objects.filter(hotel_photo=hotel_photo,hotel_photo__company = company_created_descriptions)                                                   
    if request.method == 'POST' and company_created_descriptions == company:
        formset = HotelPhotoDescriptionFormSet(prefix='description', queryset=qs, data=request.POST)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.hotel_photo = hotel_photo
                instance.save()
            messages.success(request, u'Hotel photo description saved successfully.') 
            return HttpResponseRedirect('')   
    else:
        formset = HotelPhotoDescriptionFormSet(prefix='description', queryset=qs)

    description_form = HotelPhotoDescriptionForm(prefix='description-##')
    description_form_text = render_to_string('hotels/hotel_photo_description_form.html',{'form': description_form})        
    description_form_text = description_form_text.replace('\n', '').replace('\r', '').replace('"', "'")
    
    return render_to_response('hotels/hotel_photo_description.html', 
                              {
                              'formset':formset,
                              'company':company,
                              'company_created_descriptions':company_created_descriptions,
                              'hotel':hotel,
                              'hotel_photo':hotel_photo,  
                              'description_form_text':description_form_text,                                                                                   
                              },                               
                              context_instance=RequestContext(request))

def hotel_photo_description_delete(request,hotel_photo_description_pk):

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    if request.method != u'POST':
        return HttpResponse(u'Error')
   
    try:
        hotel_photo_description = HotelPhotoLang.objects.get(pk = hotel_photo_description_pk) 
    except:
       raise Http404
             
    hotel_photo_description.delete()
    
    return HttpResponse('Success')
    
### End Hotel Photo
###############################################
    
###############################################
### Hotel Video                                

def hotel_video(request, hotel_pk, company_pk):       
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404
    company = user.company
    
    try:
        hotel = Hotel.objects.get(pk=hotel_pk)
        company_created_videos = Company.objects.get(pk=company_pk) # компания которая завела video
    except:
        raise Http404
        
    company_official_supplier = hotel.company_official_supplier    
    
    HotelVideoFormSet = modelformset_factory(HotelVideo, 
                                             form = HotelVideoForm,
                                             extra=1)
    HotelVideoFormSet.form = staticmethod(curry(HotelVideoForm, 
                                                company_id = company.id, 
                                                hotel_id = hotel.id))
    hotel_video_qs = HotelVideo.objects.filter(hotel=hotel,company=company_created_videos)

    formset_video = HotelVideoFormSet(prefix='video', queryset=hotel_video_qs)
                                                        
    if request.method == 'POST' and company_created_videos == company:
        
        formset_video = HotelVideoFormSet(request.POST, prefix='video',queryset=hotel_video_qs)
        if formset_video.is_valid():
            for form in formset_video:
                instance_video = form.save(commit=False)
                instance_video.hotel = hotel
                instance_video.company = company
                if company_official_supplier == company:
                    instance_video.public = True
                instance_video.save()
            else:        
                messages.success(request, u'Video saved successfully.')
                return HttpResponseRedirect('')
    
    video_form = HotelVideoForm(prefix='video-##')
    video_form_text = render_to_string('hotels/hotel_video_form.html',{'video_form': video_form})        
    video_form_text = video_form_text.replace('\n', '').replace('\r', '').replace('"', "'")

    return render_to_response('hotels/hotel_video.html', 
                              {
                              'formset_video':formset_video,
                              'company':company,
                              'company_created_videos':company_created_videos,
                              'hotel':hotel,  
                              'video_form_text':video_form_text,                                                                                  
                              },                               
                              context_instance=RequestContext(request))

def hotel_video_delete(request,hotel_video_pk):

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    if request.method != u'POST':
        return HttpResponse(u'Error')
   
    try:
        hotel_video = HotelVideo.objects.get(pk = hotel_video_pk, company=company) 
    except:
       raise Http404
             
    hotel_video.delete()
    
    return HttpResponse('Success')

def hotel_video_description(request, hotel_pk, company_pk, hotel_video_pk):       
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    try:
        hotel = Hotel.objects.get(pk=hotel_pk)
        company_created_descriptions = Company.objects.get(pk = company_pk) # компания которая завела description    
        hotel_video = HotelVideo.objects.get(pk=hotel_video_pk)
    except:
        raise Http404

    HotelVideoDescriptionFormSet = modelformset_factory(HotelVideoLang,
                                                  formset = BaseHotelVideoDescriptionFormSet,  
                                                  form = HotelVideoDescriptionForm,
                                                  extra=1)  
                                                  
    qs = HotelVideoLang.objects.filter(hotel_video=hotel_video,hotel_video__company = company_created_descriptions)                                                   
    if request.method == 'POST' and company_created_descriptions == company:
        formset = HotelVideoDescriptionFormSet(prefix='description', queryset=qs, data=request.POST)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.hotel_video = hotel_video
                instance.save()
            messages.success(request, u'Hotel video description saved successfully.') 
            return HttpResponseRedirect('')   
    else:
        formset = HotelVideoDescriptionFormSet(prefix='description', queryset=qs)

    description_form = HotelVideoDescriptionForm(prefix='description-##')
    description_form_text = render_to_string('hotels/hotel_video_description_form.html',{'form': description_form})        
    description_form_text = description_form_text.replace('\n', '').replace('\r', '').replace('"', "'")
    
    return render_to_response('hotels/hotel_video_description.html', 
                              {
                              'formset':formset,
                              'company':company,
                              'company_created_descriptions':company_created_descriptions,
                              'hotel':hotel,
                              'hotel_video':hotel_video,  
                              'description_form_text':description_form_text,                                                                                   
                              },                               
                              context_instance=RequestContext(request))

def hotel_video_description_delete(request,hotel_video_description_pk):

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    if request.method != u'POST':
        return HttpResponse(u'Error')
   
    try:
        hotel_video_description = HotelVideoLang.objects.get(pk = hotel_video_description_pk) 
    except:
       raise Http404
             
    hotel_video_description.delete()
    
    return HttpResponse('Success')

### End Hotel Video
#####################################   
    

def hotel_features(request, hotel_pk, company_pk):       
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
        
    try:
        hotel = Hotel.objects.get(pk=hotel_pk)    
        company_created_features = Company.objects.get(pk = company_pk) # компания которая завела features
    except:
        raise Http404
               
    hotel_feature_company, created = HotelFeatureCompany.objects.get_or_create(company=company, hotel=hotel)         
  
    feature_type_lst = []
    for feature_type in HOTEL_FEAUTURES_TYPE_CHOICES:
        qs = HotelFeature.objects.filter(feature_type=feature_type[0]).order_by('text')
        print qs
        feature_type_lst.append({'hotel_feature_lst':qs,'feature_type':feature_type})

    
    initial_from_request_post_if_errors = None # если в форме ошибки
    
    if request.method == 'POST':  
        form = HotelFeatureCompanySpecificForm(data=request.POST,hotel_feature_company=hotel_feature_company)
        if form.is_valid():
            hotel_features = form.cleaned_data['hotel_feature']

            # удаляем текущие
            HotelFeatureCompanySpecific.objects.filter(hotel_feature_company=hotel_feature_company).delete()

            for hotel_feature in hotel_features:

                if hotel_feature.data_type == 'integer':
                    if request.POST['hotel_feature_integer_%s' % hotel_feature.id]:
                        obj = HotelFeatureCompanySpecific(hotel_feature=hotel_feature,
                                                          hotel_feature_company=hotel_feature_company,
                                                          text = request.POST['hotel_feature_integer_%s' % hotel_feature.id]) 
                        obj.save()
 
                if hotel_feature.data_type == 'float':
                    if request.POST['hotel_feature_float_%s' % hotel_feature.id]:
                        obj = HotelFeatureCompanySpecific(hotel_feature=hotel_feature,
                                                          hotel_feature_company=hotel_feature_company,
                                                          text = request.POST['hotel_feature_float_%s' % hotel_feature.id]) 
                        obj.save() 

                if hotel_feature.data_type == 'text':
                    if request.POST['hotel_feature_text_%s' % hotel_feature.id]:
                        obj = HotelFeatureCompanySpecific(hotel_feature=hotel_feature,
                                                          hotel_feature_company=hotel_feature_company,
                                                          text = request.POST['hotel_feature_text_%s' % hotel_feature.id]) 
                        obj.save() 
                
                if hotel_feature.data_type == 'date':
                    if request.POST['hotel_feature_date_%s' % hotel_feature.id]:
                        obj = HotelFeatureCompanySpecific(hotel_feature=hotel_feature,
                                                          hotel_feature_company=hotel_feature_company,
                                                          text = request.POST['hotel_feature_date_%s' % hotel_feature.id]) 
                        obj.save()
            
                if hotel_feature.data_type == 'boolean':
                    obj = HotelFeatureCompanySpecific(hotel_feature=hotel_feature,hotel_feature_company=hotel_feature_company) 
                    obj.save()                        

                if hotel_feature.data_type == 'choice':
                    hotel_feature_choice = request.POST.get('hotel_feature_choice_%s' % hotel_feature.id)
                    if hotel_feature_choice: 
                        obj = HotelFeatureCompanySpecific(hotel_feature=hotel_feature,
                                                          hotel_feature_company=hotel_feature_company,
                                                          choice_text = request.POST['hotel_feature_choice_%s' % hotel_feature.id]) 
                        obj.save()

                if hotel_feature.data_type == 'multiplechoice':
                    hotel_feature_multiplechoice = request.POST.getlist('hotel_feature_multiplechoice_%s' % hotel_feature.id)            
                    choice_text = ';'.join(hotel_feature_multiplechoice)
                    if hotel_feature_multiplechoice:
                        obj = HotelFeatureCompanySpecific(hotel_feature=hotel_feature,
                                                          hotel_feature_company=hotel_feature_company,
                                                          choice_text = choice_text) 
                        obj.save()

                if hotel_feature.data_type == 'ftandmetr':
                    hotel_feature_ftandmetr = request.POST.get('hotel_feature_ftandmetr_%s' % hotel_feature.id)
                    if hotel_feature_ftandmetr:
                        hotel_feature_ftandmetr_select = request.POST.get('hotel_feature_ftandmetr_select_%s' % hotel_feature.id) 

                        if hotel_feature_ftandmetr_select == 'metr':
                            hotel_feature_ftandmetr = '%s_metr' % hotel_feature_ftandmetr
                        elif hotel_feature_ftandmetr_select == 'ft':
                            hotel_feature_ftandmetr = '%s_ft' % hotel_feature_ftandmetr
                                
                        obj = HotelFeatureCompanySpecific(hotel_feature=hotel_feature,
                                                          hotel_feature_company=hotel_feature_company,
                                                          text = hotel_feature_ftandmetr) 
                        obj.save()

                if hotel_feature.data_type == 'ftandmetrsquare':
                    hotel_feature_ftandmetr = request.POST.get('hotel_feature_ftandmetrsquare_%s' % hotel_feature.id)
                    if hotel_feature_ftandmetr:
                        hotel_feature_ftandmetr_select = request.POST.get('hotel_feature_ftandmetrsquare_select_%s' % hotel_feature.id) 

                        if hotel_feature_ftandmetr_select == 'metr':
                            hotel_feature_ftandmetr = '%s_metr' % hotel_feature_ftandmetr
                        elif hotel_feature_ftandmetr_select == 'ft':
                            hotel_feature_ftandmetr = '%s_ft' % hotel_feature_ftandmetr
                                
                        obj = HotelFeatureCompanySpecific(hotel_feature=hotel_feature,
                                                          hotel_feature_company=hotel_feature_company,
                                                          text = hotel_feature_ftandmetr) 
                        obj.save()
                               
            messages.success(request, u'Hotel services is changed successfully')
            
        else:
            initial_from_request_post_if_errors = dict(request.POST)    
    else:
        form = HotelFeatureCompanySpecificForm(hotel_feature_company=hotel_feature_company)
    
    year_now = int(datetime.date.today().year)
    years_list = range(year_now-150, year_now+5) 
    date_now = datetime.date.today()

    return render_to_response('hotels/hotel_features.html', 
                              {
                              'form':form, 
                              'company':company,
                              'company_created_features':company_created_features,
                              'hotel':hotel,
                              'feature_type_lst':feature_type_lst,
                              'initial_from_request_post_if_errors':initial_from_request_post_if_errors,
                              'years_list': years_list,
                              'date_now': date_now,                                                                                        
                              },                               
                              context_instance=RequestContext(request))
    


def hotel_features_fancybox(request, hotel_pk, company_pk):       
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
        
    hotel = Hotel.objects.get(pk=hotel_pk)
    
    company = user.company
    company_created_features = Company.objects.get(pk = company_pk) # компания которая завела features
      
    try:
        hotel_feature_company = HotelFeatureCompany.objects.get(company=company_created_features, hotel=hotel)         
    except:
        return HttpResponse('No features added for this hotel - %s' % hotel)   

    feature_type_lst = []
    for feature_type in HOTEL_FEAUTURES_TYPE_CHOICES:
        qs = HotelFeatureCompanySpecific.objects.filter(hotel_feature_company = hotel_feature_company, hotel_feature_company__hotel = hotel, hotel_feature__feature_type = feature_type[0])
        feature_type_lst.append({'hotel_feature_company_lst':qs,'feature_type':feature_type})
            
    for elem in feature_type_lst:
        if len(elem['hotel_feature_company_lst']) > 0:
            break
    else:         
       return HttpResponse('No features added for this hotel - %s' % hotel)
     
    return render_to_response('hotels/hotel_features_fancybox.html',
                              {
                              'company':company,
                              'company_created_features':company_created_features,
                              'hotel':hotel,
                              'feature_type_lst':feature_type_lst,
                              },                               
                              context_instance=RequestContext(request))



def hotel_description_edit(request, hotel_pk, company_pk):       
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    try:
        hotel = Hotel.objects.get(pk=hotel_pk)
    except:
        raise Http404
                
    if hotel.company_official_supplier:
    # Проверяем есть ли официальный поставщик свойств отеля
        company_created_descriptions = company    
    else:    
    # компания которая завела description
        try:
            company_created_descriptions = Company.objects.get(pk=company_pk) 
        except:
            raise Http404
    
    HotelDescriptionFormSet = modelformset_factory(HotelDescription, 
                                                   formset=BaseHotelDescriptionFormSet,
                                                   form = HotelDescriptionForm,
                                                   extra=1)    
                                                   
    qs = HotelDescription.objects.filter(hotel=hotel, company = company_created_descriptions)
                                                      
    if request.method == 'POST' and company_created_descriptions == company:
        formset = HotelDescriptionFormSet(prefix='description', data=request.POST, queryset = qs)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.hotel = hotel
                instance.company = company
                try:
                    instance.save()
                except:
                    continue                    
            messages.success(request, u'Hotel description saved successfully.') 
            return HttpResponseRedirect('')   
    else:
        formset = HotelDescriptionFormSet(prefix='description', queryset = qs)

    description_form = HotelDescriptionForm(prefix='description-##')
    description_form_text = render_to_string('hotels/hotel_description_form.html',{'form': description_form})        
    description_form_text = description_form_text.replace('\n', '').replace('\r', '').replace('"', "'")
    
    return render_to_response('hotels/hotel_description.html', 
                              {
                              'formset':formset,
                              'company':company,
                              'company_created_descriptions':company_created_descriptions,
                              'hotel':hotel,  
                              'description_form_text':description_form_text,                                                                                   
                              },                               
                              context_instance=RequestContext(request))



def hotel_description_get(request, hotel_supplier_pk=None, company_pk=None, hotel_pk=None, **kwargs):       

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
    
    
    if hotel_supplier_pk:
        hotel_supplier = HotelSupplier.objects.get(pk=hotel_supplier_pk)
        hotel = hotel_supplier.hotel
    elif company_pk and hotel_pk:
        # для вызова адресов с именем get_hotel_description_by_company       
        hotel = Hotel.objects.get(pk=hotel_pk)
        company = Company.objects.get(pk=company_pk)
       
    # Cначала смотрим есть ли у нас такое описание           
    try:
        hotel_description = HotelDescription.objects.get(hotel=hotel, company=company, language__code = request.LANGUAGE_CODE)
    except:
        try:
            hotel_description = HotelDescription.objects.get(hotel=hotel, company=company, language__code = 'en')    
        except:
            hotel_description = None    

    if not hotel_description:
        # Если такого описания нет, то смотрим вверх по цепочке   
        # к изначальной компании которая завела description          
        if hotel_supplier_pk:
            companies_lst = get_companies_from_rate_code_chain(hotel_supplier, company)[0]
            for company in reversed(companies_lst):
                try:
                    hotel_description = HotelDescription.objects.get(hotel=hotel, company=company, language__code = request.LANGUAGE_CODE)
                    break
                except:
                    try:
                        hotel_description = HotelDescription.objects.get(hotel=hotel, company=company, language__code = 'en')    
                        break
                    except:
                        continue
           
        # В последнюю очередь проверяем есть ли официальный поставщик свойств отеля
        if not hotel_description:
            if hotel.company_official_supplier:
                company_created_descriptions = hotel.company_official_supplier
                try:
                    hotel_description = HotelDescription.objects.get(hotel=hotel, company=company_created_descriptions, language__code = request.LANGUAGE_CODE)    
                except:
                    try:
                        hotel_description = HotelDescription.objects.get(hotel=hotel, company=company_created_descriptions, language__code = 'en')
                    except:
                        hotel_description = None
                                                          
        if not hotel_description:
            if 'call_from_hotel_search_ajax_response' in kwargs:
                return ''
            else:             
                return HttpResponse('No description added for this hotel - %s' % hotel)   

    if 'call_from_hotel_search_ajax_response' in kwargs:
        return hotel_description
    else:        
        return render_to_response('hotels/hotel_description_fancybox.html', 
                              {
                              'company':company,
                              'hotel':hotel,  
                              'hotel_description':hotel_description,                                                                                   
                              },                               
                              context_instance=RequestContext(request))
                       
                              
def hotel_photo_fancybox(request, company_pk, hotel_pk, **kwargs):       
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
    
    hotel = Hotel.objects.get(pk=hotel_pk)
    
    company_created_photos = Company.objects.get(pk = company_pk) # компания которая завела фотографии
    
    companies_ids = HotelPhoto.objects.filter(hotel=hotel).values_list('company', flat=True).distinct()
    companies_ids = list(companies_ids)
    companies_sort_lst = []
    if hotel.company_official_supplier:
        company_official_supplier = hotel.company_official_supplier # компания официальный поставщик фотографий
        for i, company_id in enumerate(companies_ids):
            if company_official_supplier.id == company_id:
                companies_sort_lst.append(company_id)
                del companies_ids[i]
    else:
        company_official_supplier = None
    
    for company_id in companies_ids:
        companies_sort_lst.append(company_id)
    
    qs = HotelPhoto.objects.filter(hotel=hotel, company__in=companies_sort_lst)
    
    return render_to_response('hotels/hotel_photo_fancybox.html', 
                              {
                              'company':company,
                              'hotel':hotel,  
                              'qs':qs,                                                                                   
                              },                               
                              context_instance=RequestContext(request))
                              

                              
def hotel_description_delete(request,hotel_description_pk):

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    if request.method != u'POST':
        return HttpResponse(u'Error')
   
    try:
        hotel_description = HotelDescription.objects.get(pk = hotel_description_pk, company=company) 
    except:
       raise Http404
             
    hotel_description.delete()
    
    return HttpResponse('Success')


def hotel_file(request, hotel_pk, company_pk):       
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404
    company = user.company
    
    try:
        hotel = Hotel.objects.get(pk=hotel_pk)
        company_created_files = Company.objects.get(pk = company_pk) # компания которая завела files
    except:
        raise Http404
        
    HotelFileFormSet = modelformset_factory(HotelFile, 
                                             formset=BaseHotelFileFormSet,
                                             form = HotelFileForm,
                                             extra=1) 

    HotelFileFormSet.form = staticmethod(curry(HotelFileForm, company_id = company.id, hotel_id = hotel.id))
    
    hotel_file_qs = HotelFile.objects.filter(hotel=hotel,company=company_created_files)                                                  
    if request.method == 'POST' and company_created_files == company:

        formset = HotelFileFormSet(request.POST, request.FILES, prefix='file',queryset=hotel_file_qs)
        if formset.is_valid():

            for form in formset.forms:
                if form.is_valid():
                    instance = form.save(commit=False) 
                    instance.hotel = hotel
                    instance.company = company
                    if instance.file_path:
                        instance.save()        
                else:
                    break   
            else:        
                messages.success(request, u'File saved successfully.')
                return HttpResponseRedirect('')
            
    else:
        formset = HotelFileFormSet(prefix='file', queryset=hotel_file_qs)

    file_form = HotelFileForm(prefix='file-##')
    file_form_text = render_to_string('hotels/hotel_file_form.html',{'form': file_form})        
    file_form_text = file_form_text.replace('\n', '').replace('\r', '').replace('"', "'")
    return render_to_response('hotels/hotel_file.html', 
                              {
                              'formset':formset,
                              'company':company,
                              'company_created_files':company_created_files,
                              'hotel':hotel,  
                              'file_form_text':file_form_text,
                              'hotel_file_qs':hotel_file_qs,                                                                            
                              },                               
                              context_instance=RequestContext(request))


def hotel_file_delete(request,hotel_file_pk):

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    if request.method != u'POST':
        return HttpResponse(u'Error')
   
    try:
        hotel_file = HotelFile.objects.get(pk = hotel_file_pk, company=company) 
    except:
       raise Http404
             
    hotel_file.delete()
    
    return HttpResponse('Success')
    

def hotel_file_description(request, hotel_pk, company_pk, hotel_file_pk):       
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    try:
        hotel = Hotel.objects.get(pk=hotel_pk)
        company_created_descriptions = Company.objects.get(pk = company_pk) # компания которая завела description    
        hotel_file = HotelFile.objects.get(pk=hotel_file_pk)
    except:
        raise Http404
    
    HotelFileDescriptionFormSet = modelformset_factory(HotelFileDescriptionLang, 
                                                  formset=BaseHotelFileDescriptionFormSet,
                                                  form = HotelFileDescriptionForm,
                                                  extra=1)  
                                                  
    qs = HotelFileDescriptionLang.objects.filter(hotel_file=hotel_file,hotel_file__company = company_created_descriptions)                                                   
    if request.method == 'POST' and company_created_descriptions == company:
        formset = HotelFileDescriptionFormSet(prefix='description', queryset=qs, data=request.POST)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.hotel_file = hotel_file
                instance.save()
            messages.success(request, u'Hotel file description saved successfully.') 
            return HttpResponseRedirect('')   
    else:
        formset = HotelFileDescriptionFormSet(prefix='description', queryset=qs)

    description_form = HotelFileDescriptionForm(prefix='description-##')
    description_form_text = render_to_string('hotels/hotel_file_description_form.html',{'form': description_form})        
    description_form_text = description_form_text.replace('\n', '').replace('\r', '').replace('"', "'")
    
    return render_to_response('hotels/hotel_file_description.html', 
                              {
                              'formset':formset,
                              'company':company,
                              'company_created_descriptions':company_created_descriptions,
                              'hotel':hotel,
                              'hotel_file':hotel_file,  
                              'description_form_text':description_form_text,                                                                                   
                              },                               
                              context_instance=RequestContext(request))
                              

def hotel_file_description_delete(request,hotel_file_description_pk):

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    if request.method != u'POST':
        return HttpResponse(u'Error')
   
    try:
        hotel_file_description = HotelFileDescriptionLang.objects.get(pk = hotel_file_description_pk) 
    except:
       raise Http404
             
    hotel_file_description.delete()
    
    return HttpResponse('Success')                              

   
def room_features(request, room_pk, company_pk):       
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    try:
        room = Room.objects.get(pk=room_pk)
        company_created_features = Company.objects.get(pk = company_pk) # компания которая завела features
    except:
        raise Http404   
           
    if company == company_created_features:
        room_feature_company, created = RoomFeatureCompany.objects.get_or_create(company=company, room=room)         
    else:
        try:
            room_feature_company = RoomFeatureCompany.objects.get(company=company_created_features, room=room) 
        except:
            raise Http404    

    feature_type_lst = []
    for feature_type in ROOM_FEAUTURES_TYPE_CHOICES:
        qs = RoomFeature.objects.filter(feature_type=feature_type[0]).order_by('text')
        feature_type_lst.append({'room_feature_lst':qs,'feature_type':feature_type})
            
    
    initial_from_request_post_if_errors = None # если в форме ошибки
    
    if request.method == 'POST':  
        form = RoomFeatureCompanySpecificForm(data=request.POST,room_feature_company=room_feature_company)
        if form.is_valid():
            room_features = form.cleaned_data['room_feature']

            # удаляем текущие
            RoomFeatureCompanySpecific.objects.filter(room_feature_company=room_feature_company).delete()

            for room_feature in room_features:                 
                if room_feature.data_type == 'integer':
                    if request.POST['room_feature_integer_%s' % room_feature.id]:
                        obj = RoomFeatureCompanySpecific(room_feature=room_feature,
                                                          room_feature_company=room_feature_company,
                                                          text = request.POST['room_feature_integer_%s' % room_feature.id]) 
                        obj.save()
 
                if room_feature.data_type == 'float':
                    if request.POST['room_feature_float_%s' % room_feature.id]:
                        obj = RoomFeatureCompanySpecific(room_feature=room_feature,
                                                          room_feature_company=room_feature_company,
                                                          text = request.POST['room_feature_float_%s' % room_feature.id]) 
                        obj.save() 

                if room_feature.data_type == 'text':
                    if request.POST['room_feature_text_%s' % room_feature.id]:
                        obj = RoomFeatureCompanySpecific(room_feature=room_feature,
                                                          room_feature_company=room_feature_company,
                                                          text = request.POST['room_feature_text_%s' % room_feature.id]) 
                        obj.save() 
                
                if room_feature.data_type == 'date':
                    if request.POST['room_feature_date_%s' % room_feature.id]:
                        obj = RoomFeatureCompanySpecific(room_feature=room_feature,
                                                          room_feature_company=room_feature_company,
                                                          text = request.POST['room_feature_date_%s' % room_feature.id]) 
                        obj.save()
            
                if room_feature.data_type == 'boolean':
                    obj = RoomFeatureCompanySpecific(room_feature=room_feature,room_feature_company=room_feature_company) 
                    obj.save()                        

                if room_feature.data_type == 'choice':
                    room_feature_choice = request.POST.get('room_feature_choice_%s' % room_feature.id)
                    if room_feature_choice: 
                        obj = RoomFeatureCompanySpecific(room_feature=room_feature,
                                                          room_feature_company=room_feature_company,
                                                          choice_text = request.POST['room_feature_choice_%s' % room_feature.id]) 
                        obj.save()

                if room_feature.data_type == 'multiplechoice':
                    room_feature_multiplechoice = request.POST.getlist('room_feature_multiplechoice_%s' % room_feature.id)            
                    choice_text = ';'.join(room_feature_multiplechoice)
                    if room_feature_multiplechoice:
                        obj = RoomFeatureCompanySpecific(room_feature=room_feature,
                                                          room_feature_company=room_feature_company,
                                                          choice_text = choice_text) 
                        obj.save()

                if room_feature.data_type == 'ftandmetr':
                    room_feature_ftandmetr = request.POST.get('room_feature_ftandmetr_%s' % room_feature.id)
                    if room_feature_ftandmetr:
                        room_feature_ftandmetr_select = request.POST.get('room_feature_ftandmetr_select_%s' % room_feature.id) 

                        if room_feature_ftandmetr_select == 'metr':
                            room_feature_ftandmetr = '%s_metr' % room_feature_ftandmetr
                        elif room_feature_ftandmetr_select == 'ft':
                            room_feature_ftandmetr = '%s_ft' % room_feature_ftandmetr
                                
                        obj = RoomFeatureCompanySpecific(room_feature=room_feature,
                                                          room_feature_company=room_feature_company,
                                                          text = room_feature_ftandmetr) 
                        obj.save()

                if room_feature.data_type == 'ftandmetrsquare':
                    room_feature_ftandmetr = request.POST.get('room_feature_ftandmetrsquare_%s' % room_feature.id)
                    if room_feature_ftandmetr:
                        room_feature_ftandmetr_select = request.POST.get('room_feature_ftandmetrsquare_select_%s' % room_feature.id) 

                        if room_feature_ftandmetr_select == 'metr':
                            room_feature_ftandmetr = '%s_metr' % room_feature_ftandmetr
                        elif room_feature_ftandmetr_select == 'ft':
                            room_feature_ftandmetr = '%s_ft' % room_feature_ftandmetr
                                
                        obj = RoomFeatureCompanySpecific(room_feature=room_feature,
                                                          room_feature_company=room_feature_company,
                                                          text = room_feature_ftandmetr) 
                        obj.save()
                               
            messages.success(request, u'Room services is changed successfully')
            
        else:
            initial_from_request_post_if_errors = dict(request.POST)    
    else:
        form = RoomFeatureCompanySpecificForm(room_feature_company=room_feature_company)
    return render_to_response('hotels/room_features.html', 
                              {
                              'form':form,
                              'company':company,
                              'company_created_features':company_created_features,
                              'room':room,
                              'feature_type_lst':feature_type_lst,
                              'initial_from_request_post_if_errors':initial_from_request_post_if_errors,                                                                                        
                              },                               
                              context_instance=RequestContext(request))


def room_features_fancybox(request, room_pk, company_pk, **kwargs):  

    if 'without_auth' in kwargs:
        pass
    else:    
        user = request.user
        if not hasattr(user, 'company'):
            raise Http404        
        company = user.company
        
    room = Room.objects.get(pk=room_pk)

    company_created_features = Company.objects.get(pk = company_pk) # компания которая завела features
    
    try:         
        room_feature_company = RoomFeatureCompany.objects.get(company=company_created_features, room=room)     
    except:
        if request.method == 'POST' and 'call_from_hotel_rooms' in request.POST:
            return HttpResponse('') 
        else:       
            return HttpResponse('No features added for this room - %s' % room)   
        
    feature_type_lst = []
    for feature_type in ROOM_FEAUTURES_TYPE_CHOICES:        
        qs = RoomFeatureCompanySpecific.objects.filter(room_feature_company=room_feature_company, room_feature__feature_type = feature_type[0])   
        feature_type_lst.append({'room_feature_company_lst':qs,'feature_type':feature_type})
   
    for elem in feature_type_lst:
        if len(elem['room_feature_company_lst']) > 0:
            break
    else:        
        return HttpResponse('No features added for this room - %s' % room)     
    
    return render_to_response('hotels/room_features_fancybox.html',
                              {
                              'company_created_features':company_created_features,
                              'room':room,
                              'feature_type_lst':feature_type_lst,
                              },                               
                              context_instance=RequestContext(request))
                              
                              
def room_description(request, company_pk, room_pk):       
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    try:
        room = Room.objects.get(pk=room_pk)
        company_created_descriptions = Company.objects.get(pk = company_pk) # компания которая завела description
    except:
        raise Http404

    RoomDescriptionFormSet = modelformset_factory(RoomDescription, 
                                                  formset=BaseRoomDescriptionFormSet,
                                                  form = RoomDescriptionForm,
                                                  extra=1)       
    
    qs = RoomDescription.objects.filter(room=room, company = company_created_descriptions)

    if request.method == 'POST' and company_created_descriptions == company:
        formset = RoomDescriptionFormSet(prefix='description', data=request.POST, queryset=qs)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.room = room
                instance.company = company
                try:
                    instance.save()
                except:
                    continue    
            messages.success(request, u'Room description saved successfully.')    
    else:
        formset = RoomDescriptionFormSet(prefix='description', queryset=qs)

    description_form = RoomDescriptionForm(prefix='description-##')
    description_form_text = render_to_string('hotels/room_description_form.html',{'form': description_form})        
    description_form_text = description_form_text.replace('\n', '').replace('\r', '').replace('"', "'")
    
    return render_to_response('hotels/room_description.html', 
                              {
                              'formset':formset,
                              'company':company,
                              'company_created_descriptions':company_created_descriptions,
                              'room':room,  
                              'description_form_text':description_form_text,                                                                                   
                              },                               
                              context_instance=RequestContext(request))


def room_description_fancybox(request, company_pk, room_pk, **kwargs):       
    
    if 'without_auth' in kwargs:
        pass
    else:    
        user = request.user
        if not hasattr(user, 'company'):
            raise Http404        
        company = user.company
    
    room = Room.objects.get(pk=room_pk)
  
    company_created_descriptions = Company.objects.get(pk = company_pk) # компания которая завела description
       
    qs = RoomDescription.objects.filter(room=room, company = company_created_descriptions)

    if len(qs) == 0:
        return HttpResponse('No description added for this room - %s' % room)   
               
    return render_to_response('hotels/room_description_fancybox.html', 
                              {
                              'company_created_descriptions':company_created_descriptions,
                              'room':room,  
                              'qs':qs,                                                                                   
                              },                               
                              context_instance=RequestContext(request))


def room_description_delete(request,room_description_pk):

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    if request.method != u'POST':
        return HttpResponse(u'Error')
   
    try:
        room_description = RoomDescription.objects.get(pk = room_description_pk, company=company) 
    except:
       raise Http404
             
    room_description.delete()
    
    return HttpResponse('Success')


def app_edit(request, id):
    application = get_object_or_404(Application, pk=id)

    if request.method == 'POST':
        form = ApplicationForm(request.POST, instance=application)
        formset = Application2ServerFormSet(request.POST, instance=application)

        if form.is_valid() and formset.is_valid():
            saved_application = form.save()
            formset.save()

            return HttpResponseRedirect(reverse(
                'proj.views.app_show',
                args=(saved_application.pk,)
            ))


    return render(request, 'app_edit.html', {'form': form, 'formset': formset})


### Рестораны и бары

def restaurant_and_bar(request, hotel_pk, company_pk):
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
    
    try:
        hotel = Hotel.objects.get(pk=hotel_pk)
        company_created_restaurants = Company.objects.get(pk = company_pk) # компания которая завела description
    except:
        raise Http404 
    
    
    restaurants_and_bars = RestaurantAndBar.objects.filter(hotel=hotel, company=company)
    return render_to_response('hotels/restaurant_and_bar.html', 
                              {'restaurants_and_bars': restaurants_and_bars,
                               'company': company,
                               'company_created_restaurants': company_created_restaurants,
                               'hotel': hotel},                               
                              context_instance=RequestContext(request))
    
    
def add_restaurant_and_bar(request, hotel_pk, company_pk):
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
    
    try:
        hotel = Hotel.objects.get(pk=hotel_pk)
    except:
        raise Http404
        
    if request.method == "POST":
        form = AddRestaurantOrBarForm(data=request.POST, hotel_pk=hotel.id, company_pk=company.id)
        if form.is_valid():
            restaurant_or_bar = form.save()
            messages.success(request, u'%s added successfully.' % form.cleaned_data["restaurant_or_bar"].capitalize())
            return HttpResponseRedirect(reverse('restaurant_and_bar', kwargs={'hotel_pk':hotel.id, 'company_pk':company.id}))
    else:
        form = AddRestaurantOrBarForm(hotel_pk=hotel.id, company_pk=company.id)
    
    
    return render_to_response('hotels/add_restaurant_or_bar.html', 
                              {'form': form,
                               'company': company,
                               'hotel': hotel,
                              },                               
                              context_instance=RequestContext(request))


def restaurant_and_bar_features(request, hotel_pk, company_pk, restaurant_and_bar_pk):       
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    try:
        hotel = Hotel.objects.get(pk=hotel_pk)
        company_created_features = Company.objects.get(pk = company_pk) # компания которая завела features
        restaurant_and_bar = RestaurantAndBar.objects.get(pk=restaurant_and_bar_pk)
    except:
        raise Http404


    if company == company_created_features:
        restaurant_and_bar_feature_company, created = RestaurantAndBarFeatureCompany.objects.get_or_create(company=company, restaurant_and_bar=restaurant_and_bar)         
    else:
        try:
            restaurant_and_bar_feature_company = RestaurantAndBarFeatureCompany.objects.get(company=company_created_features, restaurant_and_bar=restaurant_and_bar) 
        except:
            raise Http404    
    
    restaurant_and_bar_features_qs = RestaurantAndBarFeature.objects.all().order_by('text')
            
    
    initial_from_request_post_if_errors = None # если в форме ошибки
    
    if request.method == 'POST':  
        form = RestaurantAndBarFeatureCompanySpecificForm(data=request.POST,restaurant_and_bar_feature_company=restaurant_and_bar_feature_company)
        if form.is_valid():
            restaurant_and_bar_features = form.cleaned_data['restaurant_and_bar_feature']

            # удаляем текущие
            RestaurantAndBarFeatureCompanySpecific.objects.filter(restaurant_and_bar_feature_company=restaurant_and_bar_feature_company).delete()

            for restaurant_and_bar_feature in restaurant_and_bar_features:                 
                if restaurant_and_bar_feature.data_type == 'integer':
                    if request.POST['restaurant_and_bar_feature_integer_%s' % restaurant_and_bar_feature.id]:
                        obj = RestaurantAndBarFeatureCompanySpecific(restaurant_and_bar_feature=restaurant_and_bar_feature,
                                                          restaurant_and_bar_feature_company=restaurant_and_bar_feature_company,
                                                          text = request.POST['restaurant_and_bar_feature_integer_%s' % restaurant_and_bar_feature.id]) 
                        obj.save()
 
                if restaurant_and_bar_feature.data_type == 'float':
                    if request.POST['restaurant_and_bar_feature_float_%s' % restaurant_and_bar_feature.id]:
                        obj = RestaurantAndBarFeatureCompanySpecific(restaurant_and_bar_feature=restaurant_and_bar_feature,
                                                          restaurant_and_bar_feature_company=restaurant_and_bar_feature_company,
                                                          text = request.POST['restaurant_and_bar_feature_float_%s' % restaurant_and_bar_feature.id]) 
                        obj.save() 

                if restaurant_and_bar_feature.data_type == 'text':
                    if request.POST['restaurant_and_bar_feature_text_%s' % restaurant_and_bar_feature.id]:
                        obj = RestaurantAndBarFeatureCompanySpecific(restaurant_and_bar_feature=restaurant_and_bar_feature,
                                                          restaurant_and_bar_feature_company=restaurant_and_bar_feature_company,
                                                          text = request.POST['restaurant_and_bar_feature_text_%s' % restaurant_and_bar_feature.id]) 
                        obj.save() 
                
                if restaurant_and_bar_feature.data_type == 'date':
                    if request.POST['restaurant_and_bar_feature_date_%s' % restaurant_and_bar_feature.id]:
                        obj = RestaurantAndBarFeatureCompanySpecific(restaurant_and_bar_feature=restaurant_and_bar_feature,
                                                          restaurant_and_bar_feature_company=restaurant_and_bar_feature_company,
                                                          text = request.POST['restaurant_and_bar_feature_date_%s' % restaurant_and_bar_feature.id]) 
                        obj.save()
            
                if restaurant_and_bar_feature.data_type == 'boolean':
                    obj = RestaurantAndBarFeatureCompanySpecific(restaurant_and_bar_feature=restaurant_and_bar_feature,restaurant_and_bar_feature_company=restaurant_and_bar_feature_company) 
                    obj.save()                        

                if restaurant_and_bar_feature.data_type == 'choice':
                    restaurant_and_bar_feature_choice = request.POST.get('restaurant_and_bar_feature_choice_%s' % restaurant_and_bar_feature.id)
                    if restaurant_and_bar_feature_choice: 
                        obj = RestaurantAndBarFeatureCompanySpecific(restaurant_and_bar_feature=restaurant_and_bar_feature,
                                                          restaurant_and_bar_feature_company=restaurant_and_bar_feature_company,
                                                          choice_text = request.POST['restaurant_and_bar_feature_choice_%s' % restaurant_and_bar_feature.id]) 
                        obj.save()

                if restaurant_and_bar_feature.data_type == 'multiplechoice':
                    restaurant_and_bar_feature_multiplechoice = request.POST.getlist('restaurant_and_bar_feature_multiplechoice_%s' % restaurant_and_bar_feature.id)            
                    choice_text = ';'.join(restaurant_and_bar_feature_multiplechoice)
                    if restaurant_and_bar_feature_multiplechoice:
                        obj = RestaurantAndBarFeatureCompanySpecific(restaurant_and_bar_feature=restaurant_and_bar_feature,
                                                          restaurant_and_bar_feature_company=restaurant_and_bar_feature_company,
                                                          choice_text = choice_text) 
                        obj.save()

                if restaurant_and_bar_feature.data_type == 'ftandmetr':
                    restaurant_and_bar_feature_ftandmetr = request.POST.get('restaurant_and_bar_feature_ftandmetr_%s' % restaurant_and_bar_feature.id)
                    if restaurant_and_bar_feature_ftandmetr:
                        restaurant_and_bar_feature_ftandmetr_select = request.POST.get('restaurant_and_bar_feature_ftandmetr_select_%s' % restaurant_and_bar_feature.id) 

                        if restaurant_and_bar_feature_ftandmetr_select == 'metr':
                            restaurant_and_bar_feature_ftandmetr = '%s_metr' % restaurant_and_bar_feature_ftandmetr
                        elif restaurant_and_bar_feature_ftandmetr_select == 'ft':
                            restaurant_and_bar_feature_ftandmetr = '%s_ft' % restaurant_and_bar_feature_ftandmetr
                                
                        obj = RestaurantAndBarFeatureCompanySpecific(restaurant_and_bar_feature=restaurant_and_bar_feature,
                                                          restaurant_and_bar_feature_company=restaurant_and_bar_feature_company,
                                                          text = restaurant_and_bar_feature_ftandmetr) 
                        obj.save()

                if restaurant_and_bar_feature.data_type == 'ftandmetrsquare':
                    restaurant_and_bar_feature_ftandmetr = request.POST.get('restaurant_and_bar_feature_ftandmetrsquare_%s' % restaurant_and_bar_feature.id)
                    if restaurant_and_bar_feature_ftandmetr:
                        restaurant_and_bar_feature_ftandmetr_select = request.POST.get('restaurant_and_bar_feature_ftandmetrsquare_select_%s' % restaurant_and_bar_feature.id) 

                        if restaurant_and_bar_feature_ftandmetr_select == 'metr':
                            restaurant_and_bar_feature_ftandmetr = '%s_metr' % restaurant_and_bar_feature_ftandmetr
                        elif restaurant_and_bar_feature_ftandmetr_select == 'ft':
                            restaurant_and_bar_feature_ftandmetr = '%s_ft' % restaurant_and_bar_feature_ftandmetr
                                
                        obj = RestaurantAndBarFeatureCompanySpecific(restaurant_and_bar_feature=restaurant_and_bar_feature,
                                                          restaurant_and_bar_feature_company=restaurant_and_bar_feature_company,
                                                          text = restaurant_and_bar_feature_ftandmetr) 
                        obj.save()
                               
            messages.success(request, u'%s services is changed successfully' % restaurant_and_bar.restaurant_or_bar.capitalize())
            
        else:
            initial_from_request_post_if_errors = dict(request.POST)  
            messages.error(request, u'%s' % form.errors)  
    else:
        form = RestaurantAndBarFeatureCompanySpecificForm(restaurant_and_bar_feature_company=restaurant_and_bar_feature_company)

    return render_to_response('hotels/restaurant_and_bar_features.html', 
                              {
                              'form':form,
                              'hotel':hotel,
                              'company':company,
                              'company_created_features': company_created_features,
                              'restaurant_and_bar':restaurant_and_bar,
                              'restaurant_and_bar_features_qs':restaurant_and_bar_features_qs,
                              'initial_from_request_post_if_errors':initial_from_request_post_if_errors,                                                                                        
                              },                               
                              context_instance=RequestContext(request))


def restaurant_and_bar_delete(request, hotel_pk, company_pk, restaurant_and_bar_pk):
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
    
    try:
        restaurant_and_bar = RestaurantAndBar.objects.get(pk=restaurant_and_bar_pk, company=company)
    except:
        messages.error(request, u'You can delete only own restaurant')
        return HttpResponseRedirect(reverse('restaurant_and_bar',kwargs={'hotel_supplier_pk':hotel_supplier_pk}))     
    
    restaurant_and_bar.delete()
    messages.success(request, u'You successfully delete restaurant')
    
    return HttpResponseRedirect(reverse('restaurant_and_bar',kwargs={'hotel_pk':hotel_pk,'company_pk':company_pk}))

### конец рестораны и бары

def get_periods(hotel_supplier, timely=True):
    
    periods = []
    qs = PeriodDates.objects.select_related('period', 'period__f_exchange').filter(period__hotel_supplier=hotel_supplier)
    if timely:
        qs = qs.filter(date_to__gte=datetime.date.today())
    else:
        qs = qs.filter(date_to__lt=datetime.date.today())
    if qs:
        periods_tmp = list(qs)
        if len(periods_tmp) > 1:
            first_period = periods_tmp[0]
            last_period = periods_tmp[-1]
            start_date = first_period.date_from
            end_date = first_period.date_to
            prev_period = first_period
            time_delta = datetime.timedelta(days=1)
            periods.append(first_period)
            for period in periods_tmp[1:]:
                if prev_period.date_to + time_delta < period.date_from:
                    periods.append({'date_from': prev_period.date_to + time_delta, 
                        'date_to': period.date_from - time_delta,
                        'type': 'gap'
                    })
                periods.append(period)
                prev_period = period
        else:
            periods = periods_tmp
    return periods

    
def more_periods(request, hotel_supplier_pk, template_name='hotels/more_periods.html'):
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company
    
    try:
        hotel_supplier = HotelSupplier.objects.actual().get(pk=hotel_supplier_pk, 
                                                            company=company)
    except HotelSupplier.DoesNotExist:
        raise Http404

    periods = get_periods(hotel_supplier, False)
    try:
        num = int(request.GET.get('periods_count')) + 2
    except:
        num = 2

    return render_to_response(template_name, 
                              {'periods': periods, 
                               'num': num,},
                              context_instance=RequestContext(request))

def view_bird_accommodations(request, room, hotel_supplier):
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    supplier = hotel_supplier.supplier
    supplier_pk = supplier.pk
    childpolicy = hotel_supplier.childpolicy

    try:
        room_params = RoomParams.objects.get(room=room, 
                                             hotel_supplier=hotel_supplier, 
                                             company=company)
        max_pax = room_params.max_pax
    except RoomParams.DoesNotExist:    
        room_params = None
        max_pax = None

    types = []
    
    if not childpolicy:
        raise Http404
    if childpolicy:
        childpolicy_ages = childpolicy.get_ages()
        for i in range(1, len(childpolicy_ages)+1):
            types.append('age_type_%s_count' % i)
        
    if max_pax and max_pax in range(1, 11):
        initial = get_initial(max_pax, types, room.pk, hotel_supplier.pk, company.pk)
    else:
        initial = get_initial(10, types, room.pk, hotel_supplier.pk, company.pk)

    return render_to_response('hotels/view_bird_accommodations.html', 
                              {'room': room, 
                               'hotel_supplier': hotel_supplier,
                               'childpolicy': childpolicy,
                               'hotel': room.hotel, 
                               'supplier': supplier,
                               'initial': initial, 
                               'types': types,
                               'childpolicy_ages': childpolicy_ages,
                               'max_pax': max_pax,},
                              context_instance=RequestContext(request))


def min_age_and_occupancy_ajax(request, room_pk, company_pk):

    results = {}

    user = request.user
    if not hasattr(user, 'company'):
        results['error'] = u'You are not authorized.'
        return HttpResponse(simplejson.dumps(results),mimetype='application/json')         
    company = user.company

    # Разбираем POST массив
    min_age_group = request.POST.get('min_age_group')
        
    if min_age_group and len(min_age_group) > 4:
        results['error'] = u'Min age group must be 4 symbols long.'
        return HttpResponse(simplejson.dumps(results),mimetype='application/json')        
    occupancy = request.POST.get('occupancy')
    
    try:          
        room = Room.objects.get(pk = room_pk, company_id = company_pk)
        room.min_age_group = min_age_group
        room.occupancy = occupancy        
        room.save()
        results['success'] = u'You successfully saved data.'
    except Exception,e:
        results['error'] = u'Your company is not owner of this room.'    

    return HttpResponse(simplejson.dumps(results),mimetype='application/json')    
    


def get_key_list(types, values):
    key_list = [0, 0, 0, 0]
    if 'age_type_1_count' in types:
        key_list[0] = values.get('age_type_1_count', 0)
    if 'age_type_2_count' in types:
        key_list[1] = values.get('age_type_2_count', 0)
    if 'age_type_3_count' in types:
        key_list[2]  = values.get('age_type_3_count', 0)
    if 'age_type_4_count' in types:
        key_list[3] = values.get('age_type_4_count', 0)
    return tuple(key_list)


def get_initial(all, types, object_id, hotel_supplier_pk, company_pk):
    initial = []
    types_len = len(types)

    formuls = {}
    if object_id:
        try:
            accommodations = Accommodation.objects.filter(
                room__pk=object_id, 
                hotel_supplier__pk=hotel_supplier_pk, 
                company__pk=company_pk)
        except:
            accommodations = None
    else:
        accommodations = None

    if accommodations:
        for accommodation in accommodations:
            key = accommodation.age_types_count
            formuls[key] = accommodation.formula

    if types_len == 1:
        for i in range(1, all+1):
            initial_item = {types[0]: i, 'all': i}
            if object_id:
                key_list = get_key_list(types, initial_item)
                key = ';%s;%s;%s;%s;' % key_list
                initial_item.update({'formula': formuls.get(key, '')})
            initial.append(initial_item)

    if types_len == 2:
        for i in range(1, all+1):
            for j in range(i+1):
                item_0 = j
                item_1 = i-j
                initial_item = {types[0]: item_0, types[1]: item_1, 'all': i}
                if object_id:
                    key_list = get_key_list(types, initial_item)
                    key = ';%s;%s;%s;%s;' % key_list
                    initial_item.update({'formula': formuls.get(key, '')})
                initial.append(initial_item)

    if types_len == 3:
        for i in range(1, all+1):
            for j in range(i+1):
                for f in range(j+1):
                    item_0 = f
                    item_1 = j - item_0
                    item_2 = i - item_1 - item_0
                    initial_item = {types[0]: item_0, types[1]: item_1, types[2]: item_2, 'all': i}
                    
                    if object_id:
                        key_list = get_key_list(types, initial_item)
                        key = ';%s;%s;%s;%s;' % key_list
                        initial_item.update({'formula': formuls.get(key, '')})
                    initial.append(initial_item)

    if types_len == 4:
        for i in range(1, all+1):
            for j in range(i+1):
                for f in range(j+1):
                    for k in range(f+1):
                        item_0 = k
                        item_1 = f - item_0
                        item_2 = j - item_1 - item_0
                        item_3 = i - item_2  - item_1 - item_0
                        initial_item = {types[0]:item_0, types[1]: item_1, 
                                types[2]:item_2, types[3]: item_3, 'all': i}
                        if object_id:
                            key_list = get_key_list(types, initial_item)
                            key = ';%s;%s;%s;%s;' % key_list
                            initial_item.update({'formula': formuls.get(key, '')})
                        initial.append(initial_item)
    return initial


def set_periods_rate(request, childpolicy, periods, rooms, formula, type):
    if not type.lower() in (u'eb', u'rb'):
        raise Http404

    formula_error = False
    items = formula.split(';')
    if len(items) > 1:
        exchange_code = items[-1]
        ages_values = items[0:-1]
        ages = childpolicy.get_ages()
        if len(ages) != len(ages_values):
            formula_error = True
        else:
            for rate in ages_values:
                try:
                    rate_dec = Decimal(rate)
                except:
                    formula_error = True
                    break
            try:
                exchange = Exchange.objects.get(char_code=exchange_code)
            except Exchange.DoesNotExist:
                formula_error = True
            if not formula_error:
                rates_str = u';'.join(ages_values)
                added = False

                #build extra bed rates refs
                extra_bed_rates_ref = {}
                qs = ExtraBedRate.objects.filter(period__in=periods, 
                                                 room__in=rooms, 
                                                 type=type[0].upper())
                for rate in qs:
                    key = u'%d|%d' % (rate.period_id, rate.room_id)
                    extra_bed_rates_ref[key] = rate

                #save rates
                for period in periods:
                    for room in rooms:
                        key = u'%d|%d' % (period.pk, room.pk)
                        extra_bed_rate = extra_bed_rates_ref.get(key)
                        if not extra_bed_rate:
                            extra_bed_rate = ExtraBedRate(type=type[0].upper(), 
                                                          period=period, 
                                                          room=room)
                            added = True

                        extra_bed_rate.rates = rates_str
                        extra_bed_rate.exchange = exchange
                        extra_bed_rate.save()

                        #update history log
                        history_item = HotelSupplierHistory(
                            hotel_supplier_id=period.hotel_supplier_id)
                        history_item.user = request.user
                        history_item.content_object = extra_bed_rate
                        history_item.object_repr = u'%s %s-rates %s %s' % \
                            (period.title, type.upper(), rates_str, exchange_code)
                        if added:
                            history_item.action = u'A'
                        else:
                            history_item.action = u'C'
                        history_item.save()

                #update percent birds
                early_birds = EarlyBird.objects.filter(price_type=1,
                                                       hotel_supplier__period__parent__in=periods, 
                                                      )
                for early_bird in early_birds:
                    early_bird.recalc_eb_rates(periods, rooms)
                return render_to_response('hotels/default_res.html', 
                                          {'formula': formula,},
                                          context_instance=RequestContext(request))
    return HttpResponse('Formula Error')

def add_service_tax(request, hotel_supplier, formula):
    
    type = 'AND'

    #first parse formula
    parser = AddServiceTaxParser(formula=formula)
    data = parser.parse()

    #save
    service_form = ServiceAddForm(data=data)
    if service_form.is_valid():
        service = service_form.save(commit=False)
        service.is_tax = True
            
        #save services and find service in one date
        service.type = type
        service.day_type = type
        service.hotel_supplier = hotel_supplier
        service.save()
                    
        #update history log
        history_item = HotelSupplierHistory(hotel_supplier=hotel_supplier)
        history_item.user = request.user
        history_item.content_object = service
        history_item.object_repr = 'Tax %s' % service.title
        history_item.action = u'A'
        history_item.save()
            
        return render_to_response('hotels/default_res.html', 
                                  {'formula': formula,},
                                  context_instance=RequestContext(request))

    return HttpResponse('Formula Error')


def selected_hs_prices_publicate(request):

    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company

    if 'hs_list' in request.POST and request.POST['hs_list']:
        class OtherCompanyHsOwner(Exception):
            pass
        try:
            kwargs = {}
            kwargs['call_from___selected_hs_prices_publicate'] = 1
            for hs_id in request.POST['hs_list'].split(','):            
                r = publicate_hotel_prices(request, int(hs_id), **kwargs)
                if r == 'other_company_hs_owner':
                    raise OtherCompanyHsOwner
            return HttpResponse(simplejson.dumps({'result':'success'}),mimetype='application/json')            
        except OtherCompanyHsOwner:
            return HttpResponse(simplejson.dumps({'result':'other_company_hs_owner'}),mimetype='application/json')            
        except Exception,e:
            return HttpResponse(simplejson.dumps({'result':'error'}),mimetype='application/json')     
    else:
        return HttpResponse(simplejson.dumps({'result':'error'}),mimetype='application/json') 
    

                                   
def in_hotel_edit_check_errors(request, hotel_supplier_pk):
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404        
    company = user.company 
    
    try:
        hotel_supplier = HotelSupplier.objects.actual(
            ).select_related('hotel', 'supplier'
            ).get(pk=hotel_supplier_pk, company=company)
    except HotelSupplier.DoesNotExist:
        raise Http404

    hotel = hotel_supplier.hotel
    supplier = hotel_supplier.supplier
                   
    periods = get_periods(hotel_supplier)
    try:
        more_periods_qs = PeriodDates.objects.select_related('period').filter(
            period__hotel_supplier=hotel_supplier, 
            date_to__lt=datetime.date.today())[0]
        more_periods = True
    except IndexError:
        more_periods = False

    room_paxes_qs = RoomParams.objects.filter(room__hotel=hotel, 
        hotel_supplier=hotel_supplier, company=company)
    room_paxes = {}
    for room_pax in room_paxes_qs:
        room_paxes[room_pax.room.pk] = room_pax.max_pax

    # for tabs (birds)
    main_hotel_supplier = hotel_supplier if not hotel_supplier.parent else hotel_supplier.parent
    birds = EarlyBird.objects.filter(
        hotel_supplier__parent=main_hotel_supplier)

    #company room params (order)
    OrderFormSet = formset_factory(RoomOrderForm, formset=HotelSupplierItemsFormset, extra=0)
    rooms_qs = hotel.room_set.filter(
        Q(company__isnull=True) |
        Q(company=company)).order_by('id')
  
    rooms = []
    try:
        company_room_params = CompanyRoomParams.objects.get(company=company, hotel=hotel)
    except CompanyRoomParams.DoesNotExist:
        company_room_params = None
    if company_room_params:
        room_orders = company_room_params.get_room_order()
    else:
        room_orders = {}

    initial = []
    index = 0
    for room in rooms_qs:
        index += 1
        acc_list = Accommodation.objects.filter(room = room,hotel_supplier = hotel_supplier,company = company,)
        
        if len(acc_list) > 0:
            acc_err_msg = False
        else:
            acc_err_msg = 'Please add allotment'
                  
        rooms.append({'room': room, 
                      'order': room_orders.get(room.pk, 0), 
                      'index': index,
                      'acc_err_msg':acc_err_msg})
        initial.append({'room': room.pk, 'order': room_orders.get(room.pk, 0)})

    return render_to_response('hotels/in_hotel_edit_check_errors.html', 
                              {'hotel_supplier': hotel_supplier,
                               'rooms':rooms,
                               'room_paxes':room_paxes},
                              context_instance=RequestContext(request))


def check_commands(request):
    return render_to_response('hotels/check_commands.html', 
                              context_instance=RequestContext(request))
                              

def transfer_is_must(request, hotel_supplier_pk):

    if request.is_ajax() and 'checked' in request.POST:

        checked = int(request.POST['checked']) 

        hotel_supplier = HotelSupplier.objects.get(pk=hotel_supplier_pk)
        if checked == 1:
            hotel_supplier.transfer_is_must = True
            hotel_supplier.save()
            return HttpResponse(simplejson.dumps({'answer':1}),mimetype='application/json')
        elif checked == 0:
            hotel_supplier.transfer_is_must = False
            hotel_supplier.save()
            return HttpResponse(simplejson.dumps({'answer':1}),mimetype='application/json')                       
        else:
            return HttpResponse(simplejson.dumps({'answer':0}),mimetype='application/json')                                     
    else:
        return HttpResponse(simplejson.dumps({'answer':0}),mimetype='application/json')


###Temporary functions for hotel synchronization##

def sync_hotels(request):    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404
    company = user.company
    
    if request.method == 'POST':
        form = CountryChoseForSync(request.POST)
        if form.is_valid():
            chosen_country = form.cleaned_data['country']
            hotels_24travel = Hotel.objects.filter(country__iso=chosen_country.iso,
                                                   hotel__isnull=True,
                                                   ).exclude(
                                                    Q(deleted_hotel=True) |
                                                    Q(not_in_booking=True))[:20]
            hotels_booking = HotelBooking.objects.filter(cc1=chosen_country.iso)
            del_hotels = HotelSync.objects.filter(user=user).delete()
            for hotel in hotels_24travel:
                
                if hotel.longitude and hotel.latitude:                  
                    hotel_long = round(hotel.longitude, 6)
                    hotel_lat = round(hotel.latitude, 6)
                    lat_int = 0.00018 #20m latitude 
                    lat_rad = radians(hotel_lat)
                    long_int = (0.2*cos(lat_rad))/111.11111       
                    
                    matched_hotels = hotels_booking.filter(latitude__gt=(hotel_lat-lat_int),
                                                           latitude__lt=(hotel_lat+lat_int),
                                                           longitude__gt=(hotel_long-long_int),
                                                           longitude__lt=(hotel_long+long_int)                                                            
                                                           )
                    search_type = 'geo'
                else:                
                    matched_hotels = hotels_booking.filter(name__icontains=hotel.title)
                    search_type = 'name'                     
                if matched_hotels:                   
                    for matched_hotel in matched_hotels:                 
                        new_pair = HotelSync(hotel = hotel,
                                        hotel_booking = matched_hotel,
                                        user = user,
                                        sync_true = False,
                                        search_type = search_type 
                                        )
                        new_pair.save()
                else:
                    new_pair = HotelSync(hotel = hotel,
                                        hotel_booking = None,
                                        user = user,
                                        sync_true = False

                                        )
                    new_pair.save()
            return HttpResponseRedirect('hotel_list_for_sync/%s/' % (chosen_country.link))  
    else:
        form = CountryChoseForSync()           
    return render_to_response('hotels/sync_hotels.html', 
                              {                              
                               'form':form,
                               'sync_hotels':sync_hotels
                               },
                              context_instance=RequestContext(request))
                              
def sync_hotels_booking(request):    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404
    company = user.company
    
    from_stat_country = request.POST.get('from_stat_country') #если запрос пришел со статистики по странам
    public_status = request.POST.get('hotel_public') #публичный отель или нет
    print 0
    if from_stat_country:
        form = CountryChoseForSync(request.POST)
        return render_to_response('hotels/sync_hotels_booking.html', 
                              {                              
                               'form':form,
                               'sync_hotels':sync_hotels
                               },
                              context_instance=RequestContext(request))
    if request.method == 'POST':
        form = CountryChoseForSync(request.POST)
        if form.is_valid():   
            chosen_country = form.cleaned_data['country']
            hotels_24travel = Hotel.objects.filter(country__iso=chosen_country.iso,
                                                   hotel__isnull=True,
                                                   ).exclude(
                                                    Q(deleted_hotel=True) |
                                                    Q(not_in_booking=True))[:20]
            hotels_booking = HotelBooking.objects.filter(cc1=chosen_country.iso)
            del_hotels = HotelSync.objects.filter(user=user).delete()
            for hotel in hotels_24travel:
                
                if hotel.longitude and hotel.latitude:                  
                    hotel_long = round(hotel.longitude, 6)
                    hotel_lat = round(hotel.latitude, 6)
                    lat_int = 0.00018 #20m latitude 
                    lat_rad = radians(hotel_lat)
                    long_int = (0.2*cos(lat_rad))/111.11111       
                    
                    matched_hotels = hotels_booking.filter(latitude__gt=(hotel_lat-lat_int),
                                                           latitude__lt=(hotel_lat+lat_int),
                                                           longitude__gt=(hotel_long-long_int),
                                                           longitude__lt=(hotel_long+long_int)                                                            
                                                           )
                    search_type = 'geo'
                else:                
                    matched_hotels = hotels_booking.filter(name__icontains=hotel.title)
                    search_type = 'name'                     
                if matched_hotels:                   
                    for matched_hotel in matched_hotels:                 
                        new_pair = HotelSync(hotel = hotel,
                                        hotel_booking = matched_hotel,
                                        user = user,
                                        sync_true = False,
                                        search_type = search_type 
                                        )
                        new_pair.save()
                else:
                    new_pair = HotelSync(hotel = hotel,
                                        hotel_booking = None,
                                        user = user,
                                        sync_true = False

                                        )
                    new_pair.save()
            return HttpResponseRedirect('hotel_list_for_sync_booking/%s/%s' % (chosen_country.link, public_status))  
    else:
        form = CountryChoseForSync()           
    return render_to_response('hotels/sync_hotels_booking.html', 
                              {                              
                               'form':form,
                               'sync_hotels':sync_hotels
                               },
                              context_instance=RequestContext(request))                              


def hotel_list_for_sync(request, country_link):
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404
    company = user.company 
    

    hotels_24 = HotelSync.objects.filter(user=user)
    hotels_24_list = hotels_24.values_list('hotel', flat=True)
    hotels_set = set(hotels_24_list)
    initial_data = []
    for hotel in hotels_24:
        try:
            new_dict = {}
            new_dict ['hotel']= hotel.hotel
            new_dict ['hotel_booking'] = hotel.hotel_booking
            initial_data.append(new_dict)
        except:
            pass
    HotelChoseForSyncFormSet = formset_factory(HotelChoseForSync, extra = len(hotels_set), can_delete=False)
    if request.method == 'POST':    
        hotel_formset = HotelChoseForSyncFormSet(request.POST)
        for form in hotel_formset:
            if form.is_valid():
                hotel = form.cleaned_data['hotel']
                hotel_booking = form.cleaned_data['hotel_booking']
                hotel_booking_name = hotel_booking.split("(")[0]
                hotel_booking = hotel_booking.split("//") 
                hotel_booking_id = form.cleaned_data['hotel_booking_id']
                country = Country.objects.get(link = country_link)
                try:
                    approved = form.cleaned_data['approve']
                except:
                    approved = None                
                if approved:
                    try:
                        hotel_booking = HotelBooking.objects.get(pk = hotel_booking_id)
                    except:
                        try:
                            hotel_booking = HotelBooking.objects.get(pk=hotel_booking[1])
                        except:
                            hotel_booking = None
                    if hotel_booking:
                        hotel_obj = HotelSync.objects.filter(hotel__pk=hotel)
                        for hotel in hotel_obj:
                            hotel.delete()                                
                            hotel_booking.hotel = hotel.hotel
                            hotel_booking.save()
                else:
                    pass
        country = Country.objects.get(link = country_link)
        hotels_24travel = Hotel.objects.filter(country__iso=country.iso,
                                               hotel__isnull=True,
                                      ).exclude(
                                                Q(deleted_hotel=True) |
                                                Q(not_in_booking=True))[:20]
        hotels_booking = HotelBooking.objects.filter(cc1=country.iso)
        del_hotels = HotelSync.objects.filter(user=user).delete()
        for hotel in hotels_24travel:
            if hotel.longitude and hotel.latitude:                  
                hotel_long = round(hotel.longitude, 6)
                hotel_lat = round(hotel.latitude, 6)
                lat_int = 0.00018 #20m latitude 
                lat_rad = radians(hotel_lat)
                long_int = (0.02*cos(lat_rad))/111.11111 #20m longitude      
                matched_hotels = hotels_booking.filter(latitude__gt=(hotel_lat-lat_int),
                                                        latitude__lt=(hotel_lat+lat_int),
                                                        longitude__gt=(hotel_long-long_int),
                                                        longitude__lt=(hotel_long+long_int)                                                            
                                                       )
                search_type = 'geo'
            else:                
                matched_hotels = hotels_booking.filter(name__icontains=hotel.title)
                search_type = 'name'                     
            if matched_hotels:                   
                for matched_hotel in matched_hotels:                 
                    new_pair = HotelSync(hotel = hotel,
                                        hotel_booking = matched_hotel,
                                        user = user,
                                        sync_true = False,
                                        search_type = search_type 
                                        )
                    new_pair.save()
            else:
                new_pair = HotelSync(hotel = hotel,
                                     hotel_booking = None,
                                     user = user,
                                     sync_true = False,
                                    )
                new_pair.save()
        return HttpResponseRedirect('%s' % (chosen_country.link)) 

    hotel_formset = HotelChoseForSyncFormSet()       
    return render_to_response('hotels/hotel_list_for_sync.html', 
                              {                              
                               'hotel_formset':hotel_formset,
                               'hotels_24':hotels_24,
                               'country_link':country_link,
                               },                                            
                              context_instance=RequestContext(request)) 

def hotel_list_for_sync_booking(request, country_link, public_status):
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404
    company = user.company 
    
    if len(public_status)>13:
        public_status = public_status.split('/')
        public_status = public_status[-1]  
    hotels_from_status = HotelSync.objects.filter(user=user)
    if public_status: 
        if public_status == "hotel_public":   #публичный отель 
            hotels_24 = hotels_from_status.filter(hotel__company__id = None)
        else:                                 #непубличный отель
            hotels_24 = hotels_from_status.exclude(hotel__company__id = None)
    else:
        hotels_24 = HotelSync.objects.filter(user=user)
    hotels_24_list = hotels_24.values_list('hotel', flat=True)
    hotels_set = set(hotels_24_list)
    initial_data = []
    for hotel in hotels_24:
        try:
            new_dict = {}
            new_dict ['hotel']= hotel.hotel
            new_dict ['hotel_booking'] = hotel.hotel_booking
            initial_data.append(new_dict)
        except:
            pass
    HotelChoseForSyncFormSet = formset_factory(HotelChoseForSync, extra = len(hotels_set), can_delete=False)
    if request.method == 'POST': 
        data = request.POST.get('data')
        data = QueryDict(data)
        hotel_formset = HotelChoseForSyncFormSet(data)
        for form in hotel_formset:
            if form.is_valid():
                hotel = form.cleaned_data['hotel']
                hotel_booking = form.cleaned_data['hotel_booking']
                hotel_booking_name = hotel_booking.split("(")[0]
                hotel_booking = hotel_booking.split("//") 
                hotel_booking_id = form.cleaned_data['hotel_booking_id']
                country = Country.objects.get(link = country_link)
                try:
                    approved = form.cleaned_data['approve']
                except:
                    approved = None                
                if approved:
                    try:
                        hotel_booking = HotelBooking.objects.get(pk = hotel_booking_id)      
                    except:
                        try:
                            hotel_booking = HotelBooking.objects.get(pk=hotel_booking[1])
                        except:
                            hotel_booking = None
                    if hotel_booking:
                        hotel_obj = HotelSync.objects.filter(hotel__pk=hotel)
                        for hotel in hotel_obj:
                            hotel.delete()                                
                            hotel_booking.hotel = hotel.hotel
                            hotel_booking.save()
                else:
                    pass
        country = Country.objects.get(link = country_link)
        hotels_24travel = Hotel.objects.filter(country__iso=country.iso,
                                               hotel__isnull=True,
                                      ).exclude(
                                                Q(deleted_hotel=True) |
                                                Q(not_in_booking=True))[:20]
        hotels_booking = HotelBooking.objects.filter(cc1=country.iso)
        del_hotels = HotelSync.objects.filter(user=user).delete()
        for hotel in hotels_24travel:
            if hotel.longitude and hotel.latitude:                  
                hotel_long = round(hotel.longitude, 6)
                hotel_lat = round(hotel.latitude, 6)
                lat_int = 0.00018 #20m latitude 
                lat_rad = radians(hotel_lat)
                long_int = (0.02*cos(lat_rad))/111.11111 #20m longitude      
                matched_hotels = hotels_booking.filter(latitude__gt=(hotel_lat-lat_int),
                                                        latitude__lt=(hotel_lat+lat_int),
                                                        longitude__gt=(hotel_long-long_int),
                                                        longitude__lt=(hotel_long+long_int)                                                            
                                                       )
                search_type = 'geo'
            else:                
                matched_hotels = hotels_booking.filter(name__icontains=hotel.title)
                search_type = 'name'                     
            if matched_hotels:                   
                for matched_hotel in matched_hotels:                 
                    new_pair = HotelSync(hotel = hotel,
                                        hotel_booking = matched_hotel,
                                        user = user,
                                        sync_true = False,
                                        search_type = search_type 
                                        )
                    new_pair.save()
            else:
                new_pair = HotelSync(hotel = hotel,
                                     hotel_booking = None,
                                     user = user,
                                     sync_true = False,
                                    )
                new_pair.save()      
        country_link = str(request.POST.get('country'))
        return HttpResponseRedirect('%s/%s' % (country_link, public_status)) 

    hotel_formset = HotelChoseForSyncFormSet()   
    return render_to_response('hotels/hotel_list_for_sync_booking.html', 
                              {                              
                               'hotel_formset':hotel_formset,
                               'hotels_24':hotels_24,
                               'country_link':country_link,
                               'public_status':public_status
                               },                                            
                              context_instance=RequestContext(request)) 

def fill_hotel_select(request):
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404
    company = user.company
    
    perenos_good = 0;
    hotel_status = request.POST.get('hotel_public')  #публичный отель или нет
    hotels_perenos = request.POST.getlist('hotels_perenos')
    if hotels_perenos:
        for hotel_pk in hotels_perenos:
            hotel = hotel_pk
            status_work = get_hotel_in_work_ajax(request,hotel_pk)
            if status_work=='Not in work':
                hotel = Hotel.objects.get(id=hotel_pk)
                hotel.company_id = 3;
                hotel.save()    
                perenos_good = perenos_good+1;
    try: 
        try:
            hotels_from_status = HotelSync.objects.filter(user=user)
            country = hotels_from_status[0].hotel.country_id
        except:
            results = 0 
            return HttpResponse(simplejson.dumps(results),mimetype='application/json')
        if hotel_status:
            if hotel_status == "hotel_public":
                hotels = hotels_from_status.filter(hotel__company__id = None)
            else:     
                hotels = hotels_from_status.exclude(hotel__company__id = None)
        else:
            hotels = HotelSync.objects.filter(user=user)
        hotels_list = hotels.values_list('hotel', flat=True)
        hotels_set = set(hotels_list)
        tmp_list = []
        
        for hotel in hotels_set:
            tmp_dct = {}
            hotel_obj = hotels.filter(hotel = hotel) 
            tmp_dct['hotel'] = hotel_obj[0].hotel.title
            tmp_dct['hotel_city'] = hotel_obj[0].hotel.resort.title_en
            tmp_dct['hotel_pk'] = hotel_obj[0].hotel.pk
            company_name = 0
            if hotel_status:
                if hotel_obj[0].hotel.company_id:
                    company_name = Company.objects.get(id=hotel_obj[0].hotel.company_id)
                if company_name:
                    tmp_dct['hotel_public'] = str(hotel_obj[0].hotel.company_id)+" (" +str(company_name.firm_name) +")"
                else:
                    tmp_dct['hotel_public'] = hotel_obj[0].hotel.company_id
            tmp_dct['search_type'] = hotel_obj[0].search_type
            booking_hotels = []   
            for obj in hotel_obj:
                try:
                    booking_hotels.append('%s (%s)//%s' % (obj.hotel_booking.name, obj.hotel_booking.city_hotel,  obj.hotel_booking.pk))
                except:
                    booking_hotels.append(None) 
            tmp_dct['hotel_booking'] =  booking_hotels 
            tmp_list.append(tmp_dct)
    except:
        raise Http404
    if len(tmp_list) == 0:
        if hotels_perenos:
            results = {'perenos_good':perenos_good,'country':country}
        else:
            results = 0
    else:
        if hotels_perenos:
            results = {'response': tmp_list, 'perenos_good':perenos_good}
        else:
            results = {'response': tmp_list}
    return HttpResponse(simplejson.dumps(results),mimetype='application/json') 


def get_hotel_by_id(request):
    if request.method == 'POST':
        hotel_booking_id = request.POST.values()
        hotel_booking_id = ''.join(hotel_booking_id)
        try:
            hotel = HotelBooking.objects.get(pk = hotel_booking_id)
            return HttpResponse('%s (%s)' % (hotel.name, hotel.city_hotel )) 
        except HotelBooking.DoesNotExist:
            username = 'llcevrofan'
            password = '7756'
            host = u'https://distribution-xml.booking.com/json/'
            path = u'getHotels'
            path_rq = u'/%s' % path
            xml_rq = u'hotel_ids=%s' %(hotel_booking_id)
            user_pass = base64.encodestring('%s:%s' % (username, password)).replace('\n', '')
            headers = {'Authorization' : 'Basic %s' %  user_pass} 
            rs = 'https://distribution-xml.booking.com/json/bookings.%s?%s' % (path, xml_rq)
            request = urllib2.Request(rs, headers=headers)
            rs = urllib2.urlopen(request)
            booking_response = json.load(rs)
            if booking_response:
                response = booking_response[0] 
                hotel_id = int(response['hotel_id'])
                print hotel_id 
                print response['location']['longitude']
                hotel = HotelBooking(id = hotel_id,
                                     name = response['name'],
                                     address = response['address'],
                                     hotel_zip = response['zip'],
                                     city_hotel = response['city'],
                                     cc1 = response['countrycode'],
                                     ufi = response['city_id'],
                                     hotel_class = response['exact_class'],
                                     currencycode = response['currencycode'],
                                     minrate = response['minrate'],
                                     maxrate = response['maxrate'],
                                     preferred = response['preferred'],
                                     nr_rooms = response['nr_rooms'],
                                     longitude = response['location']['longitude'],
                                     latitude = response['location']['latitude'],
                                     hotel_url = response['url'],
                                     public_ranking = response['ranking']                    
                                     )
                hotel.save()                   
                return HttpResponse('%s saved to DB with %s ID' % (hotel.name, hotel.pk))                         
            else:
                return HttpResponse('not found')
        except ValueError:
            return HttpResponse('Введите целое число')
    
def get_hotel_in_work_ajax(request,*args):

    if args:
        hotel_pk = int(args[0])
    else:
        hotel_pk = u'%s' % (request.POST['hotel'])
        
    try:
        hotel = Hotel.objects.get(pk = hotel_pk)
    except:
        return HttpResponse('Hotel not found')
    try: 
        suppliers = hotel.hotelsupplier_set.all()
        try:
            accommodation = hotel.accommodation_set.all()
        except:
            accommodation = None
    except:
        suppliers = None
    if suppliers:
        suppliers_list=[]
        for supplier in suppliers:
            try:
                suppliers_list.append(supplier.company.pk);
            except:
                pass             
        if accommodation:
            order_status = u'In order //'
        else :
            order_status = u'' 
        return HttpResponse('%s Suppliers: %s' % (order_status, (', '.join(str(v) for v in set(suppliers_list)))))            
    elif accommodation:      
        return HttpResponse('In order')
    else:
        if args:
            return 'Not in work'
        return HttpResponse('Not in work')
        


def sync_hotels_list(request):
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404
    company = user.company 
    if request.method == 'POST':     
        form = CountryChoseForSync(request.POST) 
        if form.is_valid():
            country = form.cleaned_data['country']
            hotels_24travel = Hotel.objects.filter(country = country)
            hotels_booking = HotelBooking.objects.filter(cc1 = country.iso)
            city_booking = CityBooking.objects.filter(country_code = country.iso)
            hotel_list = []
            count = 0
            for hotel in hotels_24travel:
                temp_dct = {}
                temp_dct['hotel'] = hotel
                try:
                    hotel_booking = hotels_booking.get(hotel = hotel)            
                    temp_dct['hotel_booking'] = hotel_booking
                    count += 1
                    try:
                        temp_dct['city_booking'] = city_booking.get(ufi = hotel_booking.ufi)
                    except:
                        pass           
                except:
                    hotel_booking = None
                hotel_list.append(temp_dct) 
            return render_to_response('hotels/hotel_list_for_sync.html', 
                                      {                              
                                       'hotel_list':hotel_list,
                                       'count':count
                                       },                                            
                                      context_instance=RequestContext(request))
    form = CountryChoseForSync() 
    return render_to_response('hotels/hotel_list_for_sync.html', 
                                      {                              
                                       'form': form 
                                       },
                                       context_instance=RequestContext(request)) 

#заполнение полей deleted и not_in_booking в модели Hotel
def sync_hotel_ajax_operations(request):
    action = u'%s' % (request.POST['action'])
    hotel_pk = u'%s' % (request.POST['hotel'])  
    try:
        hotel = Hotel.objects.get(pk = hotel_pk)
    except:
        hotel = None
    if hotel and action == 'del':
        supplier = HotelSupplier.objects.filter(hotel = hotel)
        accommodation = OrderAccommodation.objects.filter(hotel = hotel)        
        if supplier or accommodation: 
            return HttpResponse("")
        else:          
            hotel.deleted_hotel = True
        hotel.save()    
    elif hotel and action == 'nib':
        hotel.not_in_booking = True
        hotel.save()    
    return HttpResponse('success')
    
    
def hotel_select_reload(request):
    selected_txt = u'%s' % (request.POST['selected_txt'])
    country = u'%s' % (request.POST['country'])
    country_obj = Country.objects.get(link = country)
    hotels_booking = HotelBooking.objects.filter(cc1 = country_obj.iso,
                                                 name__icontains = selected_txt 
                                                )
    booking_hotels = []
    for hotel in hotels_booking:       
        try:
            booking_hotels.append('%s (%s)//%s' % (hotel.name, hotel.city_hotel,  hotel.pk))
        except:
            booking_hotels.append(None) 
    result = {}
    result['hotels'] = booking_hotels
      
    return HttpResponse(simplejson.dumps(result),mimetype='application/json')
    

@login_required    
def hotel_choose(request):
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404
    company = user.company
    
    qs = Hotel.objects.order_by('title')
    hotel_count = qs.count()
    print 'COUNT: %s' % hotel_count 
    return render_to_response('hotels/hotel_choose.html', 
                              {
                               'hotel_count': hotel_count,
                              },
                              context_instance=RequestContext(request))
    
    

def hotel_load(request):
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404
    company = user.company
    
    form = HotelLoadForm(data=request.GET)
    if form.is_valid():
        count = form.cleaned_data['count'] or 100
        start_index = form.cleaned_data['start_index'] or 0
        query_str = form.cleaned_data['q']
        end_index = start_index + count
        qs = Hotel.objects.order_by('title')
        if query_str:
            qs = qs.filter(title__icontains=query_str).distinct().order_by('title')
            
        qs = qs[start_index:end_index]
        hotels = []
        for hotel in qs: 
            try:
                hotel_item = {'id': hotel.pk, 
                              'title': hotel.title,
                              'country_pk': hotel.country.pk,
                              'country': hotel.country.link,
                              'resort': hotel.resort.pk,
                            }
                hotels.append(hotel_item)
            except:
                pass 
        return HttpResponse(json.dumps(hotels), mimetype='application/json')
    return HttpResponse(json.dumps([]), mimetype='application/json')  
    
def hotel_sync(request):
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404
    company = user.company
    
    HotelSyncFormSet = formset_factory(HotelSyncForm, extra = 1, can_delete=False)
    hotels = Hotel.objects.all()
    old_hotel = None
    new_hotel = None
    if request.method == 'POST':
        hotel_formset = HotelSyncFormSet(request.POST)
        if hotel_formset.is_valid():    
            for form in hotel_formset:            
                old_hotel = form.cleaned_data['old_hotel'] 
                new_hotel = form.cleaned_data['new_hotel']
                try:
                    old_hotel_obj = hotels.get(pk=old_hotel)
                    new_hotel_obj = hotels.get(pk=new_hotel)
                except Resort.DoesNotExist:
                    old_hotel_obj = None
                    new_hotel_obj = None
                    
                if new_hotel_obj and old_hotel_obj:
                    new_hotel = {}
                    old_hotel = {}
                    
                    #new_hotel['name'] = new_hotel.title
                    #old_hotel['name'] = old_hotel.title
                    #i=0
                    #models_new_hotel = hotels_sync_links(new_hotel.id)
                    #models_old_hotel = hotels_sync_links(old_hotel.id)
                    #
                     
                                                                                
    else:
        hotel_formset = HotelSyncFormSet() 
    return render_to_response('hotels/hotels_merge.html',
                              {
                                'hotel_formset':hotel_formset,
                                'new_hotel': new_hotel,
                                'old_hotel': old_hotel
                               },
                               context_instance=RequestContext(request))
                               
def check_hotel_ajax(request):
    try:
        hotel_id = request.POST['id']
        hotel = Hotel.objects.get(id=hotel_id)
        return HttpResponse('%s (%s)' % (hotel.title, hotel.country.title))
    except:
        return HttpResponse('not found')    
        
def hotel_sync_links(request): 
    hotel_id = request.POST.get('hotel_id')
    models_list_first = Hotel._meta.get_all_related_objects()
    model_list = {}
    i=0
    for r in models_list_first:
        model = r.model
        model_q = model.objects.filter(hotel__id = hotel_id)
        if model_q:
            model_list[model] = model_q 
            i=i+1    
    
    company_list = {}
    for key,model in model_list.items():
        if model:
            
            for model_sample in model:  
                models = []
                model_full = {}
                model_full['name'] = key.__name__ 
                model_full['id'] = []
                if model_full['name'] == 'Hotel':
                    continue 
                if model_full['name']=='Accommodation':
                    accommodations = Accommodation.objects.filter(id = model_sample.id )
                    for accommodation in accommodations:
                        company = Company.objects.get(id =accommodation.company_id )
                        company_name = " компания:"+ str(accommodation.company_id)+" ("+ str((company.firm_name).encode('utf8'))+ ") "
                        
                        if company_list=={}:
                            model_full['id'].append(str(model_sample.id))
                            models.append(model_full)
                            company_list[company_name] = models
                        else:
                            if company_list.has_key(company_name):
                                name_list = []
                                for model_in_company in company_list[company_name]: 
                                    name_list.append(model_in_company['name'])
                                if model_full['name'] in name_list:
                                    for model_in_company in company_list[company_name]:
                                        if model_in_company['name'] == model_full['name']:
                                            model_in_company['id'].append(str(model_sample.id))
                                else:
                                    model_full['id'].append(str(model_sample.id))
                                    company_list[company_name].append(model_full)
                            else:
                                model_full['id'].append(str(model_sample.id))
                                models.append(model_full)
                                company_list[company_name]=(models)
                else:
                    company = Company.objects.get(id = int(model_sample.company_id) )
                    company_name = " компания:"+ str(model_sample.company_id)+" ("+ str((company.firm_name).encode('utf8'))+ ") "
                    if company_list=={}:
                        model_full['id'].append(str(model_sample.id))
                        models.append(model_full)
                        company_list[company_name] = models
                    else:
                        if company_list.has_key(company_name):
                            name_list = []
                            for model_in_company in company_list[company_name]: 
                                name_list.append(model_in_company['name'])
                            if model_full['name'] in name_list:
                                for model_in_company in company_list[company_name]:
                                    if model_in_company['name'] == model_full['name']:
                                        model_in_company['id'].append(str(model_sample.id))
                            else:
                                model_full['id'].append(str(model_sample.id))
                                company_list[company_name].append(model_full) 
                        else:
                            model_full['id'].append(str(model_sample.id))
                            models.append(model_full)
                            company_list[company_name]=(models)

    #for k,v in company_list.items():
       # print k,v
    hotel = Hotel.objects.values().get(id = hotel_id) 
    print hotel
    model = {}
    if hotel['country_id']:
        country = Country.objects.get(id = hotel['country_id'])
        model['country_id'] = country.title
    else:
        model['country_id'] = "None"
    if hotel['resort_id']:
        resort = Resort.objects.get(id = hotel['resort_id'])
        model['resort_id'] = resort.title
    else:
        model['resort_id'] = "None"
    if hotel['company_official_supplier_id']:
        company = Company.objects.get(id = hotel['company_official_supplier_id'])
        model['company_official_supplier_id'] = company.firm_name
    else:
        model['company_official_supplier_id'] = "None"
    if hotel['title']:
        model['title'] = hotel['title']
    else:
        model['title'] = "None"
    if hotel['latitude']:
        model['latitude'] = hotel['latitude']
    else:
        model['latitude'] = "None"
    if hotel['longitude']:
        model['longitude'] = hotel['longitude']
    else:
        model['longitude'] = "None"
    if hotel['phone']:
        model['phone'] = hotel['phone']
    else:
        model['phone'] = "None"
    if hotel['stars_id']:
        hotel_stars = HotelStars.objects.get(id = hotel['stars_id'])
        model['stars_id'] = hotel_stars.title
    else:
        model['stars_id'] = "None"
    print model
    rendered = render_to_string('hotels/hotel_sync_links.html', {'model':model}) 
    company_list = render_to_string('hotels/hotels_sync_links_companys.html', {'company_list':company_list})
    results = {'company_list': company_list, 'rendered':rendered}
    results  = simplejson.dumps( results )
    return HttpResponse(results,
                    mimetype='application/javascript')
                    
def hotels_sync_links(hotel_id):
    models_list_first = Hotel._meta.get_all_related_objects()
    print models_list_first
    model_list = {}
    i=0
    for r in models_list_first:
        model = r.model
        model_q = model.objects.filter(hotel__id = hotel_id)
        if model_q:
            model_list[model] = model_q 
            i=i+1    
        print 1
    models = []
    for key,model in model_list.items():
        print 2
        model_full = {}
        model_full['name'] = key.__name__
        model_id = model
        j=0
        print 3
        if model:
            print 4
            model_full['id'] = []
            for model_sample in model:  
                model_full['id'].append(str(model_sample.id)+" ")   
                print model_full['id'][j]         # СДЕЛАТЬ ЭТОТ БЛОК!!!!!
                model_id = model_sample.id
                j=j+1
                #print model_id
        if model_full['id']:
            models.append(model_full)
    print models    
    return models
                    


def cron_operations(request):
    
    user = request.user
    if not hasattr(user, 'company'):
        raise Http404
    company = user.company
    
    if request.method == 'POST' and request.POST['action']=='sync_res_names':
        form = CountryChoseForSync(request.POST)
        if form.is_valid():
            country = form.cleaned_data['country'] 
            country_code = country.iso.lower()       
        return HttpResponse(add_multilang_resort_title(country_code))
    if request.method == 'POST' and request.POST['action']=='sync_districts':
        form = CountryChoseForSync(request.POST)
        if form.is_valid():
            country = form.cleaned_data['country'] 
            country_code = country.iso.lower()       
        return HttpResponse(add_districts_to_resorts(country_code))
    if request.method == 'POST' and request.POST['action']=='sync_stars':     
        return HttpResponse(update_hotel_stars_info())   
    if request.method == 'POST' and request.POST['action']=='fill_booking_stars':      
        return HttpResponse(fill_hotel_stars_info())
    if request.method == 'POST' and request.POST['action']=='get_regions':      
        form = CountryChoseForSync(request.POST)
        if form.is_valid():
            country = form.cleaned_data['country'] 
            country_code = country.iso.lower()
        return HttpResponse(fill_resort_parent(country_code))
    if request.method == 'POST' and request.POST['action']=='load_hotels_from_booking':  
        form = CountryChoseForSync(request.POST)
        if form.is_valid():
            country = form.cleaned_data['country'] 
            country_code = country.iso.lower()
        return HttpResponse(sync_booking_hotels(country_code))
    return render_to_response('hotels/cron_operations.html', 
                              {                              
                               },
                              context_instance=RequestContext(request))
    