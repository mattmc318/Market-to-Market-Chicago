import magic

from django.contrib import messages
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from django.http import HttpResponseForbidden
from django.shortcuts import reverse
from django.utils.translation import ugettext as _

class AlbumManager(models.Manager):
    def album(self, album_title, album_id):
        from .models import Album, Image

        try:
            album = Album.objects.get(id=album_id)
        except Album.DoesNotExist:
            return (False, {
                'status': 'invalid ID',
                'error': 'The specified album could not be found.',
            })

        if album_title != album.slug:
            return (False, {
                'status': 'invalid slug',
                'args': [album.slug, album_id],
            })

        return (True, {
            'album': album,
            'images': Image.objects.filter(album__id=album_id),
        })

    def update_title(self, request, album_id):
        from .forms import UpdateAlbumTitleForm
        from .models import Album

        form = UpdateAlbumTitleForm(request.POST)

        # Check if user is logged in
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to update an album.')

            raise PermissionDenied()

        # Basic validations
        if form.is_valid():
            # Data collection
            title = form.cleaned_data['title']
            album_id = int(album_id)

            # Additional validations
            errors = []

            try:
                album = Album.objects.get(id=album_id)
            except Album.DoesNotExist:
                raise ValidationError(_('The specified album could not be found.'), code='not found')

            if album.title == title:
                raise ValidationError(_('Please choose a different title than the existing one.'), code='titles match')

            # Update album
            old_title = album.title
            album.title = title

            # Check permissions
            try:
                if request.user != album.created_by and not request.user.is_superuser:
                    return HttpResponseForbidden()
            except User.DoesNotExist:
                return HttpResponseForbidden()

            album.save()

            punctuation = title[-1]
            return {
                'success': 'The album with the name "%s" has successfully been changed to "%s%s"' % (old_title, title, '' if punctuation == '?' or punctuation == '!' or punctuation == '.' else '.'),
                'args': [album.slug, album_id],
            }

        raise ValidationError(_('The form data entered was not valid.'), code='invalid')

    def upload_images(self, album, images):
        from .models import Image

        for image in images:
            # Check MIME Content-Type before saving
            filetype = magic.from_buffer(image.read(2048), mime=True)

            def accept():
                img = Image.objects.create(image=image, album=album)
                img.image_ops()
                img.save()

            actions = {
                'image/gif': accept,
                'image/jpeg': accept,
                'image/png': accept,
            }

            try:
                actions[filetype]()
            except KeyError:
                raise ValidationError(_('Files with the MIME Content-Type "%s" are not supported. Please only choose images with *.gif, *.jpeg, or *.png file extensions.' % filetype), code='invalid')

    def add_images(self, request, album_id):
        from .models import Album

        # Check if user is logged in
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to update an album.')

            raise PermissionDenied()

        # Data collection
        images = request.FILES.getlist('images', [])
        album_id = int(album_id)

        # Validations
        errors = []

        try:
            album = Album.objects.get(id=album_id)
        except Album.DoesNotExist:
            raise ValidationError(_('The specified album could not be found.'), code='not found')

        # Check permissions
        try:
            if request.user != album.created_by and not request.user.is_superuser:
                return HttpResponseForbidden()
        except User.DoesNotExist:
            return HttpResponseForbidden()

        # Image creation
        self.upload_images(album, images)

        len_images = len(images)
        title = album.title
        punctuation = title[-1]
        return {
            'success': 'You have successfully added %d image%s to the album "%s%s"' % (len_images, '' if len_images == 1 else 's', title, '' if punctuation == '?' or punctuation == '!' or punctuation == '.' else '.'),
            'args': [album.slug, album_id],
        }

    def remove_images(self, request, album_id):
        from .models import Album, Image

        # Check if user is logged in
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to update an album.')

            raise PermissionDenied()

        # Data collection
        images = request.POST.getlist('images', [])
        album_id = int(album_id)

        # Validations
        errors = []

        try:
            album = Album.objects.get(id=album_id)
        except Album.DoesNotExist:
            raise ValidationError(_('The specified album could not be found.'), code='not found')

        # Check permissions
        try:
            if request.user != album.created_by and not request.user.is_superuser:
                return HttpResponseForbidden()
        except User.DoesNotExist:
            return HttpResponseForbidden()

        # Image removal
        return Image.objects.remove_images(album, images)

    def delete_album(self, request, album_id):
        from .models import Album, Image
        from articles.models import Article

        # Check if user is logged in
        if not request.user.is_authenticated:
            messages.error(request, 'You must be logged in to update an album.')

            raise PermissionDenied()

        # Data collection
        album_id = int(album_id)

        # Validations
        errors = []

        try:
            album = Album.objects.get(id=album_id)
            title = album.title
        except Album.DoesNotExist:
            raise ValidationError(_('The specified album could not be found.'), code='not found')

        # Check permissions
        try:
            if request.user != album.created_by and not request.user.is_superuser:
                return HttpResponseForbidden()
        except User.DoesNotExist:
            return HttpResponseForbidden()

        # Clear album from any articles
        for article in Article.objects.filter(album=album):
            article.album = None
            article.save()

        # Image removal
        for image in Image.objects.filter(album=album):
            image.image.delete()
            image.thumbnail.delete()
            image.delete()

        # Album removal
        album.delete()

        return {'success': 'The album "%s" was successfully deleted along with its containing images.' % title}

    def autocomplete(self, request):
        from .models import Album

        query = request.GET.get('q', '')
        albums = []

        if not request.user.is_superuser:
            return HttpResponseForbidden()

        if query == '':
            return {'albums': []}

        for album in Album.objects.filter(title__icontains=query) \
        .order_by('title')[:5]:
            albums.append({
                'id': album.id,
                'title': album.title,
            })

        return {'albums': albums}

class ImageManager(models.Manager):
    def remove_images(self, album, images):
        from .models import Image

        errors = []
        count = 0

        if not images:
            errors.append(ValidationError(_('Please select at least one image to delete.'), code='none selected'))
        for image_id in images:
            try:
                image = Image.objects.get(id=image_id)
            except Image.DoesNotExist:
                errors.append(ValidationError(_('The image with ID %s could not be found.' % image_id), code='not found'))

                continue

            if image.album != album:
                title = album.title
                punctuation = title[-1]
                errors.append(ValidationError(_('The image with ID %s could not be deleted as it is not a part of the album "%s%s"' % (image_id, title, '' if punctuation == '?' or punctuation == '!' or punctuation == '.' else '.')), code='invalid album'))

                continue

            image.delete()

            count += 1

        if len(errors) > 1:
            errors = ValidationError(errors, code='invalid')
        elif len(errors) == 1:
            errors = errors[0]

        return {
            'success': 'You have successfully removed %d image%s.' % (count, '' if count == 1 else 's') if count else None,
            'errors': errors,
        }
        