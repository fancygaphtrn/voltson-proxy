## voltson-proxy

Control [Etekcity Voltson] smart plugs via your local mqtt server rather than Etekcity's cloud.  Keeps all data local.

### Getting started

* I installed in a python virtualenv using Python 3.6.5
* Uses [paho.mqtt](https://pypi.org/project/paho-mqtt/#client)
* Uses [python-websocket-server](https://github.com/Pithikos/python-websocket-server)
* You need to redirect server2.vesync.com to the computer running
  voltlet. With dnsmasq you add a config line like this  "list address '/server2.vesync.com/192.168.1.10'".  Replace 192.168.1.10 with your server IP address
* Restart your plugs so that they connect to the local server.

#### MQTT

* Send "true" to turn on the plug to `/voltson/{plug-uuid}`
* Send "false" to turn off the plug to `/voltson/{plug-uuid}`
* Plugs send "true" or "false" to `/voltson/{plug-uuid}/state` once they've actually changed state. Messages are retained.
* Plugs send "online" or "offline" to `/voltson/{plug-uuid}/availability` depending on whether they are connected. Messages are not retained.
* Plugs send json {"instantpower": 9.098388671875, "avgpower": 9.094970703125, "instantvoltage": 121.09814453125, "avgvoltage": 120.196044921875} to `/voltson/{plug-uuid}/energy` Messages are not retained.
#### Home Assistant Example

```
switch:
  - platform: mqtt
    command_topic: "/voltson/UUID-GOES-HERE"
    state_topic: "/voltson/UUID-GOES-HERE/state"
    availability_topic: "/voltson/UUID-GOES-HERE/available"
    retain: true
    payload_on: 'true'
    payload_off: 'false'
```

```
sensor:
  - platform: mqtt
    name: "Spare Vesync switch power"
    state_topic: "voltson/UUID-GOES-HERE/energy"
    unit_of_measurement: "W"
    value_template: '{{ value_json.instantpower|int }}'
  - platform: mqtt
    name: "Spare Vesync switch voltage"
    state_topic: "voltson/UUID-GOES-HERE/energy"
    unit_of_measurement: "V"
    value_template: '{{ value_json.instantvoltage|int }}'

```

### References

* [voltlet](https://github.com/mcolyer/voltlet) the inspiration. Wrote in python because I wanted to learn the language.
* [vesync-wsproxy](https://github.com/itsnotlupus/vesync-wsproxy) this project just proxies the connect to the cloud server to spy on what happens. I'd rather keep my data local.
* This [project](https://github.com/travissinnott/outlet) attempted to do something similar but wasn't fully implemented. That said it has great notes about the line protocol


[Etekcity Voltson]: https://www.amazon.com/gp/product/B06XSTJST6/ref=as_li_tl?ie=UTF8&camp=1789&creative=9325&creativeASIN=B06XSTJST6&linkCode=as2&tag=matcol01-20&linkId=ab8750e61f7f9723ddaa60cb56d0df82
