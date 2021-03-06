import pytz

from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.db import models
from django.db.models import Q

from mtm.settings import TZ

DOW = [
    {
        'col': 0,
        'dow': 'Sun',
    },
    {
        'col': 1,
        'dow': 'Mon',
    },
    {
        'col': 2,
        'dow': 'Tue',
    },
    {
        'col': 3,
        'dow': 'Wed',
    },
    {
        'col': 4,
        'dow': 'Thu',
    },
    {
        'col': 5,
        'dow': 'Fri',
    },
    {
        'col': 6,
        'dow': 'Sat',
    },
]

class EventManager(models.Manager):
    def event(self, category_slug, location_slug, event_slug, event_id):
        from .models import Event, RecurringEvent
        from locations.models import CATEGORIES, Location
        from images.models import Image, Album

        try:
            event = RecurringEvent.objects.get(id=event_id)
            recurring = True
        except RecurringEvent.DoesNotExist:
            try:
                event = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                return (False, {'status': 'invalid ID'})

            recurring = False

        _category_slug = CATEGORIES[event.location.category] if event.location else 'events'
        _location_slug = event.location.slug if event.location else 'undefined'
        _event_slug = event.slug

        if _category_slug != category_slug or \
            _location_slug != location_slug or \
            _event_slug != event_slug:
            return (False, {
                'status': 'invalid slug',
                'args': [_category_slug, _location_slug, _event_slug, event_id],
            })

        if recurring:
            next_event = RecurringEvent.objects.filter(
                info=event.info,
                date_start__gt=event.date_start,
            ).order_by('date_start').first()
        else:
            next_event = None

        images = Image.objects.filter(album=event.album) if event.album else None

        return (True, {
            'event': event,
            'next_event': next_event,
            'category_name': Location.CATEGORY_CHOICES[event.location.category][1] if event.location else 'Miscellaneous',
            'category_slug': _category_slug,
            'recurring': recurring,
            'images_preview': images[:14] if images and len(images) > 15 else images,
        })

    def create_event(self, request):
        from .models import Event, RecurringEvent
        from locations.models import Neighborhood, Location
        from images.models import Album

        # Data collection
        name = request.POST.get('name', '')
        description = request.POST.get('description', '')
        all_day_value = request.POST.get('all-day', '')
        date_start_str = request.POST.get('date-start', '')
        date_end_str = request.POST.get('date-end', '')
        frequency = request.POST.get('frequency', '-1')
        frequency_units = request.POST.get('frequency-units', '0')
        weekday_list = request.POST.getlist('weekday-list')
        ends = request.POST.get('ends', '-1')
        ends_on_str = request.POST.get('ends-on', '')
        ends_after = request.POST.get('ends-after', '0')
        location_id = request.POST.get('location-id', '0')
        location_name = request.POST.get('location-name', '')
        album_id = request.POST.get('album-id', '0')
        album_name = request.POST.get('location-name', '')

        # Data restructuring
        all_day = all_day_value == 'true'

        if frequency:
            frequency = int(frequency)

        if frequency_units:
            frequency_units = int(frequency_units)

        if ends:
            ends = int(ends)

        if ends_after:
            ends_after = int(ends_after)

        if location_id:
            location_id = int(location_id)

        if album_id:
            album_id = int(album_id)

        # Basic validations
        errors = []

        if not name:
            errors.append('Please enter a name.')

        if not date_start_str:
            errors.append('Please enter a start date.')

        if not frequency:
            errors.append('Please enter a value for frequency.')

        if frequency_units == '':
            errors.append('Please enter a unit for frequency.')
        elif frequency_units != 0:
            if frequency == -1 or frequency == '':
                errors.append('Please enter a number of repetitions.')

            if ends == 1 and not ends_on_str:
                errors.append('Please enter a date to end on.')

            if ends == 2 and ends_after == 0:
                errors.append('Please enter a number of occurrences.')

        if ends == '':
            errors.append('Please enter an end condition.')

        if location_id <= 0 and location_name:
            errors.append('The specified location could not be found.')

        if album_id <= 0 and album_name:
            errors.append('The specified album could not be found.')

        # Datetime parsing
        def add_leading_zero_hour(date_str):
            if len(date_str) == 18:
                return date_str[:11] + '0' + date_str[-7:]
            else:
                return date_str

        add_leading_zero_hour(date_start_str)
        date_start = TZ.localize(datetime.strptime(date_start_str, '%m/%d/%Y %I:%M %p'))

        now = datetime.now(TZ)
        if date_start < now:
            errors.append('Start date cannot be in the past.')

        if date_end_str:
            add_leading_zero_hour(date_end_str)
            date_end = TZ.localize(datetime.strptime(date_end_str, '%m/%d/%Y %I:%M %p'))

            if date_end < now:
                errors.append('End date cannot be in the past.')

            if date_start >= date_end:
                errors.append('Start date must come before end date.')

        if all_day:
            date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)

        if ends == 1:
            add_leading_zero_hour(ends_on_str)
            ends_on = TZ.localize(datetime.strptime(ends_on_str, '%m/%d/%Y %I:%M %p'))

        # Grab location object or set to None
        if location_id <= 0 and location_name == '':
            location = None
        elif location_id > 0:
            try:
                location = Location.objects.get(id=location_id)
            except Location.DoesNotExist:
                errors.append('The specified location could not be found.')

        # Grab album object or set to None
        if album_id <= 0 or album_name == '':
            album = None
        elif album_id > 0:
            try:
                album = Album.objects.get(id=album_id)
            except Album.DoesNotExist:
                errors.append('The specified album could not be found.')

        if errors:
            return (False, errors)

        # Gather arguments and create event
        kwargs = {}
        if all_day:
            kwargs['all_day'] = all_day

        if date_end_str:
            kwargs['date_end'] = date_end

        if location:
            kwargs['location'] = location

        if album:
            kwargs['album'] = album

        if frequency_units == 0:
            event = Event.objects.create_single_event(
                name=name,
                date_start=date_start,
                **kwargs
            )
        else:
            if weekday_list:
                kwargs['weekday_list'] = weekday_list

            if date_end_str:
                kwargs['date_end'] = date_end

            if ends == 1:
                kwargs['ends_on'] = ends_on.replace(hour=23, minute=59, second=59, microsecond=999999)
            elif ends == 2:
                kwargs['ends_after'] = ends_after

            events = RecurringEvent.objects.create_recurring_event(
                name=name,
                date_start=date_start,
                frequency=frequency,
                frequency_units=frequency_units,
                ends=ends,
                **kwargs
            )

            events_len = len(events)
            return (True, 'You have successfully created %d event%s.' %
                (events_len, '' if events_len == 1 else 's'))

        return (True, 'You have successfully created 1 event.')

    def create_single_event(self, name, date_start, all_day=False, **kwargs):
        event = self.create(name=name, date_start=date_start.astimezone(pytz.utc), all_day=all_day)

        if not all_day and 'date_end' in kwargs:
            event.date_end = kwargs['date_end'].astimezone(pytz.utc)

        if 'location' in kwargs:
            event.location = kwargs['location']

        if 'album' in kwargs:
            event.album = kwargs['album']

        event.save()

        return event

    def update_event(self, request):
        from .models import Event, RecurringEvent
        from locations.models import Location, CATEGORIES
        from images.models import Album

        # Data collection
        event_id = request.POST.get('id', '0')
        name = request.POST.get('name', '')
        description = request.POST.get('description', '')
        all_day_value = request.POST.get('all-day', '')
        date_start_str = request.POST.get('date-start', '')
        date_end_str = request.POST.get('date-end', '')
        location_id = request.POST.get('location-id', '0')
        location_name = request.POST.get('location-name', '0')
        album_id = request.POST.get('album-id', '0')
        album_name = request.POST.get('album-name', '0')
        update = request.POST.get('update', '')

        # Data restructuring and validations
        errors = []
        event_id = int(event_id)
        if not event_id:
            errors.append('Invalid event ID.')

        all_day = all_day_value == 'true'

        if location_id:
            location_id = int(location_id)

        if album_id:
            album_id = int(album_id)

        # Datetime parsing
        def add_leading_zero_hour(date_str):
            if len(date_str) == 18:
                return date_str[:11] + '0' + date_str[-7:]
            else:
                return date_str

        add_leading_zero_hour(date_start_str)
        date_start = TZ.localize(datetime.strptime(date_start_str, '%m/%d/%Y %I:%M %p'))

        now = datetime.now(TZ)
        if date_start < now:
            errors.append('Start date cannot be in the past.')

        if date_end_str:
            add_leading_zero_hour(date_end_str)
            date_end = TZ.localize(datetime.strptime(date_end_str, '%m/%d/%Y %I:%M %p'))

            if date_end < now:
                errors.append('End date cannot be in the past.')

            if date_start >= date_end:
                errors.append('Start date must come before end date.')

        if all_day:
            date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)

        if errors:
            try:
                event = RecurringEvent.objects.get(id=event_id)
            except RecurringEvent.DoesNotExist:
                try:
                    event = Event.objects.get(id=event_id)
                except Event.DoesNotExist:
                    return (False, {
                        'errors': errors,
                        'event_found': False,
                    })
            return (False, {
                'errors': errors,
                'event_found': True,
                'args': [
                    CATEGORIES[event.location.category] if event.location else 'events',
                    event.location.slug if event.location else 'undefined',
                    event.slug,
                    event.id,
                ],
            })

        # Find event(s) and update
        if update == 'multiple-events':
            # Find recurring events and update
            event = RecurringEvent.objects.get(id=event_id)
            return RecurringEvent.objects.update_recurring_event(request, event.info)
        else:
            try:
                # Find single event
                event = Event.objects.get(id=event_id)

                # Update event
                if name:
                    event.name = name

                if description:
                    event.description = description
                event.all_day = all_day

                event.date_start = date_start

                if date_end_str:
                    event.date_end = date_end

                # Grab location object or set to None
                if location_id <= 0 or location_name == '':
                    location = None
                elif location_id > 0:
                    try:
                        location = Location.objects.get(id=location_id)
                    except Location.DoesNotExist:
                        return (False, {
                            'errors': ['The specified location could not be found.'],
                            'event_found': True,
                            'args': [
                                CATEGORIES[event.location.category] if event.location else 'events',
                                event.location.slug if event.location else 'undefined',
                                event.slug,
                                event.id,
                            ],
                        })

                event.location = location

                # Grab album object or set to None
                if album_id <= 0 or album_name == '':
                    album = None
                elif album_id > 0:
                    try:
                        album = Album.objects.get(id=album_id)
                    except Album.DoesNotExist:
                        return (False, {
                            'errors': ['The specified album could not be found.'],
                            'event_found': True,
                            'args': [
                                CATEGORIES[event.location.category] if event.location else 'events',
                                event.location.slug if event.location else 'undefined',
                                event.slug,
                                event.id,
                            ],
                        })

                event.album = album

                event.save()
            except Event.DoesNotExist:
                return (False, {
                    'errors': ['The specified event could not be found.'],
                    'event_found': False,
                })

        return (True, {
            'success': 'You have successfully updated 1 event.',
            'args': [
                CATEGORIES[event.location.category] if event.location else 'events',
                event.location.slug if event.location else 'undefined',
                event.slug,
                event.id,
            ],
        })

    def delete_event(self, request):
        from .models import Event, RecurringEvent
        from locations.models import Location, CATEGORIES

        event_id = int(request.POST.get('id', '0'))
        delete = request.POST.get('delete', '')

        errors = []
        if delete != 'single-event' and delete != 'multiple-events':
            errors.append('Please choose which instances will be deleted.')

        event_found = True
        try:
            event = RecurringEvent.objects.get(id=event_id)
        except RecurringEvent.DoesNotExist:
            try:
                event = Event.objects.get(id=event_id)
            except Event.DoesNotExist:
                errors.append('The specified event could not be found.')
                event_found = False

        if errors:
            return (False, {
                'errors': errors,
                'event_found': event_found,
                'args': [
                    CATEGORIES[event.location.category] if event.location else 'events',
                    event.location.slug if event.location else 'undefined',
                    event.slug,
                    event.id,
                ],
            })

        if delete == 'multiple-events':
            events = RecurringEvent.objects.filter(
                info=event.info,
                date_start__gte=event.date_start,
            )

            events_len = len(events)
            events.delete()
            return (True, {
                'success': 'You have successfully deleted %d event%s.' % (events_len, '' if events_len == 1 else 's'),
            })

        event.delete()

        return (True, {'success': 'You have successfully deleted 1 event.'})

    def calendar(self, request):
        from .models import Event

        today = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))

        date = first_of_month = datetime(year, month, 1, tzinfo=TZ)
        calendar = []
        while date.weekday() != 6:
            date = date - timedelta(days=1)

        for i in range(42):
            events = Event.objects.filter(
                date_start__date=date,
                date_start__gte=today,
            ).order_by('date_start')[:3]

            events_tz_adjusted = []
            for event in events:
                event.date_start = event.date_start.astimezone(TZ)

                if event.date_end:
                    event.date_end = event.date_end.astimezone(TZ)

                events_tz_adjusted.append(event)

            calendar.append({
                'date': date,
                'events': events_tz_adjusted,
                'row': int(i / 7),
                'col': i % 7,
            })

            date = date + timedelta(days=1)

        return {
            'date': first_of_month,
            'calendar': calendar,
            'days_of_week': DOW,
            'has_events': Event.objects.filter(
                Q(date_start__gte=first_of_month)
                & Q(date_start__lt=(first_of_month + relativedelta(months=1)))
            ).exists()
        }

    def by_date(self, request):
        from .models import Event
        from locations.models import CATEGORIES

        today = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))

        date = first_of_month = datetime(year, month, 1, tzinfo=TZ)
        calendar = []

        tabindex = 0
        while date.month == first_of_month.month:
            events = []
            for event in Event.objects.filter(
                date_start__date=date,
                date_start__gte=today,
            ).order_by('date_start'):
                if not event.all_day or event.location:
                    if event.location == None:
                        events.append({
                            'event': event,
                            'tabindex': tabindex,
                        })
                    else:
                        events.append({
                            'event': event,
                            'category': CATEGORIES[event.location.category] if event.location else 'events',
                            'tabindex': tabindex,
                        })
                    tabindex += 1
                else:
                    events.append({
                        'event': event,
                    })

            if events:
                calendar.append({
                    'date': date,
                    'events': events,
                })

            date = date + timedelta(days=1)

        return {
            'date': first_of_month,
            'calendar': calendar,
        }

    def by_location(self, request):
        from .models import Event
        from locations.models import Location, CATEGORIES

        today = datetime.now(TZ).replace(hour=0, minute=0, second=0, microsecond=0)
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))

        date = first_of_month = datetime(year, month, 1, tzinfo=TZ)
        locations = []

        try:
            tabindex = self.by_date(request)['calendar'][-1]['events'][-1]['tabindex'] + 1
        except IndexError:
            tabindex = 0
        except KeyError:
            tabindex = 0

        for location in Location.objects.all().order_by('name'):
            if Event.objects.filter(
                location=location,
                date_start__gte=first_of_month,
                date_start__lt=first_of_month + relativedelta(months=+1),
            ):
                day = first_of_month
                event_tree = []
                while day < first_of_month + relativedelta(months=+1):
                    events_on_day = Event.objects.filter(
                        location=location,
                        date_start__gte=day,
                        date_start__lt=day + timedelta(days=1),
                    ).filter(
                        date_start__gte=today,
                    ).order_by('date_start')

                    events = []
                    for event in events_on_day:
                        events.append({
                            'event': event,
                            'category': CATEGORIES[event.location.category] if event.location else 'events',
                            'tabindex': tabindex,
                        })
                        tabindex += 1

                    if len(events_on_day) > 0:
                        event_tree.append({
                            'date': day,
                            'events': events,
                        })

                    day = day + timedelta(days=1)

                locations.append({
                    'location': location,
                    'category': CATEGORIES[location.category],
                    'event_tree': event_tree,
                })

        return {
            'date': first_of_month,
            'locations': locations,
        }

    def prev(self, request):
        this_month = datetime.now(TZ).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)

        month = datetime(
            int(request.GET.get('year', this_month.year)),
            int(request.GET.get('month', this_month.month)),
            1, 0, 0, 0, 0,
        )
        month = TZ.localize(month)

        prev_month = month + relativedelta(months=-1)

        if month == this_month:
            return {
                'disabled': True,
            }
        else:
            return {
                'disabled': False,
                'date': {
                    'year': prev_month.year,
                    'month': prev_month.month,
                }
            }

    def next(self, request):
        this_month = datetime.now(TZ).replace(
            day=1, hour=0, minute=0, second=0, microsecond=0)

        try:
            month = datetime(
                int(request.GET.get('year', this_month.year)),
                int(request.GET.get('month', this_month.month)),
                1, 0, 0, 0, 0,
            )
            month = TZ.localize(month)
        except TypeError:
            return (False, None)

        next_month = month + relativedelta(months=+1)

        return {
            'date': {
                'year': next_month.year,
                'month': next_month.month,
            }
        }

