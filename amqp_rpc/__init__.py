import pika
import json
import uuid
import shortuuid
from threading import Thread
import time

### Config ###
_mqUrl = 'amqp://onionCore:p@test.onion.io:5672/%2F'
_exchange = ''

### Initialization ###
parameters = pika.URLParameters(_mqUrl)
_connection = pika.BlockingConnection(parameters)
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
    result = json.dumps(result)
    ch.basic_publish(exchange=_exchange, routing_key=body['replyTo'], body=result)

def register(fn):
    method = fn.__name__
    if fn!=None:
        _callbacks[method] = fn
    channel = _connection.channel()
    queue = channel.queue_declare(queue=method, auto_delete=True).method.queue
    channel.basic_consume(onCall, queue=queue, no_ack=True)

def onReturn(ch, meta, props, body):
    ch.close()
    body = json.loads(body)
    replyQueue = meta.routing_key
    _callResult[replyQueue] = body


def call(method, params):
    channel = _connection.channel()
    replyQueue = channel.queue_declare(auto_delete=True).method.queue
    _callResult[replyQueue] = None
    payload = {
        'replyTo': replyQueue,
        'params': params
    }
    payload = json.dumps(payload)
    channel.basic_publish(exchange=_exchange, routing_key=method, body=payload)
    channel.basic_consume(onReturn, queue=replyQueue, no_ack=True)
    timeout = 3
    now = time.time()
    while _callResult[replyQueue] == None:
        if int(time.time()-now) > timeout:
            print 'Timeout'
            break
        _connection.process_data_events()
    result = _callResult[replyQueue]
    del _callResult[replyQueue]
    return result


def _startConsume():
    while not _stoped:
        _connection.process_data_events()
    _connection.close()

def start():
    thread = Thread(target = _startConsume)

def stop():
    _stoped = True


class MQ:
    def __init__(self, host, vhost, exchange, user, passwd):
        self.exchange = exchange;

        credentials = pika.PlainCredentials(user, passwd)
        parameters = pika.ConnectionParameters(credentials=credentials, host=host, virtual_host=vhost)
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(exclusive=True)
        self.queue = result.method.queue

        self.callbacks = {}


    def on(self, event, callback=None):
        if callback!=None:
            self.callbacks[event] = callback
        self.channel.queue_bind(exchange=self.exchange, queue=self.queue, routing_key=event) 

    def start(self):
        self.channel.basic_consume(self.onResponse, queue=self.queue, no_ack=True)
        self.channel.start_consuming()

    def close(self):
        self.connection.close()

    def onResponse(self, ch, method, props, body):
        print props
        print ch
        print method
        try:
            data = json.loads(body)
        except:
            data = body

        try:
            self.callbacks[method.routing_key](data)
        except Exception as  e:
            print 'Error: %s'%e.strerror 

    def send(self, routing_key, body):
        self.channel.basic_publish(exchange=self.exchange, routing_key=routing_key, body=json.dumps(body))



class ESB(MQ):
    def __init__(self):
        MQ.__init__(self,"localhost", "/", "onion.core", "onionCore", "philosophy")
        self.channel.exchange_declare(exchange=self.exchange, type='topic')

    def sendEvent(self, event, data):
        self.send(event,data)

    def onResponse(self, ch, method, props, body):
        data = json.loads(body)
        # rpc with return
        if data['id']!=None:
            MQ.onResponse(self, ch, method, props, body)
        else:
            # rpc response
            if 'result' in data: 
                self.response = data['result']
            # rpc without return
            else:
                MQ.onResponse(self, ch, method, props, body)

    def call(self, event, data, hasResponse=True):
        if hasResponse:
            corrId = self.queue
        else:
            corrId = None
        payload= {
                    'method': event,
                    'id': corrId,
                    'params': data
                }

        if hasResponse:
            self.on(self.queue)
            self.response = None
            self.channel.basic_consume(self.onResponse, queue=self.queue, no_ack=True)
            self.send(event, payload)
            print "waiting for response"
            while self.response is None:
                self.connection.process_data_events()
            return self.response
        else:
            self.send(event, payload)


    def reply(self, request, response, error=None):
        replyTo = request['id'] 
        response['error'] = error
        payload = {
                "result":response,
                "id": None
                }
        self.send(replyTo,payload)


class MQTT(MQ):
    def __init__(self):
        MQ.__init__(self,"localhost", "/device/", "onion.device", "onionCore", "philosophy")

    def sendCmd(self, device, cmd):
        self.channel.basic_publish(exchange=self.exchange, routing_key=device, body=cmd)

