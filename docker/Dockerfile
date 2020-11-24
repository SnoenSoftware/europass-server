from python:3.8-slim-buster

WORKDIR /app
ENV PIPENV_VENV_IN_PROJECT=1 FLASK_APP="server.py"

COPY ./docker/install-deps.sh install-deps.sh
RUN sh install-deps.sh

COPY Pipfile Pipfile.lock /app/

RUN pipenv install

COPY ./server.py ./reader.py /app/
COPY ./static /app/static
COPY ./templates /app/templates

RUN chown -R www-data:www-data /app

USER www-data
CMD ["pipenv", "run", "flask", "run", "--port", "5000", "--host", "0.0.0.0"]