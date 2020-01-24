from django.urls import path, re_path

from . import views

urlpatterns = [
    path('create/', views.create, name='create'),
    re_path(r'^(?P<album_title>[\da-z]+(-[\da-z]+)*)/(?P<album_id>[1-9]\d*)/$', views.album, name='album'),
    re_path(r'^(?P<album_title>[\da-z]+(-[\da-z]+)*)/(?P<album_id>[1-9]\d*)/update_album_title/$', views.update_album_title, name='update_album_title'),
]
