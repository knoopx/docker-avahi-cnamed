FROM alpine:3.6

RUN apk --no-cache add py2-pip py-avahi py-dbus
RUN pip install docker

COPY ./avahi-cnamed.py /usr/local/bin/avahi-cnamed

RUN chmod a+x /usr/local/bin/avahi-cnamed

ENTRYPOINT ["avahi-cnamed"]