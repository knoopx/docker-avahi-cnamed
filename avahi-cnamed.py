#! /usr/bin/env python

import time
import threading
import docker
import avahi
import dbus

from encodings.idna import ToASCII

TTL = dbus.UInt32(60)
CLASS_IN = dbus.UInt16(0x01)
TYPE_CNAME = dbus.UInt16(0x05)


class Publisher(object):
    cnames = set()

    def run(self, ttl=50):
        while True:
            time.sleep(ttl)
            publisher.publish_all()

    def publish_all(self):
        for cname in self.cnames:
            print("Publishing " + cname)
            self.publish_cname(cname)

    def publish_cname(self, cname):
        bus = dbus.SystemBus()
        server = dbus.Interface(bus.get_object(avahi.DBUS_NAME, avahi.DBUS_PATH_SERVER),
                                avahi.DBUS_INTERFACE_SERVER)
        group = dbus.Interface(bus.get_object(avahi.DBUS_NAME, server.EntryGroupNew()),
                               avahi.DBUS_INTERFACE_ENTRY_GROUP)

        if not u'.' in cname:
            cname = cname + '.local'
        cname = self.encode_cname(cname)
        rdata = self.encode_rdata(server.GetHostNameFqdn())
        rdata = avahi.string_to_byte_array(rdata)

        group.AddRecord(avahi.IF_UNSPEC, avahi.PROTO_UNSPEC, dbus.UInt32(0),
                        cname, CLASS_IN, TYPE_CNAME, TTL, rdata)
        group.Commit()

    def encode_cname(self, name):
        return '.'.join(ToASCII(p) for p in name.split('.') if p)

    def encode_rdata(self, name):
        def enc(part):
            a = ToASCII(part)
            return chr(len(a)), a
        return ''.join('%s%s' % enc(p) for p in name.split('.') if p) + '\0'


if __name__ == '__main__':
    publisher = Publisher()
    client = docker.DockerClient()

    try:
        thread = threading.Thread(target=publisher.run)
        thread.start()

        for event in client.events(filters={"event": ["start", "stop"]}, decode=True):
            container_id = event["Actor"]["ID"]
            name = event["Actor"]["Attributes"]["name"]
            hostname = name + ".local"
            if event["Action"] == "start":
                publisher.cnames.add(hostname)
            if event["Action"] == "stop":
                publisher.cnames.remove(hostname)

    except KeyboardInterrupt:
        pass
