# Unscripted Living — Project Roadmap

This document tracks setup progress and planned features.
Credentials and secrets are **not** stored here — see k8s SealedSecrets and local `.env`.

---

## Phase 1: Project Foundation ✅

- [x] Create project directory structure
- [x] Create `.claudeignore`, `.vscode/`, `CLAUDE.md`
- [x] Initialize `pyproject.toml` with all dependencies (Django 6, allauth, OpenTelemetry, etc.)
- [x] Create `manage.py`, `.python-version`
- [x] Configure `config/settings.py` — PostgreSQL, allauth, WhiteNoise, OTEL, logging
- [x] Configure `config/urls.py`, `config/wsgi.py`, `config/asgi.py`
- [x] Configure `config/middleware.py` — JSON request/response logging with user context
- [x] Configure `config/logging_utils.py`, `config/otel_config.py`
- [x] Create `.env.example` (safe to commit — no real credentials)
- [x] Create `.env` (gitignored — contains real local dev credentials)
- [x] Create `.gitignore`

## Phase 2: Blog Application ✅

- [x] Create `blog/` Django app
- [x] Define models: `Category`, `Tag`, `Post`, `Comment`
  - Post supports Markdown content, featured image, status (draft/published), visibility (public/members), tags
  - Comment requires login, auto-approved on submit (admin can reject spam)
  - Category has icon, color, description for card display, optional gallery mode
- [x] Create views: `HomeView`, `PostListView`, `CategoryDetailView`, `PostDetailView`, `TagPostListView`
  - Public access to public posts; members-only posts require login
  - Comment submission requires login
- [x] Create `blog/urls.py`
- [x] Create `blog/forms.py` — `CommentForm`
- [x] Create `blog/admin.py` — full admin with inline comment moderation
- [x] Create `blog/context_processors.py` — injects `nav_categories` into all templates

## Phase 3: Templates & Design ✅

- [x] Create `templates/base.html` — navbar, footer, Bootstrap 5, Google Fonts (Inter + Lora)
- [x] Create homepage (`blog/home.html`) — hero section, category cards grid, featured + recent posts
- [x] Create `blog/_post_card.html` — reusable post card component
- [x] Create `blog/post_list.html` — paginated post list with sidebar
- [x] Create `blog/post_detail.html` — full post + Markdown rendering + comment section
- [x] Create `blog/category_detail.html` — category header with color accent + post grid
- [x] Create auth templates — login, signup, logout, password reset (styled, with Google OAuth button)
- [x] Create `static/css/site.css` — modern clean design with CSS custom properties, card hover effects, category colors, post body typography

## Phase 4: Database ✅

- [x] Create `unscripted-living` database in k8s PostgreSQL (192.168.86.201:30004)
- [x] Install dependencies: `uv sync`
- [x] Run Django migrations: `uv run python manage.py migrate`
- [x] Create superuser: `uv run python manage.py createsuperuser`
- [x] Verify database tables in pgAdmin

## Phase 5: Kubernetes Secrets ✅

- [x] Create `k8s/temp.yaml` (gitignored plain-text secret)
- [x] Seal the secret: `kubeseal -f k8s/temp.yaml -o yaml > k8s/secrets.yaml`
- [x] Delete temp.yaml after sealing
- [x] Apply sealed secret: `kubectl apply -f k8s/secrets.yaml`

## Phase 6: Docker & Kubernetes Deployment ✅

- [x] Create `Dockerfile` (uv-based, OpenTelemetry + gunicorn)
- [x] Create `k8s/deployment.yaml` (namespace: `unscripted-living`, init container for migrations)
- [x] Create `k8s/backup-pvc.yaml`
- [x] Generate `uv.lock`
- [x] Build and push multi-arch Docker image (`jaysuzi5/unscripted-living:latest`)
- [x] Apply namespace and deployment
- [x] Pod running at `192.168.86.239` (LoadBalancer IP)

## Phase 7: Cloudflare Tunnel ✅

- [x] Add tunnel route in Cloudflare Zero Trust:
  - Subdomain: `unscripted`
  - Domain: `jaycurtis.org`
  - Type: HTTP
  - URL: `unscripted-living.unscripted-living.svc.cluster.local:80`
- [x] Test at: https://unscripted.jaycurtis.org/

## Phase 8: Authentication Setup ✅

- [x] Create Google OAuth credentials in Google Cloud Console
  - Authorized redirect URIs:
    - `http://localhost:8000/accounts/google/login/callback/`
    - `https://unscripted.jaycurtis.org/accounts/google/login/callback/`
- [x] Log in to Django admin and register the Google Social App
- [x] Test email + Google login

