var rpc = require('../amqp_rpc');

var log = function(msg){
    process.stdout.write("test::amqp_rpc.js: ");
    console.log (msg);
}

var test = function (a, b){
    log((a===b)?'PASS':'FAIL');
}

rpc.register('ADD', function(params, callback){
    callback( params.a + params.b);
});

log('load test');
for (var i=0;i<100;i++){
    rpc.call('ADD',{a:i,b:1}, function(result){
        log(result);
        if (result == 100){
            log ('All Done');
            rpc.unregister('ADD');
        }
    });
}

setTimeout(function(){
    log('hang connection test:');
    rpc.call('ADD1',{a:i,b:1}, function(result){
        callback( params.a + params.b);
    });
},3000);



