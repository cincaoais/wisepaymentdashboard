# 012 – Project structure
Date: 3 October 2026
Roadmap step: Step 1.1

## Question
Where will every future file live, before I create it?
1. One Django app or two (or more)? Why?
2. Where will the code that talks to Wise live? It must be one place only. Why?
3. When Stripe arrives, where will its code go?
4. Which app owns the custom user model? Why decide before the first `migrate`?
5. What is the empty `core/` folder for: keep, repurpose or delete?

## Sources (links)
| # | Title | URL (full) | Domain | Type | Date | What it proves |
|---|---|---|---|---|---|---|
| S1 | Tutorial part 1, "Projects vs. apps" | https://docs.djangoproject.com/en/6.1/intro/tutorial01/ | docs.djangoproject.com | official doc | accessed 2026-10-03 (Django 6.1) | An app "does something"; a project is "a collection of configuration and apps"; `startapp` runs beside `manage.py` |
| S2 | Applications | https://docs.djangoproject.com/en/6.1/ref/applications/ | docs.djangoproject.com | official doc | accessed 2026-10-03 | An app is "a Python package that provides some set of features" (models, views, templates, URLs…). The project package often holds templates and fixtures not tied to one app |
| S3 | Customizing authentication: "Using a custom user model when starting a project" | https://docs.djangoproject.com/en/6.1/topics/auth/customizing/ | docs.djangoproject.com | official doc | accessed 2026-10-03 | Subclass `AbstractUser`; set `AUTH_USER_MODEL` "before creating any migrations or running `manage.py migrate` for the first time"; a later change "can be complex"; the model must be in its app's first migration; register it with `UserAdmin` in the app's `admin.py` |
| S4 | How to create custom django-admin commands | https://docs.djangoproject.com/en/6.1/howto/custom-management-commands/ | docs.djangoproject.com | official doc | accessed 2026-10-03 | Layout `app/management/commands/`, with `__init__.py` in both folders; works only for apps in `INSTALLED_APPS`; files starting with `_` are not commands |
| S5 | Fixtures | https://docs.djangoproject.com/en/6.1/topics/db/fixtures/ | docs.djangoproject.com | official doc | accessed 2026-10-03 | `loaddata` searches the `fixtures` folder of every installed app, then `FIXTURE_DIRS`, then a literal path |
| S6 | django-admin: `createsuperuser`, `startapp` | https://docs.djangoproject.com/en/6.1/ref/django-admin/ | docs.djangoproject.com | official doc | accessed 2026-10-03 | `--noinput` reads `DJANGO_SUPERUSER_<FIELD>` and `DJANGO_SUPERUSER_PASSWORD`; with no password the user "will not be able to log in" |
| S7 | `loaddata.py`, branch stable/6.1.x | https://raw.githubusercontent.com/django/django/stable/6.1.x/django/core/management/commands/loaddata.py | raw.githubusercontent.com | official GitHub | accessed 2026-10-03 | `parse_name` splits the name on dots. `loaddata auth.group` fails: "group is not a known serialization format" |
| S8 | Tutorial part 3, "Template namespacing" | https://docs.djangoproject.com/en/6.1/intro/tutorial03/ | docs.djangoproject.com | official doc | accessed 2026-10-03 | App templates go in `app/templates/app/`, so two apps can't clash on a name |
| S9 | Tutorial part 7, project templates | https://docs.djangoproject.com/en/6.1/intro/tutorial07/ | docs.djangoproject.com | official doc | accessed 2026-10-03 | A project `templates/` folder beside `manage.py`, listed in `TEMPLATES` `DIRS` |
| S10 | Using the authentication system | https://docs.djangoproject.com/en/6.1/topics/auth/default/ | docs.djangoproject.com | official doc | accessed 2026-10-03 | `LoginView` uses `registration/login.html` by default; `django.contrib.auth.urls` gives login and logout URLs |
| S11 | The Twelve-Factor App: Config | https://12factor.net/config | 12factor.net | blog | accessed 2026-10-03 | Config lives in environment variables; the code could be open-sourced "without compromising any credentials" |
| S12 | cookiecutter-django (13.6k stars) | https://github.com/cookiecutter/cookiecutter-django | github.com | community GitHub | last commit 2026-10-02 | README: "Comes with custom user model ready to go" |
| S13 | cookiecutter-django, `config/settings/base.py` | https://github.com/cookiecutter/cookiecutter-django/blob/main/%7B%7Bcookiecutter.project_slug%7D%7D/config/settings/base.py | github.com | community GitHub | last commit 2026-10-02 | Settings live in a `config/` package; `LOCAL_APPS` has a `users` app; `AUTH_USER_MODEL = "users.User"`; `FIXTURE_DIRS` names one project-level `fixtures` folder |
| S14 | HackSoftware/Django-Styleguide, README (6.3k stars) | https://github.com/HackSoftware/Django-Styleguide | github.com | community GitHub | last commit 2025-09-25 | Business logic lives in services (`<your_app>/services.py`), not in views; services may call external services; "you can just have services" if selectors don't fit |
| S15 | Django-Styleguide-Example (957 stars), `integrations/aws/` | https://github.com/HackSoftware/Django-Styleguide-Example/tree/master/styleguide_example/integrations/aws | github.com | community GitHub | last commit 2025-10-26 | One folder per vendor; it holds only `__init__.py` and `client.py` |
| S16 | Django-Styleguide-Example, `files/services.py` | https://github.com/HackSoftware/Django-Styleguide-Example/blob/master/styleguide_example/files/services.py | github.com | community GitHub | last commit 2025-10-26 | The service imports `s3_generate_presigned_post` from the AWS client. It does not talk to AWS itself |
| S17 | Django-Styleguide-Example, `core/` | https://github.com/HackSoftware/Django-Styleguide-Example/tree/master/styleguide_example/core | github.com | community GitHub | last commit 2025-10-26 | Their `core` app holds real code: `apps.py`, `exceptions.py`, `migrations/` |
| S18 | saleor/saleor (23.4k stars), `saleor/payment/` | https://github.com/saleor/saleor/tree/main/saleor/payment | github.com | community GitHub | last commit 2026-10-02 | One provider-neutral `payment` app (`models.py`, `interface.py`, `gateway.py`) with a `gateways/` folder inside |
| S19 | Saleor `payment/gateways/` at tag 3.20.0 | https://github.com/saleor/saleor/tree/3.20.0/saleor/payment/gateways | github.com | community GitHub | accessed 2026-10-03 | One sub-package per provider: `adyen`, `authorize_net`, `braintree`, `dummy`, `dummy_credit_card`, `np_atobarai`, `razorpay`, `stripe` |
| S20 | Saleor, commit history of `payment/gateways/` | https://github.com/saleor/saleor/commits/main/saleor/payment/gateways | github.com | community GitHub | last commit 2026-07-30 | March–July 2026 commits removed Adyen, NP Atobarai, authorize.net, Braintree, Razorpay and Dummy |
| S21 | soldatov-ss/django-referral-system (56 stars), `promoter_payout_service.py` | https://raw.githubusercontent.com/soldatov-ss/django-referral-system/main/referrals/services/promoter_payout_service.py | raw.githubusercontent.com | community GitHub | last commit 2026-04-21 | A Django app keeps its Wise payout code in `referrals/services/`. It builds a CSV for Wise and makes no HTTP calls. It saves `payout_method="wise"` as a value |
| S22 | lolml-gmbh/wise-statements (4 stars) | https://github.com/lolml-gmbh/wise-statements | github.com | community GitHub | accessed 2026-10-03 (GitHub topic page: last updated 2024-04-19) | A Streamlit (not Django) app: "All interactions with the Wise API … are managed in the `wise.py` file" |
| S23 | GitHub repository search "django transferwise" | https://github.com/search?q=django+transferwise&type=repositories | github.com | community GitHub | accessed 2026-10-03 | 0 repositories found |
| S24 | Saleor `payment/gateways/` on main | https://github.com/saleor/saleor/tree/main/saleor/payment/gateways | github.com | community GitHub | accessed 2026-10-03 | Today only `stripe/` is left (plus `__init__.py`, `utils.py`) |

