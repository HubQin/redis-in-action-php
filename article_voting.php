<?php
/**
 * Redis In Action
 * 文章投票功能
 * 前提条件：
 * 文章发表时，记录作者、发表时间、链接、标题、初始投票数
 * 每获得一个投票，文章获得432分（86400/200）
 * 数据结构：
 * 文章hash -- 每篇文章key的形式如：article:92617
 * 文章发表时间zset集合（time:），按时间排序 -- 每条记录的形式如：article:92617（member）  1332065417（score）
 * 文章得分zset集合(score:)，按分数排序
 * 用户对文章的投票set集合(vote:xxxx) -- key形式如：vote:100408，item形式如：user:233487
 */

const ONE_WEEK_IN_SECONDS = 7 * 86400;
const VOTE_SCORE = 432;
const ARTICLES_PER_PAGE = 25;

$redis = new Redis();
$redis->connect('127.0.0.1', '6379') || exit('连接失败！');

/**
 * 文章投票
 * @param Redis $redis
 * @param $user
 * @param $article
 */
function articleVote($redis, $user, $article)
{
    $cutoff = time() - ONE_WEEK_IN_SECONDS;
    //对发表时间超过一周的文章投票不生效
    //获取 time: 有序集合对应 member 的 score
    if ($redis->zScore('time:', $article) < $cutoff) {
        return;
    }

    $article_id = explode(':', $article)[1];
    //无序集合，添加记录，如果记录存在，返回0（说明用户已对该文章投票），反之则计算分数
    if ($redis->sAdd('voted:' . $article_id, $user)) {
        // 使用事务操作
        /*$redis->multi()
            ->zIncrBy('score:' , VOTE_SCORE, $article) //增加文章的分数
            ->hIncrBy($article, 'votes', 1)  //增加文章的投票数
            ->exec();*/

        //使用pipeline型的事务
        //一次性向服务端发送所有命令，减少客户端与服务端之间通讯往返次数
        $pipe = $redis->multi(Redis::PIPELINE);
        $pipe->zIncrBy('score:', VOTE_SCORE, $article);
        $pipe->hIncrBy($article, 'votes', 1);
        $pipe->exec();
    }
}

/**
 * 发表文章
 * @param Redis $redis
 * @param string $user example: 'user:123456'
 * @param $title
 * @param $link
 * @return integer
 */
function postArticle($redis, $user, $title, $link)
{
    $article_id = $redis->incr('article:');  //自增1，不存在key则赋值1
    $voted = 'voted:' . $article_id;
    $redis->sAdd($voted, $user);  //将作者设为已投票用户
    $redis->expire($voted, ONE_WEEK_IN_SECONDS);  //文章投票信息设置为一周后自动失效

    $now = time();

    //添加文章
    $article = 'article:' . $article_id;  //作为文章hash的key值
    $redis->hMSet($article, [  //批量设置hash键值对
        'title' => $title,
		'link' => $link,
		'poster' => $user,
		'time' => $now,
		'votes' => 1,
    ]);

    //注意zadd第二个参数为score，第三个为member
    $redis->zAdd('score:', $now + VOTE_SCORE, $article);  //设置文章初始分数
    $redis->zAdd('time:',  $now, $article);  //记录文章发表时间

    return $article_id;
}

/**
 * 获取文章列表
 * @param Redis $redis
 * @param $page
 * @param string $order  用来排序的有序集合
 */
function getArticles($redis, $page, $order = 'score:')
{
    $start = ($page - 1) * ARTICLES_PER_PAGE;
	$end = $start + ARTICLES_PER_PAGE - 1;

    //获取指定范围内的member值（文章ID，article:123456），按$order分数递减排序
    $ids = $redis->zRevRange($order, $start, $end);

    $pipe = $redis->multi(Redis::PIPELINE);
    foreach ($ids as $id) {
        $pipe->hGetAll($id);

        //不使用pipeline的时候
        /*$article_data = $redis->hGetAll($id);
        $article_data['id'] = $id;
        $articles[] = $article_data;*/
    }
    $articles = $pipe->exec();

    //把文章ID加回去
    foreach ($articles as $k => $article) {
        $articles[$k]['id'] = $ids[$k];
    }
    return $articles;
}

/**
 * 添加/移除文章分类
 * @param Redis $redis
 * @param $article_id
 * @param array $to_add
 * @param array $to_remove
 */
function addRemoveGroups($redis, $article_id, $to_add = [], $to_remove = [])
{
    $article = 'article:' . $article_id;

    foreach ($to_add as $group) {
        $redis->sAdd('group:' . $group, $article);
    }
    foreach ($to_remove as $group) {
        $redis->sRem('group:' . $group, $article);
    }
}

/**
 * 获取分组下的文章数据
 * @param Redis $redis
 * @param $group
 * @param $page
 * @param string $order
 */
function getGroupArticles($redis, $group, $page, $order = 'score:')
{
    $key = $order . $group;
    if (!$redis->exists($key)) {
        //获得对应分组下，文章-分数的有序集合
        $redis->zInterStore($key, ['group:' . $group, $order], [1, 1], 'max');
        $redis->expire($key, 60);
    }
    return getArticles($redis, $page, $key);
}

//发布若干文章
postArticle($redis, 'user:1', '测试文章1', 'article-link-1');
postArticle($redis, 'user:2', '测试文章2', 'article-link-2');
postArticle($redis, 'user:3', '测试文章3', 'article-link-3');


//用户10对文章1进行投票
articleVote($redis, 'user:10', 'article:1');

echo "article:1 的投票用户:" . PHP_EOL;
$result = $redis->sMembers('voted:1');
print_r($result);

echo "各文章得分:" . PHP_EOL;
$scores = $redis->zRange('score:', 0, -1, 'withscores');
print_r($scores);

echo "文章列表:" . PHP_EOL;
$articles = getArticles($redis, 1);
print_r($articles);
exit();

//给文章添加分类
addRemoveGroups($redis, '1', ['php', 'redis']);
addRemoveGroups($redis, '2', ['python', 'redis']);

//获取‘redis’分组下的文章
$redisGroupArticles = getGroupArticles($redis, 'redis', 1);
echo "redis分类的文章列表:" . PHP_EOL;
print_r($redisGroupArticles);


