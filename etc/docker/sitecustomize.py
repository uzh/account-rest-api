from os import environ, getuid, setuid, setgid, stat
from pwd import getpwuid


# read user and group ID of the configuration and storage directory
si = stat('/home/.acpy')
uid = si.st_uid
gid = si.st_gid

# ensure there is an /etc/passwd entry corresponding to this UID/GID
try:
    getpwuid(uid)
except KeyError:
    # create entry in /etc/passwd
    with open('/etc/passwd', 'a') as etc_passwd:
        etc_passwd.write(
            "{username}:x:{uid}:{gid}::/home:/bin/sh\n"
            .format(
                username=environ.get('USER', 'user'),
                uid=uid, gid=gid))

# set real and effective user ID so that we can read/write in there
if uid != getuid():
    setgid(gid)
setuid(uid)
