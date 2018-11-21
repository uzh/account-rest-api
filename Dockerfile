FROM python:3.6.7-slim

# prepare the image:
# 1. move user `root`'s home to `/home` where we shall mount
#    the corresponding host directories where user data resides
# 2. create mountpoints for volumes
RUN : \
    && mkdir -p /home /home/.acpy \
    && sed -re '1s|:/root:|:/home:|' -i /etc/passwd \
;
VOLUME /home/.acpy

# copy our source
COPY ./ /home

# install our package
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

# deploy adapter script (needs to be done last, otherwise it fails when running Python commands above)
COPY ./etc/docker/sitecustomize.py /usr/local/lib/python3/site-packages/sitecustomize.py

# run this command by default
ENTRYPOINT ["python", "-m", "acpy"]
CMD ["--help"]

# open ports
EXPOSE 5000