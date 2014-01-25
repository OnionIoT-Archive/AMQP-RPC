'use strict';

var uuid = require('node-uuid');
var amqp = require('amqplib');



var log = function(msg){
    process.stdout.write("onion::amqp_rpc: ");
    console.log (msg);
}



var mqServerUrl = 'amqp://onionCore:p@test.onion.io';
var conn = null;
var open = amqp.connect(mqServerUrl);
open.then(function(connection) {
    log('mq connection opened');
    conn = connection;
});

exports.call = function (method, params, callback){
    var replyQueue = 'rpc-'+uuid.v4();

    var payload = {
        replyTo: replyQueue,
        params: params
    }

    open.then(function(conn) {
        conn.createChannel().then(function(ch) {
            var timeOutId = setTimeout(function(){
                ch.close();
                log('time out');
            },10000);

            var options = {durable: false, noAck: false, autoDelete: true};
            ch.assertQueue(replyQueue, options);
            ch.consume(replyQueue, function(msg) {
                if (msg !== null) {
                    ch.ack(msg);
                    ch.close();
                    clearTimeout(timeOutId);
                    callback(JSON.parse(msg.content.toString()));
                }
            });
            ch.sendToQueue(method, new Buffer(JSON.stringify(payload)));
        });
    });
}

var connectionTable = {};

exports.register = function (method, callback){
    open.then(function(conn) {
        return conn.createChannel().then(function(ch) {
            var options = {durable: false, noAck: false, autoDelete: true};
            ch.assertQueue(method, options);
            connectionTable[method] = ch;
            ch.consume(method, function(msg) {
                if (msg !== null) {
                    ch.ack(msg);
                    var data = JSON.parse(msg.content.toString());
                    callback(data.params, function(result){
                        ch.sendToQueue(data.replyTo, new Buffer(JSON.stringify(result)));
                    });
                }
            });
        });
    });
}

exports.unregister = function (method){
    connectionTable[method].close();
    connectionTable[method] = null;
}
