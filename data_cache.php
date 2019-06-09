<?php
/**
 * 数据缓存
 * 疑问：设置一个过期时间不就好了？
 */
const QUIT = false;
$redis = new Redis();
$redis->connect('127.0.0.1', '6379') || exit('连接失败！');

/**
 * @param Redis $redis
 * @param $row_id
 * @param $delay
 */
function scheduleRowCache($redis, $row_id, $delay)
{
    $redis->zAdd('delay:', $delay, $row_id);
    $redis->zAdd('schedule:', time(), $row_id);
}

/**
 * @param Redis $redis
 */
function cacheRows($redis)
{
    while (!QUIT) {
        //取出有序集合的第一个元素
        $next = $redis->zRange('schedule:', 0, 0, true);
        $now = time();

        if (!$next) {
            sleep(0.05);
            continue;
        }

        $row_id = array_keys($next)[0];
        $timestamp = array_values($next)[0];

        if ($timestamp > $now) {
            sleep(0.05);
            continue;
        }

        $delay = $redis->zScore('delay:', $row_id);

        //delay小于0，将该数据的缓存删除
        if ($delay <= 0) {
            $redis->zRem('delay', $row_id);
            $redis->zRem('schedule:', $row_id);
            $redis->del('inv:' . $row_id);
            continue;
        }

        //读取数据库数据**伪代码**
        $row = Db()->get($row_id);

        //设置缓存时间
        $redis->zAdd('schedule:', $row_id, $now + $delay);
        //设置数据缓存
        $redis->set('inv:' . $row_id, json_encode($row));
    }
}