## Phase 9: Initial Content ✅

- [x] Create initial categories (suggested):
  - Daily Life — `bi-calendar-heart` — `#0ea5e9`
  - Woodworking — `bi-tools` — `#78350f`
  - Photography — `bi-camera` — `#7c3aed`
  - Reading — `bi-book` — `#15803d`
  - Computers & IT — `bi-laptop` — `#0284c7`
  - Guitar — `bi-music-note-beamed` — `#ea580c`
  - Finance — `bi-graph-up` — `#ca8a04`
  - Environment — `bi-tree` — `#16a34a`
  - AI & Tech Thoughts — `bi-cpu` — `#6366f1`
- [x] Write a "Welcome" / first post
- [x] Customize hero text and footer in `base.html`

## Phase 10: Database Backups ✅

- [x] PVC configured (`k8s/backup-pvc.yaml` — 5Gi ReadWriteOnce, staging area)
- [x] Create `k8s/cronjob-backup.yaml` — 4 CronJobs:
  - Local pg_dump to PVC every 6 hours (7-day retention)
  - Daily S3 upload at 2am → `s3://jay-curtis-backup/unscripted-living/backups/daily/YYYY/MM/DD/`
  - Monthly S3 upload on 1st at 3am → `.../monthly/YYYY/MM/`
  - Yearly S3 upload on Jan 1st at 4am → `.../yearly/YYYY/`
- [ ] Apply: `kubectl apply -f k8s/backup-pvc.yaml && kubectl apply -f k8s/cronjob-backup.yaml`
- [ ] Verify: `kubectl get cronjobs -n unscripted-living`
- [ ] Test: `kubectl create job --from=cronjob/unscripted-living-backup-local test-backup -n unscripted-living`

---

## Future Enhancements (Backlog)

- [x] Rich text / WYSIWYG editor (django-markdownx)
- [x] Featured image uploads (add S3 storage via django-storages)
- [x] Full-text search across posts
- [x] RSS feed (`django.contrib.syndication`)
- [x] Post newsletter/email notifications
- [x] Private/members-only posts (extend Post model with `visibility` field)
- [x] Related posts sidebar section
- [x] Reading progress indicator on post detail page
- [x] Dark mode toggle
- [x] Comment notifications for post author (email to jaysuzi5@gmail.com on each comment)
- [x] Social share buttons (X, Facebook, LinkedIn, copy link — on post detail)
- [x] Post archive page (by year/month) — `/archive/`, `/archive/YYYY/`, `/archive/YYYY/MM/`
- [x] Photo gallery category with lightbox — enable `is_gallery` on any Category in admin; uses GLightbox; post body images also get lightbox on all post detail pages

---

## Suggested Enhancements (Backlog)

### SEO & Discoverability
- [ ] Open Graph / Twitter Card meta tags — per-post `og:title`, `og:description`, `og:image` for rich link previews on social media
- [ ] Sitemap (`django.contrib.sitemaps`) — auto-generated XML sitemap; submit to Google Search Console
- [ ] `robots.txt` — serve via a simple view; disallow `/admin/`, allow everything else

### Content & Reading UX
- [ ] Table of contents on long posts — render the TOC generated by the existing `toc` markdown extension; show in sidebar or collapsible at top of post
- [ ] Copy-to-clipboard button on code blocks — inject a copy button on `<pre><code>` blocks via JS
- [ ] Back-to-top button — appears after scrolling down; smooth-scrolls to top
- [ ] Post view counter — increment on each detail page load; surface as "N views" on detail page and "popular posts" widget in sidebars
- [ ] Post series — link ordered multi-part posts (e.g., a woodworking build across 3 posts); `Series` model with ordered `Post` M2M; prev/next navigation on detail page

### Site Basics
- [x] Custom 404 and 500 error pages — styled templates matching the site design (`templates/404.html`, `templates/500.html`)
- [x] Favicon — add a favicon (feather icon or custom) to `base.html`

### Auth & Newsletter
- [ ] Double opt-in for newsletter — send confirmation email on subscribe; add `confirmed` field to `NewsletterSubscriber`; only send post notifications to confirmed subscribers
- [ ] Subscriber management page for admin — simple view at `/admin/subscribers/` showing count, active vs. unsubscribed, with CSV export

### Admin / Operations
- [ ] Scheduled publishing — allow setting `published_at` in the future in admin; a management command or k8s CronJob publishes posts whose `published_at` has passed
- [x] Remove `test_email_view` — temporary view in `blog/views.py` and URL in `blog/urls.py`; remove once email is confirmed working in production
