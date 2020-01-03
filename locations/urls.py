from django.urls import path, re_path

from . import views

urlpatterns = [
    # path('nightlife/', views.nightlife, name='nightlife'),
    # path('restaurants/', views.restaurants, name='restaurants'),
    # path('arts-and-entertainment/', views.arts_and_entertainment, name='arts_and_entertainment'),
    # path('health-and-fitness/', views.health_and_fitness, name='health_and_fitness'),
    # path('sports/', views.sports, name='sports'),
    # path('non-profit/', views.non_profit, name='non_profit'),
    path('neighborhoods/autocomplete/', views.neighborhoods_autocomplete, name='neighborhoods_autocomplete'),
    re_path(r'^neighborhoods/(?P<neighborhood_name>[a-z]+(-[a-z]+)*)/(?P<neighborhood_id>[1-9]\d*)/$', views.neighborhood, name='neighborhood'),
    path('locations/autocomplete/', views.locations_autocomplete, name='locations_autocomplete'),
    re_path(r'^(?P<category>[a-z]+(-[a-z]+)*)/(?P<location_name>[a-z\d]+(-[a-z\d]+)*)/(?P<location_id>[1-9]\d*)/$', views.location, name='location'),
    re_path(r'^(?P<category>[a-z]+(-[a-z]+)*)/(?P<location_name>[a-z\d]+(-[a-z\d]+)*)/(?P<event_name>[a-z\d]+(-[a-z\d]+)*)/(?P<event_id>[1-9]\d*)/$', views.event, name='event'),
]
