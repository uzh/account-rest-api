FROM alpine:3.7

# install compiler tools
RUN apk add --update --no-cache alpine-sdk
RUN apk add --update --no-cache build-base

# install python3
RUN apk add --no-cache python3-dev && \
    python3 -m ensurepip && \
    rm -r /usr/lib/python*/ensurepip && \
    pip3 install --upgrade pip setuptools && \
    if [ ! -e /usr/bin/pip ]; then ln -s pip3 /usr/bin/pip ; fi && \
    if [[ ! -e /usr/bin/python ]]; then ln -sf /usr/bin/python3 /usr/bin/python; fi && \
    rm -r /root/.cache

# install dependencies
RUN apk add libffi-dev

# copy our source
COPY . .

# install our package
RUN pip install -e .

# start our server
RUN acpy start

# open ports
EXPOSE 5000