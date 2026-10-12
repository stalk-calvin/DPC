# Django Product Catalog

A Django web application for browsing products. The main page lets you search products by description and filter them by category and tags, in any combination.

The application logic relies on Django's built-in features rather than custom plumbing:

- **ORM and migrations**: models, relationships and database constraints
- **QuerySet API**: all search and filter logic, in a custom QuerySet
- **Forms**: validation of the search and filter input
- **Generic `ListView`**: the product page, with built-in pagination
- **Templates**: server-rendered HTML with automatic escaping
- **Admin site**: data entry for categories, tags and products
- **Management commands**: `seed_catalog` loads the sample data
- **Test framework**: automated tests for models, queries, forms, views and admin

It runs on Django 5.2 (LTS), with SQLite locally and PostgreSQL under Docker. The extra packages (gunicorn, WhiteNoise, psycopg) are only used to run it under Docker.

## Requirements

Python 3.10 or newer for a local run, or Docker.

## Run with Docker

```bash
docker compose up --build
```

- App: <http://localhost:8000>
- Admin: <http://localhost:8000/admin> (Username: `admin` / Password: `admin`)

On startup the container migrates the database, loads the sample data and creates the admin user. Stop it with `docker compose down`; add `-v` to also wipe the database.

## Run locally (without Docker)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # once per database
python manage.py seed_catalog      # optional: sample data
python manage.py runserver
```

Open <http://localhost:8000> and log in to `/admin` with the user you created. Local runs store data in a SQLite file (`db.sqlite3`), so no database server or configuration is needed.

- If `createsuperuser` says the name is taken, the user already exists. Reset its password with `python manage.py changepassword <name>`.
- Docker and `runserver` both use port 8000. Stop Docker first, or run `python manage.py runserver 8001`.

## Populate data

Enter data through the Django admin at `/admin`: categories first, then tags, then products. Each product picks one category and any number of tags.

For a ready-made set (5 categories, 10 tags, 20 products), run `python manage.py seed_catalog`. It is safe to re-run: it never duplicates rows or overwrites edits made in the admin. Docker runs it on startup.

## Searching and filtering

| Field | Effect |
|---|---|
| Description contains | Case-insensitive text search in the product description |
| Category | Only products in the chosen category |
| Tags | Products with the ticked tags (see next row) |
| Show products with | *At least one selected tag* (default) or *Every selected tag* |

All filters combine: a product must match every filter you fill in. Results show 5 per page.

## Tests

```bash
python manage.py test
```

The Docker image build runs the same tests and stops if any fail.

## Logging

Warnings, errors and failed requests (4xx/5xx) are always printed to the console (`docker compose logs web` under Docker). With `DEBUG` on (local runs), admin changes are printed too. For more detail:

```bash
DJANGO_ACCESS_LOG=1 python manage.py runserver      # every request, including CSS/JS files
DJANGO_LOG_LEVEL=DEBUG python manage.py runserver   # each search: filters, result count, page
DJANGO_LOG_SQL=1 python manage.py runserver         # every SQL query (only when DEBUG is on)
```

`DJANGO_LOG_LEVEL` accepts `DEBUG`, `INFO` (default) or `WARNING`. Under Docker, set these in the `web` service's `environment` in `docker-compose.yml`. SQL logging only works locally, because Docker runs with `DEBUG` off.

## Project layout

```
config/              settings, URLs, WSGI entry point
catalog/
  models.py          Category, Tag, Product and all query logic
  forms.py           validates the search and filter input
  views.py           the product page
  admin.py           admin screens and admin logging
  templates/         product_list.html
  static/            styles.css
  management/        seed_catalog command
  tests/             automated tests
gunicorn.conf.py     gunicorn settings for Docker
```

## Notes

- Search looks at the **description** only, as required. It ignores case.
- The category filter takes one category at a time.
- The *Every selected tag* option and pagination are additions beyond the requirements.
- Every product belongs to exactly one category; tags are optional.
- Category and tag names have surrounding spaces removed and must be unique, ignoring case (`Books`, `books` and ` BOOKS ` count as the same name).
- Product names are unique within a category. Prices can't be negative.
- A category that still has products can't be deleted.
- The front end is plain Django templates with minimal CSS, so there is no front-end build step.
- The credentials in `docker-compose.yml` are for local use only.

## AI usage

**Tools used.** GitHub Copilot (chat and agent mode in VS Code) throughout this project.

**How it was used.** Copilot generated the first version of the project from the assignment brief at my request: the models and database constraints, the custom QuerySet (search, category and tag filtering), the filter form, the view, template and CSS, the admin configuration, the `seed_catalog` command and its sample data, the tests.

**Changes I directed afterwards.** I ran the app locally and in Docker, reported problems I found, and asked Copilot to change the code where something was wrong or I wanted it different:

- Removed boilerplate and files I didn't need (`apps.py`, `asgi.py`, `pyproject.toml`, dev tooling, timestamp fields), flattened the `templates/` and `static/` folders, and added `.gitignore`.
- Fixed the stylesheet not being applie by flattening static files (simplified).
- Containerized the app (`Dockerfile`, plus `docker-compose.yml` with PostgreSQL) so it installs and runs with one command. The Dockerfile is a multi-stage build (dependencies, tests, static files, final image), so the image only builds if the tests pass, and `pip` is removed from the final image.
- Fixed the admin hanging on Login/Save (gunicorn now uses threaded workers) and clarified the admin login error.
- Added logging (rejected filters, failed logins, admin changes, search details), with environment variables for the log level, SQL logging and the request log (`gunicorn.conf.py`).
- Renamed unclear variables, applied consistent formatting, and added comments explaining the key decisions.

**Learning.** I used Copilot to explain the parts of the Django ecosystem that were new to me: the ORM and migrations, QuerySets and N+1 queries, forms and validation, class-based views and pagination, the admin and permissions, static files and WhiteNoise, gunicorn, `SECRET_KEY` and signing, and logging.

