## 基本数据类型及其操作

##  string
```
	set abc hello  // OK
	get abc hello  // hello
	del abc  // (integer) 1
```
## list
> 列表中的值可重复

```
rpsuh list-key item     // (integer) 1  //从右边添加一个元素
rpush list-key item2   // (integer) 2
rpush list-key item    // (integer) 3
lrange list-key 0 -1   //1) "item" 2) "item2" 3) "item"  //输出整个列表
lindex list-key 1    // item2  //指定位置的元素
lpop list-key    // item  //从左边删除一个元素
```   
## set
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
```   

## hash
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

## zset
> 类似hash，有序集合存储的是键值对，键（成员）是唯一的，值（分数）必须是浮点数

```
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
```
