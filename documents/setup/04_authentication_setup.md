## Authentication Setup

Authentication uses `django-allauth` with email login and optional Google OAuth.

Public users can read all published posts without any account. Registration is only needed for leaving comments.

---

### Configuration (already done)

Settings in `config/settings.py`:

```python
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'optional'
SOCIALACCOUNT_LOGIN_ON_GET = True
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'
```

---

### Restricted Views

Comment submission requires login (`@login_required` on `PostDetailView.post`). All read views are public.

To make specific posts private in the future, add a `visibility` field to the `Post` model and filter in views.

---

### Google OAuth Setup

**Step 1 — Google Cloud Console**

1. Go to https://console.cloud.google.com/apis/credentials
2. Create an OAuth 2.0 Client ID (Web Application)
3. Add Authorized redirect URIs:
   - `http://localhost:8000/accounts/google/login/callback/`
   - `https://unscripted.jaycurtis.org/accounts/google/login/callback/`
4. Copy the **Client ID** and **Client Secret**

**Step 2 — Register in Django Admin**

```bash
# Local
uv run python manage.py runserver

# Production: exec into pod
kubectl exec -n unscripted-living -it <pod-name> -- /bin/sh
```

Log into `/admin`:
- Go to **Social Applications**
- Add new:
  - Provider: Google
  - Name: Google
  - Client ID: (from Google Cloud)
  - Secret: (from Google Cloud)
  - Sites: add `unscripted.jaycurtis.org` (or localhost for dev)

---

### Auth Templates

Custom auth templates live in `templates/account/`:
- `login.html` — email + Google button
- `signup.html` — registration form + Google button
- `logout.html` — confirmation page
- `password_reset.html` — email reset form

These extend `templates/account/base.html` which wraps in the site layout.