class RecurringEventManager(models.Manager):
    def create_recurring_event(self, name, date_start, frequency, frequency_units, ends, **kwargs):
        from .models import RecurringEvent, RepeatInfo

        date = date_start
        max_duration = relativedelta(years=+1)
        date_max = date + max_duration

        rd_values = [
            relativedelta(days=+frequency),
            relativedelta(days=+(7 * frequency)),
            relativedelta(months=+frequency),
            relativedelta(years=+frequency),
        ]

        days_of_week = [
            'monday',
            'tuesday',
            'wednesday',
            'thursday',
            'friday',
            'saturday',
            'sunday',
        ]

        info = RepeatInfo.objects.create_repeat_info(frequency, frequency_units, ends, **kwargs)

        if ('weekday_list' in kwargs and kwargs['weekday_list']) or (frequency == 1 and frequency_units == 2):
            info.weekly = True
        else:
            info.weekly = False

        info.save()

        frequency_units -= 1

        if ends == 0: # ends after max. duration
            if 'date_end' in kwargs:
                date_end = kwargs['date_end']

                if 'weekday_list' in kwargs and kwargs['weekday_list']:
                    while date <= date_max:
                        if days_of_week[date.weekday()] in kwargs['weekday_list']:
                            event = self.create(name=name, date_start=date.astimezone(pytz.utc), info=info)

                            event.date_end = date_end.astimezone(pytz.utc)

                            if 'location' in kwargs:
                                event.location = kwargs['location']

                            event.save()

                        date = TZ.localize(
                            date.replace(tzinfo=None) + timedelta(days=1)
                        )
                        date_end = TZ.localize(
                            date_end.replace(tzinfo=None) + timedelta(days=1)
                        )
                else:
                    while date <= date_max:
                        event = self.create(name=name, date_start=date.astimezone(pytz.utc), info=info)

                        event.date_end = date_end.astimezone(pytz.utc)

                        if 'location' in kwargs:
                            event.location = kwargs['location']

                        event.save()

                        date = TZ.localize(
                            date.replace(tzinfo=None) +
                            rd_values[frequency_units]
                        )
                        date_end = TZ.localize(
                            date_end.replace(tzinfo=None) +
                            rd_values[frequency_units]
                        )
            else:
                if 'weekday_list' in kwargs and kwargs['weekday_list']:
                    while date <= date_max:
                        if days_of_week[date.weekday()] in kwargs['weekday_list']:
                            event = self.create(name=name, date_start=date.astimezone(pytz.utc), info=info)

                            if 'all_day' in kwargs:
                                event.all_day = kwargs['all_day']
                            else:
                                event.all_day = False

                            if 'location' in kwargs:
                                event.location = kwargs['location']

                            event.save()

                        date = TZ.localize(
                            date.replace(tzinfo=None) + timedelta(days=1)
                        )
                else:
                    while date <= date_max:
                        event = self.create(name=name, date_start=date.astimezone(pytz.utc), info=info)

                        if 'all_day' in kwargs:
                            event.all_day = kwargs['all_day']
                        else:
                            event.all_day = False

                        if 'location' in kwargs:
                            event.location = kwargs['location']
                        event.save()

                        date = TZ.localize(
                            date.replace(tzinfo=None) +
                            rd_values[frequency_units]
                        )
        elif ends == 1: # ends on date
            if 'ends_on' not in kwargs:
                raise TypeError("create_recurring_event() missing 1 required keyword argument 'ends_on'")

            if 'date_end' in kwargs:
                date_end = kwargs['date_end']

                if 'weekday_list' in kwargs and kwargs['weekday_list']:
                    while date <= kwargs['ends_on'] and date <= date_max:
                        if days_of_week[date.weekday()] in kwargs['weekday_list']:
                            event = self.create(name=name, date_start=date.astimezone(pytz.utc), info=info)

                            event.date_end = date_end.astimezone(pytz.utc)

                            if 'location' in kwargs:
                                event.location = kwargs['location']

                            event.save()

                        date = TZ.localize(
                            date.replace(tzinfo=None) + timedelta(days=1)
                        )
                        date_end = TZ.localize(
                            date_end.replace(tzinfo=None) + timedelta(days=1)
                        )
                else:
                    while date <= kwargs['ends_on'] and date <= date_max:
                        event = self.create(name=name, date_start=date.astimezone(pytz.utc), info=info)

                        event.date_end = date_end.astimezone(pytz.utc)

                        if 'location' in kwargs:
                            event.location = kwargs['location']

                        event.save()

                        date = TZ.localize(
                            date.replace(tzinfo=None) +
                            rd_values[frequency_units]
                        )
                        date_end = TZ.localize(
                            date_end.replace(tzinfo=None) +
                            rd_values[frequency_units]
                        )
            else:
                if 'weekday_list' in kwargs and kwargs['weekday_list']:
                    while date <= kwargs['ends_on'] and date <= date_max:
                        if days_of_week[date.weekday()] in kwargs['weekday_list']:
                            event = self.create(name=name, date_start=date.astimezone(pytz.utc), info=info)

                            if 'all_day' in kwargs:
                                event.all_day = kwargs['all_day']
                            else:
                                event.all_day = False

                            if 'location' in kwargs:
                                event.location = kwargs['location']

                            event.save()

                        date = TZ.localize(
                            date.replace(tzinfo=None) + timedelta(days=1)
                        )
                else:
                    while date <= kwargs['ends_on'] and date <= date_max:
                        event = self.create(name=name, date_start=date.astimezone(pytz.utc), info=info)

                        if 'all_day' in kwargs:
                            event.all_day = kwargs['all_day']
                        else:
                            event.all_day = False

                        if 'location' in kwargs:
                            event.location = kwargs['location']

                        event.save()

                        date = TZ.localize(
                            date.replace(tzinfo=None) +
                            rd_values[frequency_units]
                        )
        elif ends == 2: # ends after a number of occurrences
            if 'ends_after' not in kwargs:
                raise TypeError("create_recurring_event() missing 1 required keyword argument 'ends_after'")

            if 'date_end' in kwargs:
                date_end = kwargs['date_end']

                if 'weekday_list' in kwargs and kwargs['weekday_list']:
                    i = 0
                    while i < kwargs['ends_after'] and date <= date_max:
                        if days_of_week[date.weekday()] in kwargs['weekday_list']:
                            event = self.create(name=name, date_start=date.astimezone(pytz.utc), info=info)

                            event.date_end = date_end.astimezone(pytz.utc)

                            if 'location' in kwargs:
                                event.location = kwargs['location']

                            event.save()

                            i += 1

                        date = TZ.localize(
                            date.replace(tzinfo=None) + timedelta(days=1)
                        )
                        date_end = TZ.localize(
                            date_end.replace(tzinfo=None) + timedelta(days=1)
                        )
                else:
                    i = 0
                    while i < kwargs['ends_after'] and date <= date_max:
                        event = self.create(name=name, date_start=date.astimezone(pytz.utc), info=info)

                        event.date_end = date_end.astimezone(pytz.utc)

                        if 'location' in kwargs:
                            event.location = kwargs['location']

                        event.save()

                        i += 1
                        date = TZ.localize(
                            date.replace(tzinfo=None) +
                            rd_values[frequency_units]
                        )
                        date_end = TZ.localize(
                            date_end.replace(tzinfo=None) +
                            rd_values[frequency_units]
                        )
            else:
                if 'weekday_list' in kwargs and kwargs['weekday_list']:
                    i = 0
                    while i < kwargs['ends_after'] and date <= date_max:
                        if days_of_week[date.weekday()] in kwargs['weekday_list']:
                            event = self.create(name=name, date_start=date.astimezone(pytz.utc), info=info)

                            if 'all_day' in kwargs:
                                event.all_day = kwargs['all_day']
                            else:
                                event.all_day = False

                            if 'location' in kwargs:
                                event.location = kwargs['location']

                            event.save()

                            i += 1

                        date = TZ.localize(
                            date.replace(tzinfo=None) + timedelta(days=1)
                        )
                else:
                    i = 0
                    while i < kwargs['ends_after'] and date <= date_max:
                        event = self.create(name=name, date_start=date.astimezone(pytz.utc), info=info)

                        if 'all_day' in kwargs:
                            event.all_day = kwargs['all_day']
                        else:
                            event.all_day = False

                        if 'location' in kwargs:
                            event.location = kwargs['location']

                        event.save()

                        i += 1
                        date = TZ.localize(
                            date.replace(tzinfo=None) +
                            rd_values[frequency_units]
                        )

        return RecurringEvent.objects.filter(info=info)

    def update_recurring_event(self, request, info):
        from .models import Event, RecurringEvent
        from locations.models import Location, CATEGORIES
        from images.models import Album

        # Data collection
        event_id = request.POST.get('id', '0')
        name = request.POST.get('name', '')
        description = request.POST.get('description', '')
        all_day_value = request.POST.get('all-day', '')
        date_start_str = request.POST.get('date-start', '')
        date_end_str = request.POST.get('date-end', '')
        location_id = request.POST.get('location-id', '0')
        location_name = request.POST.get('location-name', '0')
        album_id = request.POST.get('album-id', '0')
        album_name = request.POST.get('album-name', '0')

        # Relative delta values
        frequency_units = info.frequency_units - 1
        rd_values = [
            relativedelta(days=+info.frequency),
            relativedelta(days=+(7 * info.frequency)),
            relativedelta(months=+info.frequency),
            relativedelta(years=+info.frequency),
        ]

        # Data restructuring
        event_id = int(event_id)
        all_day = all_day_value == 'true'
        location_id = int(location_id)
        album_id = int(album_id)

        # Datetime parsing
        def add_leading_zero_hour(date_str):
            if len(date_str) == 18:
                return date_str[:11] + '0' + date_str[-7:]
            else:
                return date_str

        add_leading_zero_hour(date_start_str)
        date_start = TZ.localize(datetime.strptime(date_start_str, '%m/%d/%Y %I:%M %p'))

        if date_end_str:
            add_leading_zero_hour(date_end_str)
            date_end = TZ.localize(datetime.strptime(date_end_str, '%m/%d/%Y %I:%M %p'))

        if all_day:
            date_start = date_start.replace(hour=0, minute=0, second=0, microsecond=0)

        # Grab location object or set to None
        if location_id <= 0 or location_name == '':
            location = None
        else:
            try:
                location = Location.objects.get(id=location_id)
            except Location.DoesNotExist:
                try:
                    event = Event.objects.get(id=event_id)
                except Event.DoesNotExist:
                    return (False, {
                        'errors': [
                            'The specified event could not be found.',
                            'The specified location could not be found.',
                        ],
                        'event_found': False,
                    })

                return (False, {
                    'errors': ['The specified location could not be found.'],
                    'event_found': True,
                    'args': [
                        CATEGORIES[event.location.category] if event.location else 'events',
                        event.location.slug if location else 'undefined',
                        event.slug,
                        event.id,
                    ],
                })

        # Grab album object or set to None
        if album_id <= 0 or album_name == '':
            album = None
        else:
            try:
                album = Album.objects.get(id=album_id)
            except Album.DoesNotExist:
                try:
                    event = Event.objects.get(id=event_id)
                except Event.DoesNotExist:
                    return (False, {
                        'errors': [
                            'The specified event could not be found.',
                            'The specified album could not be found.',
                        ],
                        'event_found': False,
                    })

                return (False, {
                    'errors': ['The specified album could not be found.'],
                    'event_found': True,
                    'args': [
                        CATEGORIES[event.location.category] if event.location else 'events',
                        event.location.slug if location else 'undefined',
                        event.slug,
                        event.id,
                    ],
                })

        # Update events
        events = RecurringEvent.objects.filter(
            info=info,
            date_start__gte=date_start,
        )
        events_len = len(events)
        for event in events:
            if name:
                event.name = name

            if description:
                event.description = description
            event.all_day = all_day

            event.date_start = date_start
            date_start = TZ.localize(
                date_start.replace(tzinfo=None) +
                rd_values[frequency_units]
            )

            if date_end_str:
                event.date_end = date_end
                date_end = TZ.localize(
                    date_end.replace(tzinfo=None) +
                    rd_values[frequency_units]
                )

            event.location = location
            event.album = album

            event.save()

        return (True, {
            'success': 'You have successfully updated %d event%s.' % (events_len, '' if events_len == 1 else 's'),
            'event_found': True,
            'args': [
                CATEGORIES[event.location.category] if location else 'events',
                event.location.slug if location else 'undefined',
                event.slug,
                event.id,
            ],
        })

