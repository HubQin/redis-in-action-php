<?php
/**
 * 购物车
 */

$redis = new Redis();
$redis->connect('127.0.0.1', '6379') || exit('连接失败！');

/**
 * @param Redis $redis
 * @param $session
 * @param $item
 * @param $count
 */
function addToCart($redis, $session, $item, $count)
{
    if ($count < 0) {
        $redis->hDel('cart:' . $session, $item);
    } else {
        $redis->hSet('cart:' . $session, $item, $count);
    }
}
