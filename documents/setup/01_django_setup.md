## Django Setup

### Project Structure

```
unscripted-living/
├── blog/                       # Main blog application
│   ├── migrations/             # Database migrations
│   ├── templates/blog/         # Blog templates
│   ├── admin.py                # Django admin config
│   ├── apps.py
│   ├── context_processors.py   # Injects nav_categories globally
│   ├── forms.py                # CommentForm
│   ├── models.py               # Category, Tag, Post, Comment
│   ├── urls.py                 # Blog URL routing
│   └── views.py                # All blog views
├── config/                     # Django project config
│   ├── asgi.py
│   ├── logging_utils.py        # log_event() helper
│   ├── middleware.py           # JSON request/response logging
│   ├── otel_config.py          # OpenTelemetry logging init
│   ├── settings.py             # All settings (reads from .env)
│   ├── urls.py                 # Root URL config
│   └── wsgi.py
├── documents/setup/            # This documentation
├── k8s/                        # Kubernetes manifests
├── static/css/site.css         # Main stylesheet
├── templates/                  # Project-level templates
│   ├── base.html               # Master layout
│   ├── account/                # Allauth template overrides
│   └── blog/                   # Blog templates
├── .env                        # Local credentials (gitignored)
├── .env.example                # Template for .env
├── Dockerfile
├── manage.py
└── pyproject.toml
```

### Development Commands

```bash
uv sync                                    # install/update dependencies
uv run python manage.py runserver          # dev server
uv run python manage.py migrate            # apply migrations
uv run python manage.py makemigrations     # create new migrations
uv run python manage.py createsuperuser    # create admin user
uv run python manage.py check              # system check
uv add <package>                           # add a dependency
```

### Adding a New Model

1. Edit `blog/models.py`
2. Run `uv run python manage.py makemigrations blog`
3. Run `uv run python manage.py migrate`
4. Register in `blog/admin.py`

### Content Management

All content is managed through Django Admin at `/admin/`:
- Create/edit Categories (set icon, color, description)
- Write and publish Posts (supports Markdown)
- Moderate Comments (approve/reject)
- Manage Tags
