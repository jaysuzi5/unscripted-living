from django.contrib.syndication.views import Feed
from .models import Post


class LatestPostsFeed(Feed):
    title = "Unscripted Living"
    link = "/posts/"
    description = "Latest posts from Unscripted Living — retirement stories, hobbies, and honest thoughts."

    def items(self):
        return (
            Post.objects.filter(status=Post.STATUS_PUBLISHED)
            .select_related('author')
            .order_by('-published_at')[:20]
        )

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.summary or item.content[:300]

    def item_pubdate(self, item):
        return item.published_at

    def item_link(self, item):
        return item.get_absolute_url()

    def item_author_name(self, item):
        return item.author.get_full_name() or item.author.username if item.author else ''
