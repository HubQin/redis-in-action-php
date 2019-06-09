> 参考资料：https://redislabs.com/ebook/part-1-getting-started/chapter-1-getting-to-know-redis/1-2-what-redis-data-structures-look-like/

##  string

![Redis In Action 笔记（一）：基本数据类型及其操作](https://iocaffcdn.phphub.org/uploads/images/201906/07/27146/RsPYowcSXC.PNG!large)

```
	set abc hello  // OK
	get abc hello  // hello
	del abc  // (integer) 1
```
```
//增加/减少
incr key   // +1
decr key  //-1
incrby key amount  // +amount
decrby key amount  // -amount
```
```
//子串/位操作
append key value // 附加value到原有值后面
getrange key start end  //获取子串
setrange key offset value  //将offset位置的值替换为value
getbit key offset  //将字符串看成二进制，返回offset位置的二进制
setbit key offset value //将字符串看成二进制，offset位置设置为value
```
## list

![Redis In Action 笔记（一）：基本数据类型及其操作](https://iocaffcdn.phphub.org/uploads/images/201906/07/27146/BxVjLwY9BD.PNG!large)

> 列表中的值可重复

```
rpsuh list-key item     // (integer) 1  //从右边添加一个元素
rpush list-key item2   // (integer) 2
rpush list-key item    // (integer) 3
lrange list-key 0 -1   //1) "item" 2) "item2" 3) "item"  //输出整个列表
lindex list-key 1    // item2  //指定位置的元素
lpop list-key    // item  //从左边删除一个元素
```   

```
//阻塞（block）型操作和list之间转移元素
blpop key [key …] timeout  //从左到右的key列表中，弹出非空的一个，设置超时
brpop  //原理同上，参考：http://redisdoc.com/list/blpop.html
rpoplpush source-key dest-key
brpoplpush source-key dest-key timeout
```
## set

![Redis In Action 笔记（一）：基本数据类型及其操作](https://iocaffcdn.phphub.org/uploads/images/201906/07/27146/LL63YhiLmK.PNG!large)

> 集合中的元素无序、不重复

```
sadd set-key item    // (integer) 1  //添加一个元素
sadd set-key item2  // (integer) 1
sadd set-key item3   // (integer) 1
sadd set-key item    // (integer) 0  //添加已存在的元素返回0

smembers set-key    // 1) "item"  2) "item2"  3) "item3" //输出集合中所有元素
sismember set-key item4  // (integer) 0  // 判断item4是否在set-key集合中，不存在返回0
sismember set-key item    // (integer) 1 //存在返回1
srem set-key item2  // (integer) 1 //删除一个元素，返回删除的个数
srem set-key item2  // (integer) 0 // 删除不存在的元素，返回0

smove source-key dest-key item   //元素转移
spop key  //从集合中随机**移除**一个元素并返回该元素
srandmember key [count]    //从集合中随机返回一个或多个元素
scard key   //返回集合中元素个数
```   

```
// 集合运算
sdiff key-name [key-name …]  //返回第一个集合中没有在其他集合出现的元素
sdiffstore dest-key key-name [key-name …]  //同上，并将结果保存在dest-key中
sinter key-name [key-name …]  //返回所有集合中共有的
sinterstore dest-key key-name [key-name …]  //同上，并将结果保存到dest-ley中
sunion key-name [key-name …]
sunionstore dest-key key-name [key-name …]
```
## hash

![Redis In Action 笔记（一）：基本数据类型及其操作](https://iocaffcdn.phphub.org/uploads/images/201906/07/27146/2fTn8VV2kj.PNG!large)

> list 和 set 存储的是元素的序列，而hash存储的是键值对

```
hset hash-key sub-key1 value1     // (integer) 1  //新添加的，返回1
hset hash-key sub-key2 value2    // (integer) 1
hset hash-key sub-key1 value1    // (integer) 0  //非新添加，返回0

hgetall hash-key  //返回所有键值对
/**
	1) "sub-key1"
	2) "value1"
	3) "sub-key2"
	4) "value2"
*/
hdel hash-key sub-key2    // (integer) 1  //删除，删除前返回元素是否存在
hdel hash-key sub-key2    // (integer) 0
hget hash-key sub-key1    // "value1"
hgetall hash-key    // 1) "sub-key1"  2) "value1"
```

```
//批量操作
hmget key-name key [key …]
hmset key-name key value [key value …]
hdel key-name key [key …]
hlen key-name  // 返回键值对数量

//更多操作
hexists key-name key  //键是否存在
hkeys key-name  //返回所有键值
hvals key-name  //返回所有的值
hincrby key-name key increment
hincrbyfloat key-name key increment
```
## zset

![Redis In Action 笔记（一）：基本数据类型及其操作](https://iocaffcdn.phphub.org/uploads/images/201906/07/27146/2PvaKmh9Lb.PNG!large)

> 类似hash，有序集合存储的是键值对，键（成员）是唯一的，值（分数）必须是浮点数

```
//基本操作
zadd zset-key 728 member1    // (integer) 1  //添加元素，返回新增元素的数量
zadd zset-key 982 member0    // (integer) 1
zadd zset-key 982 member0    // (integer) 0  //实际没有新增元素，返回0
zrange zset-key 0 -1 withscores    //返回全部元素，按分数排序
/**
	1) "member1"
	2) "728"
	3) "member0"
	4) "982"
*/
zrangebyscore zset-key 0 800 withscores  // 按分数范围查询
/**
	1) "member1"
	2) "728"
*/
zrem zset-key member1    // (integer) 1  //删除，返回删除的元素个数
zrem zset-key member1    // (integer) 0

zcard  key-name  // 返回成员（member）的总数
zincrby  key-name amount member //给成员member增加amount
zcount key-name min max  //返回指定scroe范围的member数
zrank key-name member //返回指定member的位置
zscore key-name member //返回指定member的score
```

```
//操作数据范围和集合运算
//zinterstore（交集）例子，zunionstore（并集）同理
zadd zkey1 1 a 2 b
zadd zkey2 1 b 3 c
//原型： ZINTERSTORE destination numkeys key [key ...] [WEIGHTS weight [weight ...]] [AGGREGATE SUM|MIN|MAX]
//这里out为目标集合，合并zkey1和zkey2集合，权重都为1，聚合方式为求最大值
//输出："1"
zinterstore out 2 zkey1 zkey2 weights 1 1 aggregate max
zrange out 0 -1 withscores  //输出：1)  "b  2)  "2"
```
```
zrevrank key-name member  //返回member在集合倒序排序时的位置
zrevrange key-name start stop [WITHSCORES]  //相当于zrange倒序时获取范围

//返回score 值介于 min 和 max 之间(包括等于 min 或 max )的成员
//参考http://redisdoc.com/sorted_set/zrangebyscore.html
ZRANGEBYSCORE key min max [WITHSCORES] [LIMIT offset count] 

//相当于倒序时的ZRANGEBYSCORE
ZREVRANGEBYSCORE key max min [WITHSCORES] [LIMIT offset count]

//移除有序集 `key` 中，指定排名(rank)区间内的所有成员。
// 区间分别以下标参数 `start` 和 `stop` 指出，包含 `start` 和 `stop` 在内。
ZREMRANGEBYRANK key-name start stop

//移除有序集 key 中，所有 score 值介于 min 和 max 之间(包括等于 min 或 max )的成员
ZREMRANGEBYSCORE key-name min max
```
