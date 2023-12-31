let header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36',
	'Referer': 'https://gitcafe.net/alipaper/'
};

const cates = '华语电视$hyds#日韩电视$rhds#欧美电视$omds#其他电视$qtds#华语电影$hydy#日韩电影$rhdy#欧美电影$omdy#其他电影$qtdy#华语动漫$hydm#日韩动漫$rhdm#欧美动漫$omdm#纪录片$jlp#综艺片$zyp#教育培训$jypx#其他视频$qtsp#华语音乐$hyyy#日韩音乐$rhyy#欧美音乐$omyy#其他音乐$qtyy';
let homeJson = {}

function init(ext) {
    let url = 'https://gitcafe.net/alipaper/home.json?v=1692110598065';
    let res = req(url, {
        headers: header,
        method: 'GET'
    });
    homeJson = JSON.parse(res.content);
}

function home(filter) {
    const data = cates.split('#');
    let classes = [];
    for (const item of data) {
        const cate = item.split('$');
        classes.push({
            'type_id': cate[1],
            'type_name': cate[0]
        });
    }
    console.log(JSON.stringify(classes));
    return JSON.stringify({
        'class': classes
    });
}

function homeVod(params) {
    return category('hyds');
}

function category(tid, pg, filter, extend) {
    let videos = [];
    const data = homeJson.data[tid].catdata;
    for (const v of data) {
        const video = {
            'vod_id': 'push://https://www.aliyundrive.com/s/' + v.alikey,
            'vod_name':v.title
        };
        videos.push(video);
    }
    
    return JSON.stringify({
        'page': 1,
        'pagecount':1,
        'limit': 1,
        'total': 1,
        'list': videos,
        'type_des': ''
    });        
}


__JS_SPIDER__ = {
    init: init,
    home: home,
    homeVod: homeVod,
    category: category,
    detail: null,
    play: null,
    search: null,
    extResult: null
}


    