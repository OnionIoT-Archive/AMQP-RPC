import pika
import json
import uuid
import shortuuid
import threading 
import time

### Config ###
# load configuration file
with open("/etc/onionConfig.json") as f:
    config = json.load(f)["AMQP_RPC"]

_exchange = ''

### Initialization ###
credentials = pika.PlainCredentials( config['MQ_USER'], config['MQ_PASS'])
parameters = pika.ConnectionParameters(config['MQ_DOMAIN'], config['MQ_PORT'], config['MQ_VPATH'], credentials)
_connection = None
#_connection = pika.BlockingConnection(parameters)
#_channel = _connection.channel()
#_queue = shortuuid.uuid(name="onion.io")
#_queue = _channel.queue_declare(auto_delete=True).method.queue
#_channel.exchange_declare(exchange=_exchange, type='topic')

_stoped = False

_callbacks = {}
_callResult = {}

def onCall(ch, meta, props, body):
    method = meta.routing_key
    body = json.loads(body)
    result = _callbacks[method](body['params'])
    if body['replyTo'] != None:
        result = json.dumps(result)
        ch.basic_publish(exchange=_exchange, routing_key=body['replyTo'], body=result)

_connection = pika.BlockingConnection(parameters)
def _listenerThread(method):
    #connection = pika.BlockingConnection(parameters)
    channel = _connection.channel()
    queue = channel.queue_declare(queue=method, auto_delete=True).method.queue
    channel.basic_consume(onCall, queue=queue, no_ack=True)
    channel.start_consuming()

def register(fn):
    method = fn.__name__
    if fn!=None:
        _callbacks[method] = fn
    t = threading.Thread(target=_listenerThread, args=(method,))
    t.daemon = True
    t.start()
    print "listener %s started"%method


def onReturn(ch, meta, props, body):
    ch.close()
    body = json.loads(body)
    replyQueue = meta.routing_key
    _callResult[replyQueue] = body


def call(method, params, noReturn = False):
    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    if noReturn:
        replyQueue = None
    else:
        replyQueue = channel.queue_declare(auto_delete=True).method.queue
        _callResult[replyQueue] = 'PENDING'
    payload = {
        'replyTo': replyQueue,
        'params': params
    }
    payload = json.dumps(payload)
    channel.basic_publish(exchange=_exchange, routing_key=method, body=payload)

    if noReturn:
        return
    else:
        channel.basic_consume(onReturn, queue=replyQueue, no_ack=True)
        timeout = 3
        now = time.time()
        while _callResult[replyQueue] == 'PENDING':
            if int(time.time()-now) > timeout:
                print 'Timeout'
                return
            connection.process_data_events()
        connection.close()
        result = _callResult[replyQueue]
        del _callResult[replyQueue]
        return result

def loop():
    while True:
        time.sleep(1)


def stop():
    _stoped = True


