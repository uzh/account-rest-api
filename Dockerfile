FROM python:3.6.7-slim

RUN : \
    && mkdir -p /home /home/.acpy \
    && sed -re '1s|:/root:|:/home:|' -i /etc/passwd \
;
VOLUME /home/.acpy

COPY ./ /home

WORKDIR /home
RUN : \
    && apt-get update \
    && apt-get install --yes --no-install-recommends \
           ca-certificates \
           curl \
           g++ \
           gcc \
           libc6 libc6-dev \
           libffi6 libffi-dev \
           libldap2-dev \
           libsasl2-dev \
           make \
    && pip install -e . \
    && rm -rf /home/.cache \
    && apt-get remove --purge -y \
           make \
           g++ \
           gcc \
           libc6-dev \
           libffi-dev \
           libldap2-dev \
           libsasl2-dev \
    && apt-get autoremove --yes \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /var/cache/apt/* \
    && rm -rf /var/cache/debconf/*.dat-old \
    ;

COPY ./etc/docker/sitecustomize.py /usr/local/lib/python3/site-packages/sitecustomize.py

ENTRYPOINT ["python", "-m", "acpy"]
CMD ["--help"]

EXPOSE 8080