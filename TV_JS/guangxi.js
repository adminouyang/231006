/* ============================================================
 * 广西    key: guangxi
 * ------------------------------------------------------------
 * 来源站点：https://tv.gxtv.cn/
 * 取流方式：动态取流
 * 频道数：8      最后更新：2026-10-16
 *
 * 本文件是 TVLive 的「广西」分组订阅文件，可直接手工修改后重新上传。
 * 改完记得同步 index.json 里本文件的 sha256（不想校验就写空字符串）。
 * ============================================================ */

/* ---- 1) 频道表：TVLive 启动时会读走这一段 ----
 * name      显示名（分组标题已写省份，这里不用再重复前缀）
 * url       兜底直连地址；带时效签名的台靠下面解析器现算，这里填旧的没关系
 * provider  解析器名，对应下面第 2 段里注册的名字；不需要就整行删掉
 * param     传给解析器的参数，一般是流名或频道 id
 */
TVRemote.define({
  key: "guangxi",
  group: "广西",
  updated: "2026-10-16",
  note: "静态地址，无需解析",
  list: [
    { number: 171, name: "广西卫视", url: "https://hlscdn.liangtv.cn/live/0c4ef3a44b934cacb8b47121dfada66c/d7e04258157b480dae53883cc6f8123b.m3u8", provider: "guangxi", param: "广西卫视" },
    { number: 172, name: "广西综艺旅游频道", url: "https://hlscdn.liangtv.cn/live/de0f97348eb84f62aa6b7d8cf0430770/dd505d87880c478f901f38560ca4d4e6.m3u8", provider: "guangxi", param: "广西综艺旅游频道" },
    { number: 173, name: "广西都市频道", url: "https://hlscdn.liangtv.cn/live/b8f4e500a4024fd2bf189b46f490359f/b04d249044fb4d0887b88aa9c2cc8f6c.m3u8", provider: "guangxi", param: "广西都市频道" },
    { number: 174, name: "广西影视频道", url: "https://hlscdn.liangtv.cn/live/a84182dabc5147afbd3d90ddbb5a9404/d097f6c24c53463e897de496b32c7d2b.m3u8", provider: "guangxi", param: "广西影视频道" },
    { number: 175, name: "广西新闻频道", url: "https://hlscdn.liangtv.cn/live/a48635e37ac84afa82c0d0edc4bfabf9/dbc9a18971294257bad7c75b7f3f0c20.m3u8", provider: "guangxi", param: "广西新闻频道" },
    { number: 176, name: "广西国际频道", url: "https://hlscdn.liangtv.cn/live/0234c48e0bc24fe1b41b9999a253e581/1075ee38e04f490690f6a36a16e09c79.m3u8", provider: "guangxi", param: "广西国际频道" },
    { number: 177, name: "广西乐思购频道", url: "https://hlscdn.liangtv.cn/live/2cb851292fd14014a6558343872899e6/0820054f3fcc4ee5b4d17198bd7eddd6.m3u8", provider: "guangxi", param: "广西乐思购频道" },
    { number: 178, name: "广西移动数字电视频道", url: "https://hlscdn.liangtv.cn/live/b6cea70bfad24970aaa2256a3c340ad4/0a79a8e5f94641e583d1872ef7bed2bf.m3u8", provider: "guangxi", param: "广西移动数字电视频道" }
  ]
});

/* ---- 2) 取流解析器：带时效签名的台靠它现算新鲜地址 ----
 * 每个解析器注册成 window.__RESOLVERS.<provider>(param) -> Promise<m3u8>
 * 不想用解析器就整段删掉，播放时会退回上面的 url。
 */
/* ============================================================
 * 广西 直播解析器  (window.__RESOLVERS.guangxi)
 * 站点: https://tv.gxtv.cn/
 * ------------------------------------------------------------
 * 原理:
 *   页面 channeliveList.js 调:
 *     http.postNoToken('memberApi/channel/channelList',
 *         {pageNo:1, pageSize:1000, liveMethod:"0"})
 *   domainName       = https://api2019.gxtv.cn/
 *   setParams 自动补 deptId / platformId:
 *     deptId     = 0a509685ba1a11e884e55cf3fc49331c
 *     platformId = bd7d620a502d43c09b35469b3cd8c211
 *   返回 JSON: data.rows[].encodeM3u8 即 m3u8 地址。
 *   这些地址实测为长效静态地址（等 10 分钟再拉仍 200），
 *   所以也可直接写死兜底（见 STATIC_FALLBACK）。
 * ============================================================ */
