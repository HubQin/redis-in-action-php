<?php
//Sort命令详解
$redis = new Redis();
$redis->connect('127.0.0.1', '6379') || exit('连接失败！');

/**
 * Sort
 *
 * @param   string  $key
 * @param   array   $option array(key => value, ...) - optional, with the following keys and values:
 * - 'by' => 'some_pattern_*',
 * - 'limit' => array(0, 1),
 * - 'get' => 'some_other_pattern_*' or an array of patterns,
 * - 'sort' => 'asc' or 'desc',
 * - 'alpha' => TRUE,
 * - 'store' => 'external-key'
 * @return  array
 * An array of values, or a number corresponding to the number of elements stored if that was used.
 * @link    https://redis.io/commands/sort
 */

$redis->delete('s');
$redis->sadd('s', 5);
$redis->sadd('s', 4);
$redis->sadd('s', 2);
$redis->sadd('s', 1);
$redis->sadd('s', 3);

//一般排序、倒序、保存到out键
var_dump($redis->sort('s')); // 1,2,3,4,5
var_dump($redis->sort('s', ['sort' => 'desc'])); // 5,4,3,2,1
var_dump($redis->sort('s', ['sort' => 'desc', 'store' => 'out'])); // (int)5

//按字母排序、倒序、取出第一个起的两个元素
$redis->delete('test');
$redis->lpush('test', 'a');
$redis->lpush('test', 'd');
$redis->lpush('test', 'b');
var_dump($redis->sort('test', ['ALPHA' => true, 'limit' => [0,2], 'sort' => 'desc']));

//通过By匹配的key来排序id list
$keys = $redis->keys('price_*');
$redis->delete($keys);
$redis->set('price_1', 10);
$redis->set('price_2', 30);
$redis->set('price_3', 20);

$redis->delete('id');
$redis->lpush('id', 1);
$redis->lpush('id', 2);
$redis->lpush('id', 3);

$keys = $redis->keys('name_*');
$redis->delete($keys);
$redis->set('name_1', 'apple');
$redis->set('name_2', 'banana');
$redis->set('name_3', 'melon');

var_dump($redis->sort('id', ['BY' => 'price_*', 'SORT' => 'desc'])); //2,3,1

//使用不存在key排序，不进行排序来取得外部keys
//输出：array(3) {
//  [0]=>
//  string(2) "20"
//  [1]=>
//  string(2) "30"
//  [2]=>
//  string(2) "10"
//}
var_dump($redis->sort('id', ['BY' => 'non-exists', 'GET' => 'price_*']));
//使用 # 代表被排序的key本身
var_dump($redis->sort('id', ['BY' => 'non-exists', 'GET' => ['#','price_*']]));

//使用hash是的GET和BY
$redis->delete('fruit-*');
$redis->hSet('fruit-1', 'weight', 11);
$redis->hSet('fruit-2', 'weight', 13);
$redis->hSet('fruit-3', 'weight', 12);

var_dump($redis->sort('id', ['BY' => 'fruit-*->weight'])); // 1,3,2
//取得各hash中的weight
var_dump($redis->sort('id', ['BY' => 'fruit-*->weight', 'GET' => 'fruit-*->weight'])); // 11,12,13


