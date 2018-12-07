.. Hey, Emacs this is -*- rst -*-

   This file follows reStructuredText markup syntax; see
   http://docutils.sf.net/rst.html for more information.

.. recommendation:

.. _NGINX: https://nginx.org/

===================================================
We recommend the following production configuration
===================================================

1. NGINX reverse proxy with SSL (no plain HTTP due to login mechanism).
2. systemd service for managing our service.

NGINX
=====

Make sure NGINX_ is installed on your system.

Get a Certificate
*****************

You will need to purchase or create an SSL certificate. These commands are for a self-signed certificate, but you should get an officially signed certificate if you want to avoid browser warnings.

Move into the proper directory and generate a certificate:

 cd /etc/nginx
 sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 -keyout /etc/nginx/cert.key -out /etc/nginx/cert.crt

You will be prompted to enter some information about the certificate. You can fill this out however you'd like; just be aware the information will be visible in the certificate properties. We've set the number of bits to 2048 since that's the minimum needed to get it signed by a CA. If you want to get the certificate signed, you will need to create a CSR.
Edit the Configuration

Next you will need to edit the default Nginx configuration file.

 sudo nano /etc/nginx/sites-enabled/default

Here is what the final config might look like; the sections are broken down and briefly explained below. You can update or replace the existing config file, although you may want to make a quick copy first.

.. code-block::

 server {
    listen 80;
    return 301 https://$host$request_uri;
 }

.. code-block::

 server {
    listen 443;
    server_name accounting.domain.com;

    ssl_certificate           /etc/nginx/cert.crt;
    ssl_certificate_key       /etc/nginx/cert.key;

    ssl on;
    ssl_session_cache  builtin:1000  shared:SSL:10m;
    ssl_protocols  TLSv1 TLSv1.1 TLSv1.2;
    ssl_ciphers HIGH:!aNULL:!eNULL:!EXPORT:!CAMELLIA:!DES:!MD5:!PSK:!RC4;
    ssl_prefer_server_ciphers on;

    access_log            /var/log/nginx/accounting.access.log;

    location / {
      proxy_set_header        Host $host;
      proxy_set_header        X-Real-IP $remote_addr;
      proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header        X-Forwarded-Proto $scheme;

      # Fix the “It appears that your reverse proxy set up is broken" error.
      proxy_pass          http://localhost:8080;
      proxy_read_timeout  90;
      proxy_redirect      http://localhost:8080 https://accounting.domain.com;
    }
  }

In our configuration, the cert.crt and cert.key settings reflect the location where we created our SSL certificate. You will need to update the servername and `proxyredirect` lines with your own domain name. There is some additional Nginx magic going on as well that tells requests to be read by Nginx and rewritten on the response side to ensure the reverse proxy is working.

The first section tells the Nginx server to listen to any requests that come in on port 80 (default HTTP) and redirect them to HTTPS.

.. code-block::

 ...
 server {
   listen 80;
   return 301 https://$host$request_uri;
 }
 ...


Next we have the SSL settings. This is a good set of defaults but can definitely be expanded on. For more explanation, please read this tutorial.

.. code-block::

  ...
  listen 443;
  server_name accounting.domain.com;

  ssl_certificate           /etc/nginx/cert.crt;
  ssl_certificate_key       /etc/nginx/cert.key;

  ssl on;
  ssl_session_cache  builtin:1000  shared:SSL:10m;
  ssl_protocols  TLSv1.2;
  ssl_ciphers HIGH:!aNULL:!eNULL:!EXPORT:!CAMELLIA:!DES:!MD5:!PSK:!RC4;
  ssl_prefer_server_ciphers on;
  ...

The final section is where the proxying happens. It basically takes any incoming requests and proxies them to the instance that is bound/listening to port 8080 on the local network interface. This is a slightly different situation, but this tutorial has some good information about the Nginx proxy settings.

.. code-block::

  ...
  location / {
    proxy_set_header        Host $host;
    proxy_set_header        X-Real-IP $remote_addr;
    proxy_set_header        X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header        X-Forwarded-Proto $scheme;

    # Fix the “It appears that your reverse proxy set up is broken" error.
    proxy_pass          http://localhost:8080;
    proxy_read_timeout  90;
    proxy_redirect      http://localhost:8080 https://accounting.domain.com;
  }
  ...

systemd
=======
If you've installed acpy in system space, you should be able to create the file ``/etc/systemd/system/acpy.service`` with the following contents:

.. code-block::

  [Unit]
  Description=ACPY Service
  After=nginx.target

  [Service]
  Type=forking
  ExecStart=acpy start -g
  ExecStop=acpy stop

  [Install]
  WantedBy=multi-user.target

In order to start the service, first run ``systemctl daemon-reload``.
Now test if ``systemctl start acpy`` works, if so you can enable it ``systemctl enable acpy``.