class RepeatInfoManager(models.Manager):
    def create_repeat_info(self, frequency, frequency_units, ends, **kwargs):
        from .models import Weekday

        info = self.create(frequency=frequency, frequency_units=frequency_units, ends=ends)

        weekday_options = {
            'monday': 0,
            'tuesday': 1,
            'wednesday': 2,
            'thursday': 3,
            'friday': 4,
            'saturday': 5,
            'sunday': 6,
        }

        if 'weekday_list' in kwargs:
            info.weekly = True
            for weekday in kwargs['weekday_list']:
                Weekday.objects.create_weekday(info, weekday_options[weekday])
        elif frequency == 1 and frequency_units == 2:
            info.weekly = True
        else:
            info.weekly = False

        if ends == 1: # ends on date
            if 'ends_on' in kwargs:
                info.ends_on = kwargs['ends_on']
            else:
                raise TypeError("create_repeat_info() missing 1 required keyword argument 'ends_on'")
        elif ends == 2: # ends after a number of occurrences
            if 'ends_after' in kwargs:
                info.ends_after = kwargs['ends_after']
            else:
                raise TypeError("create_repeat_info() missing 1 required keyword argument 'ends_after'")

        info.save()

        return info

class WeekdayManager(models.Manager):
    def create_weekday(self, info, weekday):
        return self.create(info=info, weekday=weekday)

