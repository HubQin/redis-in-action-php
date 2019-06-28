import redis
import time
from datetime import datetime
import bisect

conn = redis.Redis(host='127.0.0.1', port=6379)


# 以秒为单位的计数器精度
PRECISION = [1, 5, 60, 300, 3600, 18000, 86400]     

QUIT = False
SAMPLE_COUNT = 100

# 更新计数器
# 将次数统计到每个时间段的开始点
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
        # **这个zset的score值都是0，所以最后排序的时候按member字符串的二进制来排序**
        pipe.zadd('known:', {hash: 0})   # 这个记录在后面的清理程序有用  

        pipe.hincrby('count:' + hash, pnow, count) # 更新对应精度时间片的计数   
    pipe.execute()

update_counter(conn, 'hit')

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
            # 取出有序集合的一个元素(打印hash，发现返回的是一个byte类型)                    
            hash = conn.zrange('known:', index, index)

            index += 1
            if not hash:
                break
            hash = hash[0]
            # 得到时间精度
            prec = int(hash.partition(b':')[0])
            # 按上面说明的清理规则计算时间间隔
            # 小于60s的计数器至少1min清理一次                  
            bprec = int(prec // 60) or 1    # '//'操作是取整除法 

            # 实现几分钟清理一次的逻辑
            # 不整除的时候continue --> 重新while循环
            # 比如，1分钟，每次都整除，所以每次判断后后执行continue下面的语句
            # 10分钟，要等10次到passes=10才整除                   
            if passes % bprec: #                                  
                continue

            # 清理逻辑开始
            hkey = 'count:' + hash.decode('utf-8') # 注意将byte转换成str，书中没有转换
            print(hkey)
            # 根据要保留的个数*精度，计算要截取的时间点
            cutoff = time.time() - SAMPLE_COUNT * prec

            # python3的map返回可迭代对象而不是list，原书的这句需要加上list转换          
            samples = list(map(int, conn.hkeys(hkey)))
            samples.sort()
            print(samples)
            # 二分法找出cutoff右边的位置（index）                                      
            remove = bisect.bisect_right(samples, cutoff)       

            print(remove)
            # 如果有需要移除的
            if remove: 
                # 删除0-remove位置的元素                                         
                conn.hdel(hkey, *samples[:remove])

                # 判断是否全部被移除              
                if remove == len(samples):                      
                    try:
                        pipe.watch(hkey) 
                        # 再次确保hash中已经没有元素                       
                        if not pipe.hlen(hkey):                 
                            pipe.multi() 
                            # 同时将known:中的相应元素移除                       
                            pipe.zrem('known:', hash)           
                            pipe.execute() 
                            # 减少了一个计数器                     
                            index -= 1                          
                        else:
                            pipe.unwatch()                      
                    except redis.exceptions.WatchError:         
                        pass                                    
        # 累计次数，直到整除，才开始清理程序
        passes += 1      

        # 计算程序运行时间，且保证至少1s，最多是1min                                       
        duration = min(int(time.time() - start) + 1, 60)  

        # 休息，时间为：1min减去程序运行时间，也即1min中剩余的时间，且保证至少是1s
        time.sleep(max(60 - duration, 1))                       


clean_counters(conn)