from django.urls import path, re_path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('month/', views.month, name='month'),
    path('by-date/', views.by_date, name='by_date'),
    path('by-location/', views.by_location, name='by_location'),
    path('prev/', views.prev, name='prev'),
    path('next/', views.next, name='next'),
    re_path(r'^(?P<location>[a-z\d-]+)/(?P<name>[a-z\d-]+)/(?P<id>[1-9]\d*)/$', views.event, name='event'),
]
