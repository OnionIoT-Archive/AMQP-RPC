import amqp_rpc as rpc
import time



@rpc.register
def PY_TEST(params):
    return params['a'] + params['b']

@rpc.register
def PY_TEST2(params):
    return 'PY_TEST2: %s'%params


rpc.start()

print '##### Load Test #####'

for i in range(10):
    result = rpc.call('PY_TEST',{'a': i, 'b':i})
    print '%s + %s = %s'%(i,i,result)

print '##### DB Test #####'

print "DB_GET_USER:"
print rpc.call('DB_GET_USER', {})

print '##### Hang Test #####'
print rpc.call('RANDOM_FUNCTION', {})


rpc.stop()
#time.sleep(1)

