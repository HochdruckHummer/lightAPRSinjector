#!/bin/sh
set -e
# Volumes created by older (root) versions are owned by root: hand them to the app user,
# then drop privileges.
if [ "$(id -u)" = "0" ]; then
  chown -R app:app /data
  exec setpriv --reuid=app --regid=app --init-groups "$@"
fi
exec "$@"
