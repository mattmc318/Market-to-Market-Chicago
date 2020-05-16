from datetime import datetime

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import (
    HttpResponseBadRequest,
    HttpResponseRedirect,
)
from django.shortcuts import render, redirect, reverse, get_object_or_404

from .models import Album, Image
from .forms import CreateAlbumForm, UpdateAlbumTitleForm, AddImagesForm
from mtm.settings import TZ, NAME

def create_album(request):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    form = CreateAlbumForm(request.POST, request.FILES)
    if form.is_valid():
        album = form.save(commit=False)
        album.created_by = get_object_or_404(User, id=request.user.id)
        album.save()

        images = request.FILES.getlist('images', [])
        for image in images:
            img = Image.objects.create(image=image, album=album)
            img.image_ops()
            img.save()

        len_images = len(images)
        punctuation = album.title[-1]
        messages.success(request, 'You have successfully uploaded %d image%s to the album "%s%s"' % (len_images, '' if len_images == 1 else 's', album.title, '' if punctuation == '?' or punctuation == '!' or punctuation == '.' else '.'))

        return HttpResponseRedirect(
            reverse('images:album', args=[album.slug, album.id])
        )

    messages.error(request, 'There was an error uploading the album.')

    return redirect('users:index')

def album(request, slug, album_id):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    valid, response = Album.objects.album(slug, album_id)

    if not valid:
        def invalid_id():
            messages.error(request, response['error'])

            return redirect('users:index')

        def invalid_slug():
            return HttpResponseRedirect(
                reverse('images:album', args=response['args'])
            )

        actions = {
            'invalid ID': invalid_id,
            'invalid slug': invalid_slug,
        }

        return actions[response['status']]()

    update_album_title = UpdateAlbumTitleForm()
    add_images = AddImagesForm()

    return render(request, 'images/album.html', {
        **response,
        'update_album_title': update_album_title,
        'add_images': add_images,
        'user': request.user,
        'name': NAME,
        'year': datetime.now(TZ).year,
    })

def update_album_title(request, slug, album_id):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    try:
        response = Album.objects.update_title(request, album_id)
    except ValidationError as errors:
        for error in errors:
            if error != 'The specified album could not be found.':
                messages.error(request, error)

        return HttpResponseRedirect(
            reverse('images:album', args=[slug, album_id])
        )
    except PermissionDenied:
        return HttpResponseRedirect(
            reverse('images:album', args=[slug, album_id])
        )

    messages.success(request, response['success'])

    return HttpResponseRedirect(
        reverse('images:album', args=response['args'])
    )

def add_images(request, slug, album_id):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    try:
        response = Album.objects.add_images(request, album_id)
    except ValidationError as errors:
        for error in errors:
            messages.error(request, error)

        return HttpResponseRedirect(
            reverse('images:album', args=[slug, album_id])
        )
    except PermissionDenied:
        return HttpResponseRedirect(
            reverse('images:album', args=[slug, album_id])
        )

    messages.success(request, response['success'])

    return HttpResponseRedirect(
        reverse('images:album', args=response['args'])
    )

def delete_images(request, slug, album_id):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    try:
        response = Album.objects.remove_images(request, album_id)
    except PermissionDenied:
        return HttpResponseRedirect(
            reverse('images:album', args=[slug, album_id])
        )

    if response['success']:
        messages.success(request, response['success'])

    if response['errors']:
        for error in response['errors']:
            messages.error(request, error)

    return HttpResponseRedirect(
        reverse('images:album', args=[slug, album_id])
    )

def delete_album(request, slug, album_id):
    if request.method != 'POST':
        return HttpResponseBadRequest()

    try:
        response = Album.objects.delete_album(request, album_id)
    except ValidationError as errors:
        for error in errors:
            messages.error(request, error)

        return redirect('users:index')
    except PermissionDenied:
        return HttpResponseRedirect(
            reverse('images:album', args=[slug, album_id])
        )

    if response['success']:
        messages.success(request, response['success'])

    return redirect('users:index')

def album_autocomplete(request):
    if request.method != 'GET':
        return HttpResponseBadRequest()

    return render(request, 'home/autocomplete.html',
        Album.objects.autocomplete(request)
    )
