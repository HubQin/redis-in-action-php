import redis
import time
from datetime import datetime

conn = redis.Redis(host='127.0.0.1', port=6379)


# 以秒为单位的计数器精度
PRECISION = [1, 5, 60, 300, 3600, 18000, 86400]     

QUIT = False
SAMPLE_COUNT = 100    

# 更新计数器
def update_counter(conn, name, count=1, now=None):

    now = now or time.time()    # 当前时间                        
    pipe = conn.pipeline()                              
    for prec in PRECISION:                              
        pnow = int(now / prec) * prec  # 获取当前时间片的开始时间                 
        hash = '%s:%s'%(prec, name)    # 创建存储计数信息的hash
        
        # zadd在redis-py 3.0之后更改了，第二个参数应该传入一个字典 √                
        # pipe.zadd('known:', hash, 0) ×
        # 有序集合，用于后期可以按顺序迭代清理计数器（并不使用expire，因为expire只能对hash整个键过期）
        # 这里可以组合使用set和list，但用zset，可以排序，又可以避免重复元素
        # **这个zset的score值都是0，所以最后排序的时候按member值来排序**
        pipe.zadd('known:', {hash: 0})           
        pipe.hincrby('count:' + hash, pnow, count) # 更新对应精度时间片的计数   
    pipe.execute()

# update_counter(conn, 'hit')

# 获取计数器
def get_counter(conn, name, precision):
    hash = '%s:%s'%(precision, name)  # 要获取的hash的key              
    data = conn.hgetall('count:' + hash)            
    to_return = []                                  
    for key, value in data.items():             
        to_return.append((int(key), int(value)))    
    to_return.sort()                                
    return to_return

# print(get_counter(conn, 'hit', 5))

# 清理计数器
# 清理规则： 1s,5s计数器，1min清理一次
# 后面的，5min计数器5min清理一次，以此类推
def clean_counters(conn):
    pipe = conn.pipeline(True)
    passes = 0 
    # 按时间片段从小到大迭代已知的计数器                                                 
    while not QUIT:                                             
        start = time.time()                                     
        index = 0                                               
        while index < conn.zcard('known:'):
            # 取出有序集合的一个元素                     
            hash = conn.zrange('known:', index, index)          
            index += 1
            if not hash:
                break
            hash = hash[0]

            # 得到时间精度
            prec = int(hash.partition(':')[0])
            # 按上面说明的清理规则计算时间间隔                  
            bprec = int(prec // 60) or 1    # '//'操作是取整除法                    
            if passes % bprec:                                  
                continue

            hkey = 'count:' + hash
            cutoff = time.time() - SAMPLE_COUNT * prec          
            samples = map(int, conn.hkeys(hkey))                
            samples.sort()                                      
            remove = bisect.bisect_right(samples, cutoff)       

            if remove:                                          
                conn.hdel(hkey, *samples[:remove])              
                if remove == len(samples):                      
                    try:
                        pipe.watch(hkey)                        
                        if not pipe.hlen(hkey):                 
                            pipe.multi()                        
                            pipe.zrem('known:', hash)           
                            pipe.execute()                      
                            index -= 1                          
                        else:
                            pipe.unwatch()                      
                    except redis.exceptions.WatchError:         
                        pass                                    

        passes += 1                                             
        duration = min(int(time.time() - start) + 1, 60)        
        time.sleep(max(60 - duration, 1))                       