var rpc = require('../system/js/amqp_rpc');

var log = function(msg){
    process.stdout.write("test::amqp_rpc.js: ");
    console.log (msg);
}


rpc.register('ADD', function(params){
    return params.a + params.b
});


