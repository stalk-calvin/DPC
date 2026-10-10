FROM python:3.13-slim AS base
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt && pip uninstall -y pip
COPY . .

FROM base AS test
RUN python manage.py test && touch /tests-passed

FROM base AS build
RUN DJANGO_DEBUG=0 DJANGO_SECRET_KEY=build python manage.py collectstatic --noinput

FROM base AS app

ENV DJANGO_DEBUG=0

COPY --from=test /tests-passed /tmp/tests-passed
COPY --from=build /app/staticfiles ./staticfiles

RUN useradd --create-home --uid 10001 app
USER app

CMD ["gunicorn", "config.wsgi"]