## Experiment (request, response, screenshots – token removed)
No Wise call needed. Run these in order, from the workspace root. Nothing is committed yet, so plain `mv` is fine.

```bash
source .venv/bin/activate
cd wisepaymentdashboard                      # the folder with manage.py (BASE_DIR)
ls -l db.sqlite3                             # 0 bytes = never migrated
find core                                    # only empty folders
rmdir core/admin core/management core        # rmdir refuses if a folder is not empty
python manage.py startapp users
mkdir users/fixtures
mv fixtures/auth.group.json users/fixtures/groups.json
# In your editor: delete the "users.user" object from groups.json. Keep the "auth.group" object.
rmdir fixtures
mkdir -p templates/registration
mkdir -p payments/providers payments/management/commands payments/templates/payments
touch payments/providers/__init__.py payments/providers/wise.py
touch payments/management/__init__.py payments/management/commands/__init__.py
touch payments/services.py payments/forms.py payments/urls.py
rm payments/tests.py
mkdir -p payments/tests/wise_responses
touch payments/tests/__init__.py
# In your editor: settings.py (INSTALLED_APPS, AUTH_USER_MODEL, TEMPLATES DIRS),
# then users/models.py and users/admin.py.
python manage.py makemigrations users        # expect users/migrations/0001_initial.py
python manage.py check
# STOP. Do not run migrate now. The first migrate is Step 1.5, on Postgres.
# Step 1.5, with DJANGO_SUPERUSER_USERNAME, _EMAIL and _PASSWORD set from .env:
python manage.py migrate
python manage.py createsuperuser --noinput
python manage.py loaddata groups
```

