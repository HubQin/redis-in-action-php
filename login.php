<?php
/**
 * Created by PhpStorm.
 * User: hugh
 * Date: 2019/6/8
 * Time: 8:44
 */

/**
 * Data structure
 *  登录数据
 *  +-+ login: +---------------+ hash +--+
 *  |                                    |
 *  |   token +-------------> user_id    |
 *  |   (key)                 (value)    |
 *  |                                    |
 *  +------------------------------------+
 *  最近访问数据
 *  +-+ recent: +--------------+ zset +--+
 *  |                                    |
 *  |   token +-------------> timestamp  |
 *  |   (member)              (score)    |
 *  |                                    |
 *  +------------------------------------+
 *
 *  浏览记录数据
 *  +-+ viewed:123(uid) +------+ zset +--+
 *  |                                    |
 *  |   token +-------------> timestamp  |
 *  |   (member)              (score)    |
 *  |                                    |
 *  +------------------------------------+
 *
 */
const QUIT = false;
const LIMIT = 1000; //原书为10000000

$redis = new Redis();
$redis->connect('127.0.0.1', '6379') || exit('连接失败！');

/**
 * 检查token
 * @param Redis $redis
 * @param $token
 * @return mixed
 */
function checkToken($redis, $token)
{
    return $redis->hGet('login:', $token);
}

/**
 * 更新token
 * @param Redis $redis
 * @param $token
 * @param $user
 * @param $item
 */
function updateToken($redis, $token, $user, $item = null)
{
    $now = time();
    //添加或更新用户的token
    $redis->hSet('login:', $token, $user);
    //添加或更新用户最近访问时间
    $redis->zAdd('recent:', $now, $token);

    if ($item) {
        $redis->zAdd('viewed:' . $token, $now, $item);
        //表示从0开始，到倒数第26个之间的数据删除（闭区间，最后一个为-1）
        //也即是从-1数到-25这个范围内的数据保留-->保留最后25个
        $redis->zRemRangeByRank('viewed:' . $token, 0, -26);
    }
}

/**
 * 清除数据
 * 前提假设：网站一天有500万人次访问，那么每秒新增token数为5000000/86400=58
 * 每秒执行一次清理的话，则每秒要清理58条记录
 * 存在的问题：如果用户刚好在访问网站
 * 这时候token刚好被删除的话，又需要重新登录
 * @param Redis $redis
 */
function cleanSessions($redis)
{
    while (!QUIT) {  //可以改为守护进程或cron job任务来定期执行
        //统计最近访问记录数量
        $size = $redis->zCard('recent:');
        //如果数量没有超过限制，则休眠1s，重新检查
        if ($size <= LIMIT) {
            sleep(1);
            continue;
        }
        $end_index = min($size - LIMIT, 100);
        //$end_index的值为[0-100]区间的整数
        //取出recent: 集合保留0-100之间的记录，也即超过LIMIT的这一部分
        //下面将这一部分进行删除
        $tokens = $redis->zRange('recent:', 0, $end_index - 1);
        $session_keys = [];
        foreach ($tokens as $token) {
            $session_keys[] = 'viewed:' . $token;
        }
        //删除相应用户的浏览记录
        $aa = $redis->delete($session_keys);
        //删除相应用户的登录信息
        $redis->hDel('login:', ...$tokens);
        //删除相应用户的最近访问记录
        $redis->zRem('recent:', ...$tokens);
    }
}

//假设用户访问了30个商品，商品id从1到30
//最终viewed:123有序集合的基数是25
for ($i = 0; $i < 30; $i++) {
    updateToken($redis, 'user-1-token', 123, $i);
}
$count = $redis->zCard('viewed:user-1-token');
echo $count . PHP_EOL;  //输出25

//根据token查找用户
$is_login = checkToken($redis, 'user-1-token');
echo (bool)$is_login . PHP_EOL;

//模拟大量用户访问
for ($i = 0; $i < 1050; $i++) {
    updateToken($redis, 'token-' . $i, 123 + $i, $i);
}
//view:xxx集合的数量、‘recent:’基数，‘login:’的基数将保持在LIMIT
cleanSessions($redis);

