from django.urls import path
from . import views
from .feeds import LatestPostsFeed

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('posts/', views.PostListView.as_view(), name='post_list'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('post/<slug:slug>/', views.PostDetailView.as_view(), name='post_detail'),
    path('tag/<slug:slug>/', views.TagPostListView.as_view(), name='tag_posts'),
    path('archive/', views.ArchiveView.as_view(), name='archive'),
    path('archive/<int:year>/', views.ArchiveYearView.as_view(), name='archive_year'),
    path('archive/<int:year>/<int:month>/', views.ArchiveMonthView.as_view(), name='archive_month'),
    path('test-email/', views.test_email_view, name='test_email'),
    path('search/', views.SearchView.as_view(), name='search'),
    path('rss/', LatestPostsFeed(), name='rss_feed'),
]
