from django.contrib import admin
from markdownx.admin import MarkdownxModelAdmin
from .models import Category, Tag, Post, Comment


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'order', 'published_post_count']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ['author', 'created_at']
    fields = ['author', 'content', 'approved', 'created_at']


@admin.register(Post)
class PostAdmin(MarkdownxModelAdmin):
    list_display = ['title', 'category', 'author', 'status', 'featured', 'published_at', 'approved_comment_count']
    list_filter = ['status', 'category', 'featured', 'created_at']
    list_editable = ['status', 'featured']
    search_fields = ['title', 'content', 'summary']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['tags']
    inlines = [CommentInline]
    date_hierarchy = 'created_at'
    save_on_top = True
    readonly_fields = ['created_at', 'updated_at', 'published_at']

    fieldsets = [
        (None, {
            'fields': ['title', 'slug', 'category', 'author', 'status', 'featured'],
        }),
        ('Content', {
            'fields': ['summary', 'content', 'featured_image'],
        }),
        ('Tags & Options', {
            'fields': ['tags', 'comments_enabled'],
        }),
        ('Timestamps', {
            'fields': ['created_at', 'updated_at', 'published_at'],
            'classes': ['collapse'],
        }),
    ]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['post', 'author', 'approved', 'created_at']
    list_filter = ['approved', 'created_at']
    list_editable = ['approved']
    actions = ['approve_comments', 'reject_comments']

    @admin.action(description='Approve selected comments')
    def approve_comments(self, request, queryset):
        queryset.update(approved=True)

    @admin.action(description='Reject selected comments')
    def reject_comments(self, request, queryset):
        queryset.update(approved=False)