(function (G) {
  'use strict';
  G.__RESOLVERS = G.__RESOLVERS || {};

  var API = 'https://api2019.gxtv.cn/memberApi/channel/channelList';
  var DEPT_ID = '0a509685ba1a11e884e55cf3fc49331c';
  var PLATFORM_ID = 'bd7d620a502d43c09b35469b3cd8c211';

  // 名称 <-> 接口名 对照 (键为对外常用名)
  var CHANNELS = [
    { name: '广西卫视', api: '广西卫视' },
    { name: '综艺旅游', api: '综艺旅游频道' },
    { name: '都市', api: '都市频道' },
    { name: '影视', api: '影视频道' },
    { name: '新闻', api: '新闻频道' },
    { name: '国际', api: '国际频道' },
    { name: '乐思购', api: '乐思购频道' },
    { name: '移动数字电视', api: '移动数字电视频道' },
  ];

  // 兜底静态地址（实测长效，2026-10-11 验证 8/8 全 200）
  var STATIC_FALLBACK = {
    '广西卫视': 'https://hlscdn.liangtv.cn/live/0c4ef3a44b934cacb8b47121dfada66c/d7e04258157b480dae53883cc6f8123b.m3u8',
    '综艺旅游频道': 'https://hlscdn.liangtv.cn/live/de0f97348eb84f62aa6b7d8cf0430770/dd505d87880c478f901f38560ca4d4e6.m3u8',
    '都市频道': 'https://hlscdn.liangtv.cn/live/b8f4e500a4024fd2bf189b46f490359f/b04d249044fb4d0887b88aa9c2cc8f6c.m3u8',
    '影视频道': 'https://hlscdn.liangtv.cn/live/a84182dabc5147afbd3d90ddbb5a9404/d097f6c24c53463e897de496b32c7d2b.m3u8',
    '新闻频道': 'https://hlscdn.liangtv.cn/live/a48635e37ac84afa82c0d0edc4bfabf9/dbc9a18971294257bad7c75b7f3f0c20.m3u8',
    '国际频道': 'https://hlscdn.liangtv.cn/live/0234c48e0bc24fe1b41b9999a253e581/1075ee38e04f490690f6a36a16e09c79.m3u8',
    '乐思购频道': 'https://hlscdn.liangtv.cn/live/2cb851292fd14014a6558343872899e6/0820054f3fcc4ee5b4d17198bd7eddd6.m3u8',
    '移动数字电视频道': 'https://hlscdn.liangtv.cn/live/b6cea70bfad24970aaa2256a3c340ad4/0a79a8e5f94641e583d1872ef7bed2bf.m3u8',
  };

  function pickApiName(ch) {
    if (ch == null) return null;
    for (var i = 0; i < CHANNELS.length; i++) {
      if (CHANNELS[i].name === ch || CHANNELS[i].api === ch) return CHANNELS[i].api;
    }
    for (var j = 0; j < CHANNELS.length; j++) {
      if (ch.indexOf(CHANNELS[j].name) >= 0 || CHANNELS[j].name.indexOf(ch) >= 0 ||
        ch.indexOf(CHANNELS[j].api) >= 0 || CHANNELS[j].api.indexOf(ch) >= 0) return CHANNELS[j].api;
    }
    return null;
  }

  function fetchChannelList() {
    var body = 'deptId=' + DEPT_ID + '&platformId=' + PLATFORM_ID +
      '&pageNo=1&pageSize=1000&liveMethod=0';
    return fetch(API, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'Origin': 'https://tv.gxtv.cn',
        'Referer': 'https://tv.gxtv.cn/',
        'Accept': 'application/json, text/javascript, */*; q=0.01',
      },
      body: body,
      cache: 'no-store',
    }).then(function (r) { return r.json(); }).then(function (j) {
      if (!j || !j.data || !j.data.rows) throw new Error('广西：channelList 返回异常 ' + JSON.stringify(j).slice(0, 120));
      return j.data.rows;
    });
  }

  function resolveAll() {
    return fetchChannelList().then(function (rows) {
      var out = {};
      rows.forEach(function (r) { if (r.encodeM3u8) out[r.name] = r.encodeM3u8; });
      return out;
    });
  }

  function resolve(channel) {
    var apiName = pickApiName(channel) || channel;
    return fetchChannelList().then(function (rows) {
      var hit = null;
      for (var i = 0; i < rows.length; i++) if (rows[i].name === apiName) { hit = rows[i]; break; }
      if (!hit) for (var k = 0; k < rows.length; k++) if (rows[k].name.indexOf(apiName) >= 0) { hit = rows[k]; break; }
      if (hit && hit.encodeM3u8) return hit.encodeM3u8;
      // 兜底静态
      if (STATIC_FALLBACK[apiName]) return STATIC_FALLBACK[apiName];
      throw new Error('广西：频道 [' + channel + '] 无 m3u8');
    });
  }

  G.__RESOLVERS.guangxi = {
    name: '广西',
    site: 'https://tv.gxtv.cn/',
    channels: CHANNELS,
    staticFallback: STATIC_FALLBACK,
    resolve: resolve,
    resolveAll: resolveAll,
  };
})(typeof window !== 'undefined' ? window : this);
