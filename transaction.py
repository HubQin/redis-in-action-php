import redis
import time
import threading

conn = redis.Redis(host='127.0.0.1', port=6379)

def notrans():
	# +1 并打印结果
	print(conn.incr('notrans:'))
	# 等待 100ms
	time.sleep(.1)
	# -1
	conn.incr('notrans:', -1)

def trans():
	# 创建一个事务型pipeline对象
	pipeline = conn.pipeline()
	# +1 操作放入队列
	pipeline.incr('trans:')
	time.sleep(.1)
	#-1 操作放入队列
	pipeline.incr('trans:', -1)
	# 执行被事务所包裹的命令，并打印结果
	print(pipeline.execute())


if 1:
	print('没有事务时的并发操作：')
	for i in range(3):
		threading.Thread(target=notrans).start()
	time.sleep(.5)
	'''结果（随机）1 2 3'''

	print('有事务时的并发操作：')
	for i in range(3):
		threading.Thread(target=trans).start()
	time.sleep(.5)
	'''结果[1, 0] [1, 0] [1, 0]'''