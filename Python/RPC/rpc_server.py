#!/usr/bin/env python3
import pika
import ctypes
import time

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='172.17.0.2'))

channel = connection.channel()

channel.queue_declare(queue='rpc_queue')


def fib(n:int) -> int:
    if n == 0:
        return 0
    elif n == 1:
        return 1
    else:
        return fib(n - 1) + fib(n - 2)

def cppSharedLib(x:int,y:int) -> int:
    TestLib = ctypes.cdll.LoadLibrary('./libTestLib.so')
    time.sleep(30)
    return TestLib.SampleAddInt(x,y)


def on_request(ch, method, props, body):
    n = int(body)

    print(" [.] fib(%s)" % n)
    response = fib(n)
    resp = cppSharedLib(n, n)

    ch.basic_publish(exchange='',
                     routing_key=props.reply_to,
                     properties=pika.BasicProperties(correlation_id = \
                                                         props.correlation_id),
                     body=' - '.join([str(response),str(resp)]) )
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='rpc_queue', on_message_callback=on_request)

print(" [x] Awaiting RPC requests")
channel.start_consuming()