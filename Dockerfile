FROM python:3.7.0-slim

RUN set -ex \
    && buildDeps=' \
        gcc \
        libbz2-dev \
        libc6-dev \
        libgdbm-dev \
        liblzma-dev \
        libncurses-dev \
        libreadline-dev \
        libsqlite3-dev \
        libssl-dev \
        libpcre3-dev \
        make \
        tcl-dev \
        tk-dev \
        wget \
        xz-utils \
        zlib1g-dev \
    ' \
    && deps=' \
        libexpat1 \
    ' \
    && apt-get update && apt-get install -y $buildDeps $deps --no-install-recommends  && rm -rf /var/lib/apt/lists/* \
    && pip install uwsgi \
    && apt-get purge -y --auto-remove $buildDeps \
    && find /usr/local -depth \
    \( \
        \( -type d -a -name test -o -name tests \) \
        -o \
        \( -type f -a -name '*.pyc' -o -name '*.pyo' \) \
    \) -exec rm -rf '{}' +

RUN pip3 install --no-cache-dir pipenv

RUN mkdir /app
WORKDIR /app

COPY Pipfile Pipfile
COPY Pipfile.lock Pipfile.lock

RUN pipenv install --deploy --system

COPY . /app

CMD bash -C 'start.sh'

EXPOSE 5000