import redis
import time

conn = redis.Redis(host='127.0.0.1', port=6379)

# 将商品放到市场上销售
def list_item(conn, itemid, sellerid, price):
    inventory = "inventory:%s"%sellerid  # inventory key
    item = "%s.%s"%(itemid, sellerid)    # item key

    end = time.time() + 5
    pipe = conn.pipeline()

    while time.time() < end:
        try:
            pipe.watch(inventory) # 监视库存变化                    
            if not pipe.sismember(inventory, itemid): # 如果库存中没有该商品
                pipe.unwatch()   # 取消监控                    
                return None

            pipe.multi() # 开启事务                            
            pipe.zadd("market:", item, price)  # 添加商品到市场      
            pipe.srem(inventory, itemid)       # 从库存中删除商品      
            pipe.execute()                     # 执行事务      
            return True
        # WATCH和EXEC之间所监控的inventory已经发生变化
        # 这时事务执行失败，抛出WatchError
        # 这里不做任何处理，5s内会继续while循环
        except redis.exceptions.WatchError:          
            pass                                     
    return False

# 购买商品
def purchase_item(conn, buyerid, itemid, sellerid, lprice):
    buyer = "users:%s"%buyerid            # 当前买家
    seller = "users:%s"%sellerid          # 当前卖家
    item = "%s.%s"%(itemid, sellerid)	  # 市场market上商品的key
    inventory = "inventory:%s"%buyerid	  # 买家用户商品库存
    end = time.time() + 10
    pipe = conn.pipeline()

    while time.time() < end:
        try:
            pipe.watch("market:", buyer)  # 监控当前市场和当前买家            

            price = pipe.zscore("market:", item)    # 商品价格    
            funds = int(pipe.hget(buyer, "funds"))  # 当前买家余额   
            if price != lprice or price > funds:    # 当前价格是否发生变化或买家余额不足  
                pipe.unwatch()                      # 取消监控   
                return None							# 购买失败

            pipe.multi()    # 开启事务                           
            pipe.hincrby(seller, "funds", int(price))  # 卖家余额增加
            pipe.hincrby(buyer, "funds", int(-price))  # 买家余额减少
            pipe.sadd(inventory, itemid)               # 将添加该商品到买家库存
            pipe.zrem("market:", item)                 # 删除市场中的该商品
            pipe.execute()                             # 执行事务
            return True								   # 成功完成一次买卖过程		

        # WATCH失败，即在WATCH和EXEC之间监控的KEY发生了改变
        # 10s内会继续while循环重试
        except redis.exceptions.WatchError:            
            pass                                       

    return False  # 购买失败


# 非事务型操作（处理大量的操作能大大提高效率）
# 将2.5节的update_token改造为非事务型流水线操作
# 改造前：
# 需要2-5次通信往返
# 假如每次通讯耗时2毫秒，则执行一次update_token要4-10毫秒
# 那么每秒可以处理的请求数为100-250次
def update_token(conn, token, user, item=None):
    timestamp = time.time()                            
    conn.hset('login:', token, user)        # 1           
    conn.zadd('recent:', token, timestamp)  # 2           
    if item:
        conn.zadd('viewed:' + token, item, timestamp)   # 3
        conn.zremrangebyrank('viewed:' + token, 0, -26) # 4
        conn.zincrby('viewed:', item, -1)  				# 5

# 改造后
# 只要一次通信
# 通信往返次数减少到原来的1/2-1/5
# 每秒处理请求数可以到500次
def update_token_pipeline(conn, token, user, item=None):
    timestamp = time.time()
    pipe = conn.pipeline(False)  # 非事务型流水线操作                        
    pipe.hset('login:', token, user)
    pipe.zadd('recent:', token, timestamp)
    if item:
        pipe.zadd('viewed:' + token, item, timestamp)
        pipe.zremrangebyrank('viewed:' + token, 0, -26)
        pipe.zincrby('viewed:', item, -1)
    pipe.execute()   # 执行添加的所有命令          