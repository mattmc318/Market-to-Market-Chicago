from datetime import datetime
from dateutil.relativedelta import relativedelta
from django.shortcuts import render, redirect
from django.urls import reverse
from django.http import (
    HttpResponseBadRequest,
    HttpResponseNotFound,
    HttpResponseRedirect,
    JsonResponse,
)
from django.contrib.auth.models import User
from mtm.settings import TZ, NAME, API_KEY
from .models import Event

def index(request):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    current_month = datetime.now(TZ).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    return render(request, 'events/index.html', {
        'user': User.objects.get(pk=request.session['id']) \
            if 'id' in request.session else None,
        'calendar': Event.objects.calendar(request),
        'by_date': Event.objects.by_date(request),
        'by_location': Event.objects.by_location(request),
        'prev': current_month + relativedelta(months=-1),
        'next': current_month + relativedelta(months=+1),
        'name': NAME,
        'year': current_month.year,
    })

def event(request, category, location_name, event_name, event_id):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    valid, response = Event.objects.event(category, location_name, event_name, event_id)

    if not valid:
        def invalid_id():
            return HttpResponseNotFound("Invalid event ID")

        def invalid_slug():
            return HttpResponseRedirect(
                reverse('events:event', args=response['args']))

        actions = {
            'invalid ID': invalid_id,
            'invalid slug': invalid_slug,
        }

        return actions[response['status']]()

    return render(request, 'events/event.html', {
        **response,
        'user': User.objects.get(pk=request.session['id']) \
            if 'id' in request.session else None,
        'name': NAME,
        'year': datetime.now(TZ).year,
        'API_KEY': API_KEY,
    })

def month(request):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    return render(request, 'events/month.html', {
        'calendar': Event.objects.calendar(request)
    })

def by_date(request):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    return render(request, 'events/by_date.html', {
        'by_date': Event.objects.by_date(request)
    })

def by_location(request):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    return render(request, 'events/by_location.html', {
        'by_location': Event.objects.by_location(request)
    })

def prev(request):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    return JsonResponse(Event.objects.prev(request))

def next(request):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    return JsonResponse(Event.objects.next(request))
