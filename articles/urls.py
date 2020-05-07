from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r'^articles/create/$', views.create, name='create'),
    re_path(r'^articles/(?P<slug>[\da-z]+(-[\da-z]+)*)/(?P<article_id>[1-9]\d*)/$', views.article, name='article'),
    re_path(r'^articles/(?P<slug>[\da-z]+(-[\da-z]+)*)/(?P<article_id>[1-9]\d*)/update/$', views.update, name='update'),
    re_path(r'^articles/(?P<slug>[\da-z]+(-[\da-z]+)*)/(?P<article_id>[1-9]\d*)/delete/$', views.delete, name='delete'),
    re_path(r'^articles/by-page/$', views.by_page, name='by-page'),
    re_path(r'^authors/create/$', views.create_author, name='create-author'),
    re_path(r'^authors/(?P<author_id>[1-9]\d*)/$', views.author, name='author'),
]