## Finding (in your own words)
- **Django's own words.** A project is settings plus apps. An app "does something" [S1]. An app is a package with some mix of models, views, templates and URLs [S2]. Site-wide templates can sit in a project `templates/` folder [S2][S9]. App templates go in `app/templates/app/` [S8].
- **Custom user.** Start with a subclass of `AbstractUser`. Point `AUTH_USER_MODEL` at it before any migration or the first `migrate` [S3]. Changing it later needs manual fixes to the database [S3]. The model must be in its app's first migration [S3].
- **Commands.** A command only exists inside an installed app, in `management/commands/`. The docs show an `__init__.py` in both folders [S4].
- **Fixtures.** `loaddata` looks in each app's `fixtures` folder, in `FIXTURE_DIRS`, or at a full path [S5]. Our `fixtures/` folder beside `manage.py` is neither of the first two, so `loaddata` can't find it by name. A dotted name like `auth.group` also fails, because Django reads the last part as the file format [S7].
- **Superuser.** `createsuperuser --noinput` takes its values from `DJANGO_SUPERUSER_*` environment variables [S6]. This keeps secrets out of the code, as 12-factor asks [S11].
- **cookiecutter-django** has a `users` app and `AUTH_USER_MODEL = "users.User"` [S12][S13]. We borrow the `users` app. We skip the rest; it is built for bigger projects.
- **HackSoft** keeps views thin and puts logic in `services.py` [S14]. Each outside vendor gets one client file (`integrations/aws/client.py`). The service imports it [S15][S16]. We borrow both ideas. Their `core` app exists because it holds real code [S17].
- **Saleor** has one neutral `payment` app with one folder per provider inside `gateways/` [S18][S19]. In 2026 they deleted most provider folders one at a time; only `stripe/` is left [S20][S24]. My reading: one folder per provider makes adding or removing a provider a small change.
- **Wise in Django.** I found no public Django project that calls the Wise API. GitHub finds 0 repos for "django transferwise" [S23]. The closest is a Django app that keeps its Wise payout code in a services module (CSV only) [S21]. A small non-Django Wise app keeps all Wise API calls in one `wise.py` [S22].

## Decision (what you will do and why)
**Q1. Two apps: `users` and `payments`.** Each one "does something" [S1]. `users` decides who can log in. `payments` holds the payment data, the provider clients, the logic and the ~7 pages. Pages, models and logic change together, so they share one app. Inside it, files split the jobs: `providers/` for HTTP, `services.py` for logic, `views.py` for pages [S14]. *Judgement call. Alternative: a third `dashboard` app for views and templates, split off only if `views.py` grows too big to read.*

**Q2. Only `payments/providers/wise.py` talks to Wise.** No other file imports `requests` or knows a Wise URL. Why one place: (a) the token is read once, so it's easy to keep it out of logs (Step 3.1). (b) The base URL and API version (`2026Q4`, new every quarter, roadmap §2) change in one line. (c) Every call passes through one request function, so the API log (02 §6.3, page 5) sees every call. (d) Views get your own error type, never raw `requests` errors. (e) Tests fake HTTP for one module. Services call the client; views call services [S14][S16].

**Q3. Stripe goes in `payments/providers/stripe.py`, next to `wise.py`.** Same shape, same test-first loop (roadmap Phase 7, step 4). This copies Saleor's one-folder-per-provider [S19] and HackSoft's one-client-per-vendor [S15]. No new app. *Judgement call. Alternative: a separate `integrations` app like HackSoft. That is too much for two clients.*

**Q4. The `users` app owns `User`, a subclass of `AbstractUser` with no extra fields yet.** Set `AUTH_USER_MODEL` to `users.User`, like cookiecutter-django [S13]. Do it now: the docs say before the first `migrate`, and later means manual database fixes [S3]. `db.sqlite3` is 0 bytes and never migrated, so today it costs nothing. The old fixture already says `users.user`: app `users`, model `User`. The superuser comes from `createsuperuser --noinput` and `.env` values [S6], not a fixture. A fixture is a file in Git, and a password hash in Git fails the 12-factor test [S11]. The "Admin" group moves to `users/fixtures/groups.json`. `loaddata groups` finds it with no extra setting [S5]. The plain name avoids the dotted-name error [S7]. *Judgement call. Alternative: keep a project `fixtures/` folder and list it in `FIXTURE_DIRS`, like cookiecutter-django [S13].*

