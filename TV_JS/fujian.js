/* ============================================================
 * 福建    key: fujian
 * ------------------------------------------------------------
 * 来源站点：https://live.fjtv.net/
 * 取流方式：动态取流
 * 频道数：6      最后更新：2026-10-16
 *
 * 本文件是 TVLive 的「福建」分组订阅文件，可直接手工修改后重新上传。
 * 改完记得同步 index.json 里本文件的 sha256（不想校验就写空字符串）。
 * ============================================================ */

/* ---- 1) 频道表：TVLive 启动时会读走这一段 ----
 * name      显示名（分组标题已写省份，这里不用再重复前缀）
 * url       兜底直连地址；带时效签名的台靠下面解析器现算，这里填旧的没关系
 * provider  解析器名，对应下面第 2 段里注册的名字；不需要就整行删掉
 * param     传给解析器的参数，一般是流名或频道 id
 */
TVRemote.define({
  key: "fujian",
  group: "福建",
  updated: "2026-10-16",
  note: "动态取流",
  list: [
    { number: 201, name: "东南卫视", url: "https://live1-fuyun.fjtv.net/dnpd/hd/live.m3u8?_upt=ed1fd9ba1791658569", provider: "fujian", param: "5" },
    { number: 202, name: "海峡卫视", url: "https://live1-fuyun.fjtv.net/haixiapd/hd/live.m3u8?_upt=553c53961791658563", provider: "fujian", param: "3" },
    { number: 203, name: "福建综合频道", url: "https://live2-fuyun.fjtv.net/zhpd/hd/live.m3u8?_upt=4f4470731791658567", provider: "fujian", param: "4" },
    { number: 204, name: "福建新闻频道", url: "https://live1-fuyun.fjtv.net/xwpd/hd/live.m3u8?_upt=f2d4ea371791658582", provider: "fujian", param: "13" },
    { number: 205, name: "福建少儿频道", url: "https://live2-fuyun.fjtv.net/child/hd/live.m3u8?_upt=b43fe33b1791658561", provider: "fujian", param: "2" },
    { number: 206, name: "福建文旅体育频道", url: "https://live1-fuyun.fjtv.net/dspd/hd/live.m3u8?_upt=79d8dfd41791658576", provider: "fujian", param: "8" }
  ]
});

/* ---- 2) 取流解析器：带时效签名的台靠它现算新鲜地址 ----
 * 每个解析器注册成 window.__RESOLVERS.<provider>(param) -> Promise<m3u8>
 * 不想用解析器就整段删掉，播放时会退回上面的 url。
 */
/* ============================================================
 * 福建 直播解析器  (window.__RESOLVERS.fujian)
 * 站点: https://live.fjtv.net/
 * ------------------------------------------------------------
 * 原理:
 *   GET https://live.fjtv.net/m2o/channel/channel_info.php?channel_id=<N>
 *   返回 JSON 数组，[0].m3u8 (或 [0].channel_stream[0].m3u8) 即带
 *   _upt 时效签名的播放地址。
 *
 *   !! 该接口对请求头敏感，缺了会 403 (且对 TLS 指纹也敏感，
 *      curl 直连会 403，浏览器/WebView/Node-undici 正常)：
 *        Referer: https://live.fjtv.net/
 *        Accept: *\/*
 *        sec-ch-ua / sec-ch-ua-mobile / sec-ch-ua-platform
 *        Sec-Fetch-Mode: cors
 *        Sec-Fetch-Site: same-origin
 *   ---- 注意：sec-ch-ua* 与 Sec-Fetch-* 是"禁止的头"，
 *        浏览器 fetch 无法手动设置；从 live.fjtv.net 同源页面/WebView
 *        发起时浏览器会自动带上，因此本函数默认不显式设置它们，
 *        但显式设置 Referer/Accept。若在无这些自动头的环境跑，
 *        需要外部代理补头。
 * ------------------------------------------------------------
 * channel_id 对照:
 *   东南卫视=5 海峡卫视=3 福建综合=4 福建新闻=13 福建少儿=2 福建文旅体育=8
 * ============================================================ */
(function (G) {
  'use strict';
  G.__RESOLVERS = G.__RESOLVERS || {};

  var API = 'https://live.fjtv.net/m2o/channel/channel_info.php?channel_id=';

  var CHANNELS = [
    { name: '东南卫视', id: 5 },
    { name: '海峡卫视', id: 3 },
    { name: '福建综合', id: 4 },
    { name: '福建新闻', id: 13 },
    { name: '福建少儿', id: 2 },
    { name: '福建文旅体育', id: 8 },
  ];
  var ALIAS = {
    '综合频道': '福建综合', '新闻频道': '福建新闻', '少儿频道': '福建少儿',
    '文旅体育': '福建文旅体育', '文旅体育频道': '福建文旅体育', '东南': '东南卫视', '海峡': '海峡卫视',
  };

  function pick(ch) {
    if (ch == null) return null;
    if (ALIAS[ch]) ch = ALIAS[ch];
    for (var i = 0; i < CHANNELS.length; i++) if (CHANNELS[i].name === ch || String(CHANNELS[i].id) === String(ch)) return CHANNELS[i];
    for (var j = 0; j < CHANNELS.length; j++) if (ch.indexOf(CHANNELS[j].name) >= 0 || CHANNELS[j].name.indexOf(ch) >= 0) return CHANNELS[j];
    return null;
  }

  function fetchInfo(id) {
    // sec-ch-ua / sec-ch-ua-mobile / sec-ch-ua-platform 是"禁止的头"，JS 无法手动设置；
    // 但 Chromium(WebView) 会对所有请求自动附带这三个默认 client hints —— 服务端正是靠
    // 它们放行。Referer 也用 fetch 的 referrer 选项设定(与目标同源，允许)，
    // 避免 file:// 页面发出 file:// Referer 被 403。
    return fetch(API + id, {
      headers: {
        'Accept': '*/*',
      },
      // 浏览器里用 referrer 选项给出 Referer（Referer 是禁止头，不能走 headers）。
      // 目标与 referrer 同源(live.fjtv.net)，允许设置。
      referrer: 'https://live.fjtv.net/',
      cache: 'no-store',
    }).then(function (r) {
      if (!r.ok) throw new Error('福建：channel_info HTTP ' + r.status + ' (需 Referer / sec-ch-ua 头)');
      return r.json();
    }).then(function (j) {
      var node = Array.isArray(j) ? j[0] : j;
      if (!node) throw new Error('福建：channel_id=' + id + ' 返回空');
      var url = node.m3u8;
      if (!url && node.channel_stream && node.channel_stream[0]) url = node.channel_stream[0].m3u8;
      if (!url) throw new Error('福建：channel_id=' + id + ' 无 m3u8 (未配置直播流)');
      return url;
    });
  }

  function resolve(channel) {
    var c = pick(channel);
    if (!c) return Promise.reject(new Error('福建：未知频道 [' + channel + ']'));
    return fetchInfo(c.id);
  }

  function resolveAll() {
    return Promise.all(CHANNELS.map(function (c) {
      return fetchInfo(c.id).then(function (url) { return { name: c.name, id: c.id, url: url }; })
        .catch(function (e) { return { name: c.name, id: c.id, error: e.message }; });
    }));
  }

  G.__RESOLVERS.fujian = {
    name: '福建',
    site: 'https://live.fjtv.net/',
    channels: CHANNELS,
    resolve: resolve,
    resolveAll: resolveAll,
  };
})(typeof window !== 'undefined' ? window : this);
