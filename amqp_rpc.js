var uuid = require('node-uuid');
var amqp = require('amqplib');

var log = function(msg){
    process.stdout.write("onion::amqp_rpc: ");
    console.log (msg);
}

exports.call = function (method, params, callback){
    var replyQueue = 'rpc-'+uuid.v4();

    var payload = {
        replyTo: replyQueue,
        params: params
    }

    var open = amqp.connect('amqp://onionCore:p@zh.onion.io');
    open.then(function(conn) {
        return conn.createChannel().then(function(ch) {
            var options = {durable: false, noAck: true, autoDelete: true};
            ch.assertQueue(replyQueue, options);
            ch.consume(replyQueue, function(msg) {
                if (msg !== null) {
                    conn.close();
                    callback(msg.content.toString());
                }
            });
            ch.sendToQueue(method, new Buffer(JSON.stringify(payload)));
        });
    });
}

exports.register = function (method, callback){
    var open = amqp.connect('amqp://onionCore:p@localhost');
    open.then(function(conn) {
        return conn.createChannel().then(function(ch) {
            var options = {durable: false, noAck: true, autoDelete: true};
            ch.assertQueue(method, options);
            ch.consume(method, function(msg) {
                if (msg !== null) {
                    var data = JSON.parse(msg.content.toString());
                    var result = callback(data.params);
                    ch.sendToQueue(data.replyTo, new Buffer(JSON.stringify(result)));
                }
            });
        });
    });
}
