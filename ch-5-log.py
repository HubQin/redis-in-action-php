import redis
import time
import logging
from datetime import datetime

conn = redis.Redis(host='127.0.0.1', port=6379)

SEVERITY = {                                                    
    logging.DEBUG: 'debug',                                     
    logging.INFO: 'info',                                       
    logging.WARNING: 'warning',                                 
    logging.ERROR: 'error',                                     
    logging.CRITICAL: 'critical'                               
}  

# 这句运行出错，貌似原书有误，注释掉这句。                                                             
# SEVERITY.update((name,name) for name in SEVERITY.values()) 

# 记录最近日志
# 思路：将日志加入list，然后修剪到规定大小
def log_recent(conn, name, message, severity=logging.INFO, pipe=None):
    severity = str(SEVERITY.get(severity, severity)).lower()    
    destination = 'recent:%s:%s'%(name, severity)   # 日志的KEY，构成：recent：日志名称：日志级别            
    message = time.asctime() + ' ' + message  # 日志信息前面添加时间信息                  
    pipe = pipe or conn.pipeline()                              
    pipe.lpush(destination, message)   # 1. 加入list                         
    pipe.ltrim(destination, 0, 99)     # 2. 截取最近100条记录                        
    pipe.execute()     # 执行以上两步

# 运行：log_recent(conn, 'test', 'test_msg')
# 结果：（key）recent:test:info  （value）Sun Jun 23 11:57:38 2019 test_msg      

# 记录常见日志
# 思路：消息作为成员记录到有序集合，消息出现频率作为成员的分值（score）
# 记录的时间范围为1小时，记录的时候发现已经过了一小时，
# 则把已有的记录归档到上一小时（通过把KEY重命名来实现）
# 则新的一小时消息频率有从0开始记录
# 用于记录的KEY：[common:日志名称：日志级别]
def log_common(conn, name, message, severity=logging.INFO, timeout=5):
    severity = str(SEVERITY.get(severity, severity)).lower()    
    destination = 'common:%s:%s'%(name, severity) 
    #当前所处小时数              
    start_key = destination + ':start'    # common:日志名称：日志级别：start                     
    pipe = conn.pipeline()

    end = time.time() + timeout
    while time.time() < end:
        try:
            pipe.watch(start_key)    # 监控
            # 时间的转化：
            # datetime.utcnow() --> datetime.datetime(2019, 6, 23, 6, 51, 59, 941710)
            # datetime.utcnow().timetuple --> time.struct_time(tm_year=2019, tm_mon=6, tm_mday=23, tm_hour=6, tm_min=52, tm_sec=24, tm_wday=6, tm_yday=174, tm_isdst=-1)                          
            # datetime(*now[:4]) --> datetime.datetime(2019, 6, 23, 6, 0)
            # datetime(*now[:4]).isoformat() --> '2019-06-23T06:00:00'
            now = datetime.utcnow().timetuple()  
            # 简单获取小时数（原书方法行不通，这里加以修改）               
            hour_start = now.tm_hour         

            # 获取[common:日志名称：日志级别：start]的值
            # 这里返回字符串类型，注意转为整型
            existing = pipe.get(start_key)
            pipe.multi()   

            # 如果值存在 且 小于当前小时数                                  
            if existing and int(existing) < hour_start:
                # 进行归档
            	# KEY [common:日志名称：日志级别] 重命名为 [common:日志名称：日志级别:last]         
                pipe.rename(destination, destination + ':last') 
                # KEY [common:日志名称：日志级别:start] 重命名为 [common:日志名称：日志级别:pstart]
                pipe.rename(start_key, destination + ':pstart') 
                # KEY [common:日志名称：日志级别:start] 的值更新为当前小时数
                pipe.set(start_key, hour_start) 

            # 不存在则添加该日志开始时间记录                
            elif not existing:
            	# KEY [common:日志名称：日志级别:start] 的值设置为当前小时数                                  
                pipe.set(start_key, hour_start)

            # 对有序集合destination的成员message自增1
            # 注意：zincrby在redis-py3.0+的用法  
            pipe.zincrby(destination, 1, message)        
            # 记录到最新日志
            log_recent(pipe, name, message, severity, pipe)     
            return

        # 如果其他客户端刚好有操作，修改了watch的key，进行重试
        except redis.exceptions.WatchError:
            continue   
# 运行
log_common(conn, 'test', 'msg')
#结果
#（zset）common:test:info   msg --> 1
# -->1小时后再次记录日志的话，该KEY就会变成common:test:info:last
#（string）common:test:info:start   14（小时数）
# -->1小时后再次记录日志的话，该KEY就会变成common:test:info:pstart
#（list）recent:test:info   Wed Jun 26 22:53:17 2019 msg
