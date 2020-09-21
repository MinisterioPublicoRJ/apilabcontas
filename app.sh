#!/bin/bash

refresh_kinit() {
    KINIT_TIMEOUT=$([[ -z "$KINIT_TIMEOUT" ]] && echo 5184000 || echo $KINIT_TIMEOUT);
    echo "Refreshing kinit every $KINIT_TIMEOUT seconds";
    while true; do
        echo "Refresquei kinit";
        kinit mpmapas@BDA.LOCAL -kt /keys/mpmapas.keytab;
        sleep $KINIT_TIMEOUT;
    done
}

refresh_kinit &;
sleep 1;

gunicorn datalakecadg.wsgi:application --workers=12 --threads=2 --bind=0.0.0.0:8080 -t 180 --log-file -
