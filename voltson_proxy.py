#!/srv/voltson-proxy/bin/python3
import datetime, threading, time
import logging
import json
import paho.mqtt.client as mqtt
from websocket_server import WebsocketServer

log = logging.getLogger()
log.setLevel(logging.INFO)
#if (log.hasHandlers()):
#    log.handlers.clear()

formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
log.addHandler(ch)

log.info('Starting')

MQTTHOST = "home.lan"
MQTTPORT = 1883
WSHOST = "0.0.0.0"
WSPORT = 17273

# The callback for when the client receives a CONNACK response from the server.
def mqtt_on_connect(client, userdata, flags, rc):
    log.info("MQTT Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("voltson/+/set")
    log.info("MQTT Subscribed to voltson/+/set")

def mqtt_on_disconnect(client, userdata, rc):
    log.info("MQTT Disconnected with result code "+str(rc))

def mqtt_on_log(client, userdata, level, buf):
    log.info("MQTT "+buf)


# The callback for when a PUBLISH message is received from the server.
def mqtt_on_message(client, userdata, msg):
    log.info(msg.topic+" "+str(msg.payload))
    t = msg.topic.split('/')
    found = False
    for x in server.clients:
        if 'info' in x:
            if 'id' in x['info']:
                if x['info']['id'] == t[1]:
                    if msg.payload == "true".encode():
                        r = {"uri": "/relay", "action": "open"}
                        server.send_message(x, json.dumps(r))
                        log.info("Sending Client(%d): %s %s" % (x['id'], x['info']['id'],json.dumps(r)))
                    else:
                        r = {"uri": "/relay", "action": "break"}
                        server.send_message(x, json.dumps(r))
                        log.info("Sending Client(%d): %s %s" % (x['id'], x['info']['id'],json.dumps(r)))
                    found = True
    if found == False:
        mqtt_server.publish("voltson/" + t[1] + "/available", "offline", qos=0, retain=False)
        log.info("MQTT %s offline", t[1])

        for x in server.clients:
            if 'info' in x:
                if 'id' in x['info']:
                    if x['id'] != client['id']:
                        mqtt_server.publish("voltson/" + x['info']['id'] + "/available", "online", qos=0, retain=False)
                        log.info("MQTT %s online",x['info']['id'])



# Called for every client connecting (after handshake)
def ws_new_client(client, server):
    log.info("New client connected id %d" % client['id'])

# Called for every client disconnecting
def ws_client_left(client, server):
    mqtt_server.publish("voltson/" + client['info']['id'] + "/available", "offline", qos=0, retain=False)
    log.info("MQTT %s offline",client['info']['id'])
    log.info("Client(%d) disconnected" % client['id'])

    for x in server.clients:
        if 'info' in x:
            if 'id' in x['info']:
                if x['id'] != client['id']:
                    mqtt_server.publish("voltson/" + x['info']['id'] + "/available", "online", qos=0, retain=False)
                    log.info("MQTT %s online",x['info']['id'])



# Called when a client sends a message
def ws_message_received(client, server, message):
    
    log.info("Received Client(%d): %s" % (client['id'], message))

    now = datetime.datetime.now()

    m = json.loads(message)
    if 'id' in m:
        # login message
        # {"account":"fancygaphtrn@gmail.com","id":"117de316-72c6-4b42-af2b-3f0f7d1915b7","deviceName":"vesync_wifi_outlet","deviceVersion":"1.5","deviceVersionCode":5,"type":"wifi-switch","apptype":"switch-measure","firmName":"cosytek_firm_a","firmVersion":"1.89","firmVersionCode":89,"key":0,"relay":"open"

        # login response
        # {"uri":"/loginReply","error":0,"wd":3,"year":2017,"month":11,"day":1,"ms":62125134,"hh":0,"hl":0,"lh":0,"ll":0}

        client['info'] = m

        r = {"uri": "/loginReply", "error":0, "wd":3, "year": 2017, "month":11, "day":1, "ms":62125134, "hh":0, "hl":0, "lh":0, "ll":0}

        server.send_message(client, json.dumps(r))
        log.info("Sending Client(%d): %s" % (client['id'], json.dumps(r)))

        mqtt_server.publish("voltson/" + client['info']['id'] + "/available", "online", qos=0, retain=False)
        log.info("MQTT %s online",client['info']['id'])

        if m['relay'] == "open":
            mqtt_server.publish("voltson/" + client['info']['id'] + "/state", "true", qos=0, retain=True)
        else:
            mqtt_server.publish("voltson/" + client['info']['id'] + "/state", "false", qos=0, retain=True)

    if 'uri' in m:
        if m['uri'] == "/state":
            client['info']['relay'] = m['relay']
            if m['relay'] == "open":
                mqtt_server.publish("voltson/" + client['info']['id'] + "/state", "true", qos=0, retain=True)
            else:
                mqtt_server.publish("voltson/" + client['info']['id'] + "/state", "false", qos=0, retain=True)

        if m['uri'] == "/runtimeInfo":

            mqtt_server.publish("voltson/" + client['info']['id'] + "/available", "online", qos=0, retain=False)
            log.info("MQTT %s online",client['info']['id'])

            client['info']['relay'] = m['relay']
            if m['relay'] == "open":
                mqtt_server.publish("voltson/" + client['info']['id'] + "/state", "true", qos=0, retain=True)
            else:
                mqtt_server.publish("voltson/" + client['info']['id'] + "/state", "false", qos=0, retain=True)
                
            p = m['power'].split(':')
            v = m['voltage'].split(':')

            publish = True
            r = {}
            #Get massive spikes sometimes.   Switch is rated at 8A at 120v so using 1000 for power and 130 for voltage
            r["instantpower"]   = int(p[0],16)/4096
            if r["instantpower"] >= 1000:
                r["instantpower"] = 1000
                publish = False
                
            r["avgpower"]       = int(p[1],16)/4096
            if r["avgpower"] >= 1000:
                r["avgpower"] = 1000
                publish = False

            r["instantvoltage"] = int(v[0],16)/4096
            if r["instantvoltage"] >= 130:
                r["instantvoltage"] = 130
                publish = False

            r["avgvoltage"]     = int(v[1],16)/4096
            if r["avgvoltage"] >= 130:
                r["avgvoltage"] = 130
                publish = False

            if publish:
                mqtt_server.publish("voltson/" + client['info']['id'] + "/energy", json.dumps(r), qos=0, retain=False)

        # server message send via heartbeat {"uri":"/kr","error":0,"wd":3,"year":2017,"month":11,"day":1,"ms":62482912}
        if m['uri'] == "/ka":

            mqtt_server.publish("voltson/" + client['info']['id'] + "/available", "online", qos=0, retain=False)
            log.info("MQTT %s online",client['info']['id'])

            client['info']['rssi'] = m['rssi']
            r = {"uri":"/kr","error":0,"wd":3,"year":2017,"month":11,"day":1,"ms":62482912}
            server.send_message(client, json.dumps(r))
            log.info("Sending Client(%d): %s" % (client['id'], json.dumps(r)))

        if m['uri'] == "/kr":

            mqtt_server.publish("voltson/" + client['info']['id'] + "/available", "online", qos=0, retain=False)
            log.info("MQTT %s online",client['info']['id'])

        if m['uri'] == "/report":
            client['info']['e'] = m['e']
            client['info']['t'] = m['t']

            #p = str(round(int(m['e'], 16) / int(m['t'], 16),2))
            #mqtt_server.publish("voltson/" + client['info']['id'] + "/power", p , qos=0, retain=False)
            #log.info("MQTT %s power %s",client['info']['id'], p)


    #log.info("Info Client(%d): %s" % (client['id'], client['info']))

def heartbeat():
    while True:

        #r = {"uri":"/ka"}
        #server.send_message_to_all(json.dumps(r))
        #log.info("Sending ka Heartbeat to all clients")


        r = {"uri":"/getRuntime"}
        server.send_message_to_all(json.dumps(r))
        log.info("Sending getRuntime to all clients")

        #for x in server.clients:
        #    r = {"uri":"/ka"}
        #    server.send_message(x, json.dumps(r))
        #    log.info("Sending Heartbeat Client(%d): %s" % (x['id'],json.dumps(r)))

        time.sleep(30)


server = WebsocketServer(WSPORT, host=WSHOST)
server.set_fn_new_client(ws_new_client)
server.set_fn_client_left(ws_client_left)
server.set_fn_message_received(ws_message_received)

mqtt_server = mqtt.Client("",True)
mqtt_server.on_connect = mqtt_on_connect
mqtt_server.on_disconnect = mqtt_on_disconnect
mqtt_server.on_message = mqtt_on_message
mqtt_server.on_log = mqtt_on_log

mqtt_server.connect(MQTTHOST, MQTTPORT, 60)
mqtt_server.loop_start()

t = threading.Thread(target=heartbeat)
t.daemon = True
t.start()

try:
    log.info("Listening on port %d for clients.." % server.port)
    server.serve_forever()
except KeyboardInterrupt:
    server.server_close()
    mqtt_server.loop_stop()
    log.info("Server terminated.")
except Exception as e:
    log.error(str(e), exc_info=True)

log.info('Ending')
