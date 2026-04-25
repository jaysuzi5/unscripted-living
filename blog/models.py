import uuid

from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.utils import timezone
from markdownx.models import MarkdownxField
from PIL import Image


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=60, blank=True, help_text='Bootstrap Icons class, e.g. bi-camera')
    color = models.CharField(max_length=30, default='#2563eb', help_text='CSS hex color for the category accent')
    order = models.PositiveIntegerField(default=0)
    is_gallery = models.BooleanField(default=False, help_text='Display posts as a photo gallery grid')

    class Meta:
        ordering = ['order', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('category_detail', kwargs={'slug': self.slug})

    @property
    def published_post_count(self):
        return self.posts.filter(status=Post.STATUS_PUBLISHED).count()


class Tag(models.Model):
    name = models.CharField(max_length=50)
    slug = models.SlugField(unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('tag_posts', kwargs={'slug': self.slug})


class Post(models.Model):
    STATUS_DRAFT = 'draft'
    STATUS_PUBLISHED = 'published'
    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    VISIBILITY_PUBLIC = 'public'
    VISIBILITY_MEMBERS = 'members'
    VISIBILITY_CHOICES = [
        (VISIBILITY_PUBLIC, 'Public'),
        (VISIBILITY_MEMBERS, 'Members only'),
    ]

    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=250)
    category = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='posts'
    )
    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='posts'
    )
    summary = models.TextField(
        max_length=500, blank=True, help_text='Brief description shown in listings'
    )
    content = MarkdownxField(help_text='Markdown supported')
    featured_image = models.ImageField(upload_to='posts/%Y/%m/', blank=True, null=True)
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    visibility = models.CharField(
        max_length=20, choices=VISIBILITY_CHOICES, default=VISIBILITY_PUBLIC,
        help_text='Public: visible to all. Members only: requires login.',
    )
    featured = models.BooleanField(default=False, help_text='Show in featured section on homepage')
    comments_enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-published_at', '-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        _send_newsletter = False
        if self.status == self.STATUS_PUBLISHED:
            if self.pk:
                try:
                    old_status = Post.objects.only('status').get(pk=self.pk).status
                    if old_status != self.STATUS_PUBLISHED:
                        _send_newsletter = True
                except Post.DoesNotExist:
                    _send_newsletter = True
            else:
                _send_newsletter = True

        if self.status == self.STATUS_PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)
        if self.featured_image:
            try:
                img = Image.open(self.featured_image.path)
                if img.width > 512 or img.height > 512:
                    img.thumbnail((512, 512))
                    img.save(self.featured_image.path)
            except NotImplementedError:
                from io import BytesIO
                from django.core.files.base import ContentFile
                storage = self.featured_image.storage
                name = self.featured_image.name
                with storage.open(name, 'rb') as f:
                    img = Image.open(f)
                    img.load()
                if img.width > 512 or img.height > 512:
                    img_format = img.format or 'JPEG'
                    img.thumbnail((512, 512))
                    buf = BytesIO()
                    img.save(buf, format=img_format, quality=85)
                    buf.seek(0)
                    storage.save(name, ContentFile(buf.read()))

        if _send_newsletter:
            _send_post_newsletter(self)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('post_detail', kwargs={'slug': self.slug})

    @property
    def approved_comment_count(self):
        return self.comments.filter(approved=True).count()

    @property
    def reading_time_minutes(self):
        word_count = len(self.content.split())
        return max(1, round(word_count / 200))


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.author} on "{self.post}"'


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email


def _send_post_newsletter(post):
    from django.core.mail import send_mail
    subscribers = NewsletterSubscriber.objects.filter(is_active=True)
    if not subscribers.exists():
        return
    post_url = f'https://unscripted.jaycurtis.org{post.get_absolute_url()}'
    for subscriber in subscribers:
        unsub_url = f'https://unscripted.jaycurtis.org/unsubscribe/{subscriber.unsubscribe_token}/'
        body = f'{post.title}\n\n'
        if post.summary:
            body += f'{post.summary}\n\n'
        if post.visibility == Post.VISIBILITY_MEMBERS:
            body += f'This post is for members only. Sign in to read:\n{post_url}\n\n'
        else:
            body += f'Read the full post:\n{post_url}\n\n'
        body += f'---\nUnsubscribe: {unsub_url}'
        send_mail(
            subject=f'New post: {post.title}',
            message=body,
            from_email=None,
            recipient_list=[subscriber.email],
            fail_silently=True,
        )
