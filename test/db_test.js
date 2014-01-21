var rpc = require('../system/js/amqp_rpc');

var log = function(msg){
    process.stdout.write("test::db_test.js: ");
    console.log (msg);
}


rpc.call('DB_GET_USER',{user:'guest',pass:'guest'}, function(result){
    log(result);
});
