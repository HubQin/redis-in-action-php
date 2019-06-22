<?php
/**
 * Created by PhpStorm.
 * User: hugh
 * Date: 2019/6/21
 * Time: 22:14
 */
$redis = new Redis();
$redis->connect('127.0.0.1', '6379') || exit('连接失败！');

$redis->subscribe(['news'], function($redis, $channel, $msg){
    var_dump($msg);
});

