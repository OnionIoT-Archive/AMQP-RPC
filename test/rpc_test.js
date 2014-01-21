var rpc = require('../system/js/amqp_rpc');

var log = function(msg){
    process.stdout.write("test::amqp_rpc.js: ");
    console.log (msg);
}


//rpc.register('ADD', function(params){
//    return params.a + params.b
//});

rpc.call('ADD',{a:1,b:2}, function(result){
    log('1+2='+result);
});

rpc.call('ADD',{a:9,b:1}, function(result){
    log('9+1='+result);
});