**Q5. Delete `core/`.** It has no `__init__.py` and no `apps.py`, it is not in `INSTALLED_APPS`, and Git doesn't track it (checked in this repo). It does nothing. Its two subfolders already have homes. Commands go in the app that owns them: `payments/management/commands/` [S4]. Admin setup goes in each app's `admin.py` [S3]. HackSoft has a `core` because it holds real shared code [S17]. Re-create `core` only when both apps need the same code.

**Also kept:** the config package keeps its name, `wisepaymentdashboard/`. *Judgement call. Alternative: rename it `config/` like cookiecutter-django [S13]. That edits `manage.py`, `settings.py`, `asgi.py` and `wsgi.py` for little gain.*

```text
wisepaymentdashboard/                  workspace root (Git repo, .venv, .env.example, README.md)
├── docs/rnd/012-project-structure.md
└── wisepaymentdashboard/              BASE_DIR
    ├── manage.py
    ├── wisepaymentdashboard/          config package: settings.py, urls.py, asgi.py, wsgi.py
    ├── templates/
    │   ├── base.html
    │   └── registration/login.html
    ├── users/
    │   ├── __init__.py  apps.py  admin.py  models.py  tests.py  views.py
    │   ├── fixtures/groups.json
    │   └── migrations/
    │       ├── __init__.py
    │       └── 0001_initial.py
    └── payments/
        ├── __init__.py  apps.py  admin.py  models.py
        ├── services.py
        ├── forms.py  views.py  urls.py
        ├── providers/
        │   ├── __init__.py
        │   ├── wise.py                the ONLY module that calls Wise
        │   └── stripe.py              Phase 7 (do not create yet)
        ├── templates/payments/        one template per page
        ├── management/
        │   ├── __init__.py
        │   └── commands/
        │       ├── __init__.py
        │       ├── wise_smoke_test.py      Step 3.4
        │       └── refresh_statuses.py     Phase 5.1
        ├── migrations/__init__.py
        └── tests/
            ├── __init__.py
            ├── wise_responses/        saved Wise JSON, token removed
            ├── test_wise.py
            └── test_services.py
```

**Where things live**
| Concept | Path | Why |
|---|---|---|
| Settings, root URLs | `wisepaymentdashboard/settings.py`, `urls.py` | Project = configuration [S1]. Root URLs add `accounts/` from `django.contrib.auth.urls` [S10] |
| Custom user model | `users/models.py`, `users/admin.py` | Docs pattern [S3]; same as cookiecutter-django [S13] |
| "Admin" group data | `users/fixtures/groups.json` | `loaddata` finds app fixtures by itself [S5] |
| Superuser | `.env` → `createsuperuser --noinput` | No secret in Git [S6][S11] |
| Base layout, login page | `templates/base.html`, `templates/registration/login.html` | Site-wide, not one app's [S9]; `LoginView`'s default name [S10] |
| Payment tables (Phase 2) | `payments/models.py` | Names chosen in Phase 2 (Step 2.3 "Stripe test") |
| Wise HTTP calls | `payments/providers/wise.py` | One place (Q2) |
| Stripe HTTP calls (Phase 7) | `payments/providers/stripe.py` | Sibling slot (Q3) |
| Business steps (call provider, save result) | `payments/services.py` | Logic stays out of views [S14] |
| Pages | `payments/views.py`, `urls.py`, `forms.py`, `templates/payments/` | Thin views; namespaced templates [S8] |
| Smoke test, polling | `payments/management/commands/` | Commands live in an installed app [S4] |
| API activity log | a model in `payments/models.py`, with a provider field | Both providers write to it (02 §8) |
| Saved Wise JSON for tests | `payments/tests/wise_responses/` | Not `payments/fixtures/`: `loaddata` searches that folder [S5]. *Judgement call; alternative: `payments/fixtures/wise/`, which works but mixes two kinds of "fixture"* |

**Names.** Shared by Wise and Stripe, so neutral (02 §8): `payments`, `providers/`, `services.py`, the API log, the list page (it becomes "Transactions"), `refresh_statuses`. Wise-only, so they say "wise": `wise.py`, `wise_smoke_test.py`, `wise_responses/`, `test_wise.py`.

## Open questions
1. Where does `.env` live? `.env.example` is in the workspace root, but `BASE_DIR` is the folder with `manage.py`. Decide in Step 1.4, together with how `createsuperuser` gets the `DJANGO_SUPERUSER_*` values.
2. Who writes the API-log row: the one request function in `wise.py`, or each service? Decide in the Step 3.1 client design note.
3. Does the "Admin" group have a job? It has no permissions, and roles are a non-goal (02 §6.7). If not, drop the fixture.
4. Wise webhooks (Phase 5.2): does the signature check go in `wise.py` or in a new `payments/webhooks.py`? Decide in the webhook note.
5. When Stripe arrives, do both clients share one base error type? Decide in Phase 7.
