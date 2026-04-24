from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db.models import Q
import markdown
import bleach

from .models import Category, Post, Tag
from .forms import CommentForm

ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3',
    'h4', 'h5', 'h6', 'blockquote', 'code', 'pre', 'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td', 'hr',
]
ALLOWED_ATTRS = {
    'a': ['href', 'title', 'rel'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
}


def render_markdown(text):
    html = markdown.markdown(
        text,
        extensions=['fenced_code', 'tables', 'nl2br', 'toc'],
    )
    return bleach.clean(html, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRS)


class HomeView(View):
    def get(self, request):
        categories = Category.objects.all()
        featured_posts = (
            Post.objects.filter(status=Post.STATUS_PUBLISHED, featured=True)
            .select_related('category', 'author')[:6]
        )
        recent_posts = (
            Post.objects.filter(status=Post.STATUS_PUBLISHED)
            .select_related('category', 'author')
            .order_by('-published_at')[:6]
        )
        return render(request, 'blog/home.html', {
            'categories': categories,
            'featured_posts': featured_posts,
            'recent_posts': recent_posts,
        })


class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        return (
            Post.objects.filter(status=Post.STATUS_PUBLISHED)
            .select_related('category', 'author')
            .order_by('-published_at')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['page_title'] = 'All Posts'
        ctx['categories'] = Category.objects.all()
        return ctx


class CategoryDetailView(View):
    def get(self, request, slug):
        category = get_object_or_404(Category, slug=slug)
        posts = (
            Post.objects.filter(category=category, status=Post.STATUS_PUBLISHED)
            .select_related('author')
            .order_by('-published_at')
        )
        return render(request, 'blog/category_detail.html', {
            'category': category,
            'posts': posts,
            'categories': Category.objects.all(),
        })


class PostDetailView(View):
    def get(self, request, slug):
        post = get_object_or_404(Post, slug=slug, status=Post.STATUS_PUBLISHED)
        comments = post.comments.filter(approved=True).select_related('author')
        comment_form = (
            CommentForm()
            if request.user.is_authenticated and post.comments_enabled
            else None
        )
        rendered_content = render_markdown(post.content)
        return render(request, 'blog/post_detail.html', {
            'post': post,
            'comments': comments,
            'comment_form': comment_form,
            'rendered_content': rendered_content,
        })

    @method_decorator(login_required)
    def post(self, request, slug):
        post = get_object_or_404(Post, slug=slug, status=Post.STATUS_PUBLISHED)
        if not post.comments_enabled:
            return redirect(post.get_absolute_url())

        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            messages.success(
                request,
                'Your comment has been submitted and is awaiting approval.'
            )
            return redirect(post.get_absolute_url())

        comments = post.comments.filter(approved=True).select_related('author')
        rendered_content = render_markdown(post.content)
        return render(request, 'blog/post_detail.html', {
            'post': post,
            'comments': comments,
            'comment_form': form,
            'rendered_content': rendered_content,
        })


class SearchView(ListView):
    template_name = 'blog/search_results.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        q = self.request.GET.get('q', '').strip()
        if not q:
            return Post.objects.none()
        return (
            Post.objects.filter(status=Post.STATUS_PUBLISHED)
            .filter(Q(title__icontains=q) | Q(summary__icontains=q) | Q(content__icontains=q))
            .select_related('category', 'author')
            .order_by('-published_at')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['query'] = self.request.GET.get('q', '').strip()
        return ctx


class TagPostListView(ListView):
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return (
            Post.objects.filter(tags=self.tag, status=Post.STATUS_PUBLISHED)
            .select_related('category', 'author')
            .order_by('-published_at')
        )

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['tag'] = self.tag
        ctx['page_title'] = f'Posts tagged: {self.tag.name}'
        ctx['categories'] = Category.objects.all()
        return ctx
