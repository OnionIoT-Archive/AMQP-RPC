import pika
import json
import uuid

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

