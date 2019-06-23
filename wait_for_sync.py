import redis
import time

mconn = redis.Redis(host='127.0.0.1', port=6379)
sconn = redis.Redis(host='127.0.0.1', port=6380)

# mconn 主服务器连接对象
# sconn 从服务器连接对象
def wait_for_sync(mconn, sconn):
	# 生成一个唯一标识
	identifier = str(uuid.uuid4())
	# 将这个唯一标识（令牌）添加到主服务器
	mconn.zadd('sync:wait', identifier, time.time())

	# 等待主从复制成功
	# master_link_status = up 代表复制成功
	# 等同于 while sconn.info()['master_link_status'] = 'down'
	# 即同步为完成时，继续等待，每隔1ms判断一次
	while not sconn.info()['master_link_status'] != 'up':
		time.sleep(.001)

	# 从服务器还没有接收到主服务器的同步时（无identifier），继续等待
	while not sconn.zscore('sync:wait', identifier):
		time.sleep(.001)

	dealine = time.time() + 1.01 # 最多只等待1s

	while time.time() < dealine:
		# 注意AOF开启时，才有aof_pending_bio_fsync选项
		# 等于0说明没有fsync挂起的任务，即写入磁盘已完成
		if sconn.info()['aof_pending_bio_fsync'] == 0:
			break
		time.sleep(.001)

	# 从服务器同步到磁盘后完成后，主服务器删除该唯一标识
	mconn.zrem('sync:wait', identifier)
	# 删除15分钟前可能没有删除的标识
	mconn.zremrangebyscore('sync.wait', time.time() - 900)