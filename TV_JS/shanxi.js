/* ============================================================
 * 山西    key: shanxi
 * ------------------------------------------------------------
 * 来源站点：https://www.sxrtv.com/tv/index.shtml
 * 取流方式：省级 tidePlayer + 市级 华为云
 * 频道数：16      最后更新：2026-10-16
 *
 * 本文件是 TVLive 的「山西」分组订阅文件，可直接手工修改后重新上传。
 * 改完记得同步 index.json 里本文件的 sha256（不想校验就写空字符串）。
 * ============================================================ */

/* ---- 1) 频道表：TVLive 启动时会读走这一段 ----
 * name      显示名（分组标题已写省份，这里不用再重复前缀）
 * url       兜底直连地址；带时效签名的台靠下面解析器现算，这里填旧的没关系
 * provider  解析器名，对应下面第 2 段里注册的名字；不需要就整行删掉
 * param     传给解析器的参数，一般是流名或频道 id
 */
TVRemote.define({
  key: "shanxi",
  group: "山西",
  updated: "2026-10-16",
  note: "省级 6（tidePlayer 每日 token）+ 市级 10（华为云 1 小时签名）",
  list: [
    { number: 91, name: "山西卫视", url: "https://livehhhttps.sxrtv.com/lsdream/q8RVWgs/1000/f3sqkR0.m3u8", provider: "shanxi", param: "q8RVWgs" },
    { number: 92, name: "黄河电视台", url: "https://livehhhttps.sxrtv.com/lsdream/lce1mC4/800/e3tlke0.m3u8", provider: "shanxi", param: "lce1mC4" },
    { number: 93, name: "山西经济与科技", url: "https://livehhhttps.sxrtv.com/lsdream/4j01KWX/800/6814k00.m3u8", provider: "shanxi", param: "4j01KWX" },
    { number: 94, name: "山西影视", url: "https://livehhhttps.sxrtv.com/lsdream/Md571Kv/800/p7iMk50.m3u8", provider: "shanxi", param: "Md571Kv" },
    { number: 95, name: "山西社会与法制", url: "https://livehhhttps.sxrtv.com/lsdream/p4y5do9/500/u2dpky0.m3u8", provider: "shanxi", param: "p4y5do9" },
    { number: 96, name: "山西文体(测试)", url: "https://livehhhttps.sxrtv.com/lsdream/agmpyEk/800/j1oakm0.m3u8", provider: "shanxi", param: "agmpyEk" },
    { number: 97, name: "太原新闻综合", url: "https://citymlive.sxrtv.com/live/sxtymlive.m3u8?hwSecret=0f9239f38747cfb3022a0d58ac418b269a8935d462568cd2a6887a1506c83cb0&hwTime=6aca8554", provider: "shanxi_city", param: "11" },
    { number: 98, name: "吕梁", url: "https://citymlive.sxrtv.com/live/sxllmlive.m3u8?hwSecret=ebb432ecb5ef55811cdc3537d78a00de6ad7fc02c9a64e4bdb12a9e9a8745624&hwTime=6aca8555", provider: "shanxi_city", param: "1" },
    { number: 99, name: "临汾", url: "https://citymlive.sxrtv.com/live/sxlfmlive.m3u8?hwSecret=f349d8d6d2d1f5810fd51c76d43370aaa5bfe526621f0548fc1f36bfc54e81d9&hwTime=6aca8555", provider: "shanxi_city", param: "2" },
    { number: 100, name: "忻州", url: "https://citymlive.sxrtv.com/live/sxxzmlive.m3u8?hwSecret=ee71cadbe0bf316b74e585c02b9e7f6a181a0f42a4e786b1d5c97f0a58d243f2&hwTime=6aca8555", provider: "shanxi_city", param: "3" },
    { number: 101, name: "运城", url: "https://citymlive.sxrtv.com/live/sxycmlive.m3u8?hwSecret=4fcc1ed32059eb46bf111b242cad4a15c626342130345865e11bb1f6340a0bf9&hwTime=6aca8555", provider: "shanxi_city", param: "4" },
    { number: 102, name: "晋中", url: "https://citymlive.sxrtv.com/live/sxjzmlive.m3u8?hwSecret=5198169c9d554ffaf0194158765d30ac46733b3f9a6eaf4f6f0b6bfc19be7f70&hwTime=6aca8555", provider: "shanxi_city", param: "5" },
    { number: 103, name: "朔州", url: "https://citymlive.sxrtv.com/live/sxszmlive.m3u8?hwSecret=9f793fd85452ea8887c7261fd714cbb4c4fdee3bf06eab652b0f37b73506a376&hwTime=6aca8555", provider: "shanxi_city", param: "6" },
    { number: 104, name: "晋城", url: "https://citymlive.sxrtv.com/live/sxjcmlive.m3u8?hwSecret=e986b1b987133c3b090c5fc674bc4bf9a02368fcf8a7217436d5fffacc7984fa&hwTime=6aca8555", provider: "shanxi_city", param: "7" },
    { number: 105, name: "长治", url: "https://citymlive.sxrtv.com/live/sxczmlive.m3u8?hwSecret=2827bc1af56bfcb23100b522c30faa462569186193569904d41f7caf55ae7bdc&hwTime=6aca8556", provider: "shanxi_city", param: "8" },
    { number: 106, name: "阳泉", url: "https://citymlive.sxrtv.com/live/sxyqmlive.m3u8?hwSecret=cf9c8e1768881ec14aeece1c657908d1f9b4666ee459b51de1818abbd7a83aec&hwTime=6aca8556", provider: "shanxi_city", param: "9" }
  ]
});

/* ---- 2) 取流解析器：带时效签名的台靠它现算新鲜地址 ----
 * 每个解析器注册成 window.__RESOLVERS.<provider>(param) -> Promise<m3u8>
 * 不想用解析器就整段删掉，播放时会退回上面的 url。
 */
/* ============================================================
 * 山西 省级 直播解析器  (window.__RESOLVERS.shanxi)   [tidePlayer]
 * 站点: https://www.sxrtv.com/tv/index.shtml
 * ------------------------------------------------------------
 * tidePlayer 算法 (来自 https://www.sxrtv.com/js/tidePlayer.js):
 *
 *  1) 取频道列表 (每次带时间戳签名的 token):
 *     t   = "/lsdream/336E7E6818120C00FA7E8129A9999A10/info.json"
 *     ms  = Date.now()
 *     GET https://livehhhttps.sxrtv.com + t
 *            + "?t=" + ms.toString(16) + "&token=" + md5(ms + t + "Dream")
 *     返回 { channels:[{n:名称, i:频道id, t:类型, r:[{t,n:码率}]}],
 *            play:{dl, ds, tk, dh, kk} }
 *
 *  2) 拼直播地址:
 *     jt(cid, dl, "live") 生成 path token (算法见下)
 *     地址 = https://livehhhttps.sxrtv.com/lsdream/<cid>/<码率>/<token>.m3u8
 *
 *  jt() 还原自 tidePlayer.js (旧key分支, C.oldkey 为假):
 *      token = ( x(c.toString(36)) + v.join("") ).substr(0, cid.length)
 *    x=s=>s.split('').reverse().join('')   y=ms=>new Date(ms).getDay()
 *    a = 当天 00:00 的时间戳(ms);  o = cid
 *    // 逐字符累加 charCode, 再加相邻差的和
 * ------------------------------------------------------------
 * 纯浏览器 JS: md5 自实现, 无 require。
 * ============================================================ */
(function (G) {
  'use strict';
  G.__RESOLVERS = G.__RESOLVERS || {};

  // ---------- 纯 JS MD5 ----------
  function md5(str) {
    function rl(n, c) { return (n << c) | (n >>> (32 - c)); }
    function au(x, y) { var l = (x & 0xFFFF) + (y & 0xFFFF); var m = (x >> 16) + (y >> 16) + (l >> 16); return (m << 16) | (l & 0xFFFF); }
    function cmn(q, a, b, x, s, t) { return au(rl(au(au(a, q), au(x, t)), s), b); }
    function ff(a, b, c, d, x, s, t) { return cmn((b & c) | (~b & d), a, b, x, s, t); }
    function gg(a, b, c, d, x, s, t) { return cmn((b & d) | (c & ~d), a, b, x, s, t); }
    function hh(a, b, c, d, x, s, t) { return cmn(b ^ c ^ d, a, b, x, s, t); }
    function ii(a, b, c, d, x, s, t) { return cmn(c ^ (b | ~d), a, b, x, s, t); }
    var utf8 = unescape(encodeURIComponent(str)), x = [], li;
    for (li = 0; li < utf8.length; li++) x.push(utf8.charCodeAt(li));
    var len = x.length;
    x.push(0x80);
    while (x.length % 64 !== 56) x.push(0);
    var bitlen = len * 8;
    for (li = 0; li < 8; li++) x.push((bitlen / Math.pow(2, li * 8)) & 0xFF);
    var a = 1732584193, b = -271733879, c = -1732584194, d = 271733878;
    for (var i = 0; i < x.length; i += 64) {
      var o = i, aa = a, bb = b, cc = c, dd = d, w = [], j;
      for (j = 0; j < 16; j++) w[j] = x[o + j * 4] | (x[o + j * 4 + 1] << 8) | (x[o + j * 4 + 2] << 16) | (x[o + j * 4 + 3] << 24);
      a = ff(a, b, c, d, w[0], 7, -680876936); d = ff(d, a, b, c, w[1], 12, -389564586); c = ff(c, d, a, b, w[2], 17, 606105819); b = ff(b, c, d, a, w[3], 22, -1044525330);
      a = ff(a, b, c, d, w[4], 7, -176418897); d = ff(d, a, b, c, w[5], 12, 1200080426); c = ff(c, d, a, b, w[6], 17, -1473231341); b = ff(b, c, d, a, w[7], 22, -45705983);
      a = ff(a, b, c, d, w[8], 7, 1770035416); d = ff(d, a, b, c, w[9], 12, -1958414417); c = ff(c, d, a, b, w[10], 17, -42063); b = ff(b, c, d, a, w[11], 22, -1990404162);
      a = ff(a, b, c, d, w[12], 7, 1804603682); d = ff(d, a, b, c, w[13], 12, -40341101); c = ff(c, d, a, b, w[14], 17, -1502002290); b = ff(b, c, d, a, w[15], 22, 1236535329);
      a = gg(a, b, c, d, w[1], 5, -165796510); d = gg(d, a, b, c, w[6], 9, -1069501632); c = gg(c, d, a, b, w[11], 14, 643717713); b = gg(b, c, d, a, w[0], 20, -373897302);
      a = gg(a, b, c, d, w[5], 5, -701558691); d = gg(d, a, b, c, w[10], 9, 38016083); c = gg(c, d, a, b, w[15], 14, -660478335); b = gg(b, c, d, a, w[4], 20, -405537848);
      a = gg(a, b, c, d, w[9], 5, 568446438); d = gg(d, a, b, c, w[14], 9, -1019803690); c = gg(c, d, a, b, w[3], 14, -187363961); b = gg(b, c, d, a, w[8], 20, 1163531501);
      a = gg(a, b, c, d, w[13], 5, -1444681467); d = gg(d, a, b, c, w[2], 9, -51403784); c = gg(c, d, a, b, w[7], 14, 1735328473); b = gg(b, c, d, a, w[12], 20, -1926607734);
      a = hh(a, b, c, d, w[5], 4, -378558); d = hh(d, a, b, c, w[8], 11, -2022574463); c = hh(c, d, a, b, w[11], 16, 1839030562); b = hh(b, c, d, a, w[14], 23, -35309556);
      a = hh(a, b, c, d, w[1], 4, -1530992060); d = hh(d, a, b, c, w[4], 11, 1272893353); c = hh(c, d, a, b, w[7], 16, -155497632); b = hh(b, c, d, a, w[10], 23, -1094730640);
      a = hh(a, b, c, d, w[13], 4, 681279174); d = hh(d, a, b, c, w[0], 11, -358537222); c = hh(c, d, a, b, w[3], 16, -722521979); b = hh(b, c, d, a, w[6], 23, 76029189);
      a = hh(a, b, c, d, w[9], 4, -640364487); d = hh(d, a, b, c, w[12], 11, -421815835); c = hh(c, d, a, b, w[15], 16, 530742520); b = hh(b, c, d, a, w[2], 23, -995338651);
      a = ii(a, b, c, d, w[0], 6, -198630844); d = ii(d, a, b, c, w[7], 10, 1126891415); c = ii(c, d, a, b, w[14], 15, -1416354905); b = ii(b, c, d, a, w[5], 21, -57434055);
      a = ii(a, b, c, d, w[12], 6, 1700485571); d = ii(d, a, b, c, w[3], 10, -1894986606); c = ii(c, d, a, b, w[10], 15, -1051523); b = ii(b, c, d, a, w[1], 21, -2054922799);
      a = ii(a, b, c, d, w[8], 6, 1873313359); d = ii(d, a, b, c, w[15], 10, -30611744); c = ii(c, d, a, b, w[6], 15, -1560198380); b = ii(b, c, d, a, w[13], 21, 1309151649);
      a = ii(a, b, c, d, w[4], 6, -145523070); d = ii(d, a, b, c, w[11], 10, -1120210379); c = ii(c, d, a, b, w[2], 15, 718787259); b = ii(b, c, d, a, w[9], 21, -343485551);
      a = au(a, aa); b = au(b, bb); c = au(c, cc); d = au(d, dd);
    }
    function hex(n) { var s = ''; for (var i2 = 0; i2 < 4; i2++) s += ('0' + ((n >> (i2 * 8)) & 0xFF).toString(16)).slice(-2); return s; }
    return hex(a) + hex(b) + hex(c) + hex(d);
  }

  // ---------- tidePlayer 的 jt() path-token 算法 ----------
  function x(t) { return t.split('').reverse().join(''); }
  function y(t) { return new Date(t).getDay(); }

  function jt(cid, t, e) {
    var o = cid;
    if (!t) return e || o;
    var now = new Date();
    var a = new Date(now.getFullYear(), now.getMonth(), now.getDate()).getTime(); // 当天00:00
    var r = 0, d = 0, b = -1, gg2 = 0;
    for (r = 0; r < o.length; r++) { var _ = o.charCodeAt(r); d += _; if (b != -1) gg2 += b - _; b = _; }
    d += gg2;
    var l = d.toString(36);
    var p = a.toString(36);
    var s = 0;
    for (r = 0; r < p.length; r++) s += p.charCodeAt(r);
    p = p.substr(5) + p.substr(0, 5);
    var w, m, c = Math.abs(s - d);
    var u = (p = x(l) + p).substr(0, 4);
    var h = p.substr(4);
    var v = [];
    var f = y(a) % 2;
    for (r = 0; r < o.length; r++) {
      if (r % 2 == f) v.push(p.charAt(r % p.length));
      else {
        w = o.charAt(r - 1);
        if (w) { m = u.indexOf(w); if (m == -1) v.push(w); else v.push(h.charAt(m)); }
        else v.push(u.charAt(r));
      }
    }
    return (x(c.toString(36)) + v.join('')).substr(0, o.length);
  }

  // ---------- 站点逻辑 ----------
  var BASE = 'https://livehhhttps.sxrtv.com';
  var INFO = '/lsdream/336E7E6818120C00FA7E8129A9999A10/info.json';

  // 省级 6 个 (来自 https://www.sxrtv.com/tv/index.shtml .channelstab li[type=1])
  var CHANNELS = [
    { key: 'q8RVWgs', name: '山西卫视' },
    { key: 'lce1mC4', name: '黄河电视台' },
    { key: '4j01KWX', name: '山西经济与科技' },
    { key: 'Md571Kv', name: '山西影视' },
    { key: 'p4y5do9', name: '山西社会与法治' },
    { key: 'agmpyEk', name: '山西文体生活' },
  ];
  var ALIAS = {
    '黄河': 'lce1mC4', '山西经济与科技频道': '4j01KWX', '经济科技': '4j01KWX',
    '影视': 'Md571Kv', '社会与法制': 'p4y5do9', '社会与法治': 'p4y5do9', '文体生活': 'agmpyEk',
  };

  function pickKey(ch) {
    if (ch == null) return null;
    for (var i = 0; i < CHANNELS.length; i++) if (CHANNELS[i].key === ch || CHANNELS[i].name === ch) return CHANNELS[i].key;
    if (ALIAS[ch]) return ALIAS[ch];
    for (var j = 0; j < CHANNELS.length; j++) if (ch.indexOf(CHANNELS[j].name) >= 0 || CHANNELS[j].name.indexOf(ch) >= 0) return CHANNELS[j].key;
    return null;
  }

  function fetchInfo() {
    var ms = Date.now();
    var url = BASE + INFO + '?t=' + ms.toString(16) + '&token=' + md5(ms + INFO + 'Dream');
    return fetch(url, { headers: { 'Referer': 'https://www.sxrtv.com/' }, cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j.error) throw new Error('山西省级：info.json ' + j.error);
        if (!j.channels) throw new Error('山西省级：info.json 无 channels');
        return j;
      });
  }

  function buildUrl(cid, quality, dl) {
    var token = jt(cid, dl, 'live');
    var q = quality ? quality + '/' : '';
    return BASE + '/lsdream/' + cid + '/' + q + token + '.m3u8';
  }

  function resolveAll() {
    return fetchInfo().then(function (j) {
      var dl = j.play && j.play.dl;
      var out = [];
      (j.channels || []).forEach(function (c) {
        if (c.t == '1') out.push({ key: c.i, name: c.n, url: buildUrl(c.i, c.r && c.r[0] ? c.r[0].n : '', dl) });
      });
      return out;
    });
  }

  function resolve(channel) {
    var key = pickKey(channel) || channel;
    return fetchInfo().then(function (j) {
      var dl = j.play && j.play.dl;
      var hit = null;
      (j.channels || []).forEach(function (c) { if (c.i === key) hit = c; });
      if (!hit) (j.channels || []).forEach(function (c) { if (!hit && c.n === channel) hit = c; });
      if (!hit) throw new Error('山西省级：找不到频道 [' + channel + ']');
      var quality = hit.r && hit.r[0] ? hit.r[0].n : '';
      return buildUrl(hit.i, quality, dl);
    });
  }

  G.__RESOLVERS.shanxi = {
    name: '山西省级',
    site: 'https://www.sxrtv.com/tv/index.shtml',
    channels: CHANNELS,
    md5: md5,
    jt: jt,
    resolve: resolve,
    resolveAll: resolveAll,
  };
})(typeof window !== 'undefined' ? window : this);

/* ============================================================
 * 山西 市级 直播解析器  (window.__RESOLVERS.shanxi_city)  [华为云签名]
 * 站点: https://www.sxrtv.com/tv/index.shtml  (地市频道 swiper)
 * ------------------------------------------------------------
 * 原理:
 *   页面地市频道 li[type=2] 带 data-itemid，点击后:
 *     GET https://dyhhplus.sxrtv.com/tapi/custom/huawei_live_secret.jsp?itemId=<id>
 *     返回 {"code":200,"data":{"address":"https://citymlive.sxrtv.com/live/<code>.m3u8?hwSecret=..&hwTime=.."}}
 *   该 address 是华为云签名的时移地址(~1小时有效期)，直接拿去播放。
 * ------------------------------------------------------------
 * itemId 对照表 (抓自页面 swiper-city .channel-item):
 *   吕梁=1 临汾=2 忻州=3 运城=4 晋中=5 朔州=6 晋城=7 长治=8 阳泉=9 太原=11
 * ============================================================ */
(function (G) {
  'use strict';
  G.__RESOLVERS = G.__RESOLVERS || {};

  var API = 'https://dyhhplus.sxrtv.com/tapi/custom/huawei_live_secret.jsp?itemId=';

  var CHANNELS = [
    { name: '吕梁', itemId: 1, code: 'sxllmlive' },
    { name: '临汾', itemId: 2, code: 'sxlfmlive' },
    { name: '忻州', itemId: 3, code: 'sxxzmlive' },
    { name: '运城', itemId: 4, code: 'sxycmlive' },
    { name: '晋中', itemId: 5, code: 'sxjzmlive' },
    { name: '朔州', itemId: 6, code: 'sxszmlive' },
    { name: '晋城', itemId: 7, code: 'sxjcmlive' },
    { name: '长治', itemId: 8, code: 'sxczmlive' },
    { name: '阳泉', itemId: 9, code: 'sxyqmlive' },
    { name: '太原', itemId: 11, code: 'sxtymlive' },
  ];
  var ALIAS = {
    '吕梁综合': '吕梁', '吕梁-1': '吕梁', '临汾-1': '临汾', '忻州综合': '忻州',
    '运城-1': '运城', '晋中综合': '晋中', '朔州-1': '朔州', '晋城新闻综合': '晋城',
    '长治-1': '长治', '阳泉新闻综合': '阳泉', '太原-1': '太原',
  };

  function pick(ch) {
    if (ch == null) return null;
    if (ALIAS[ch]) ch = ALIAS[ch];
    for (var i = 0; i < CHANNELS.length; i++) if (CHANNELS[i].name === ch || String(CHANNELS[i].itemId) === String(ch)) return CHANNELS[i];
    for (var j = 0; j < CHANNELS.length; j++) if (ch.indexOf(CHANNELS[j].name) >= 0) return CHANNELS[j];
    return null;
  }

  function fetchSecret(itemId) {
    return fetch(API + itemId, { headers: { 'Referer': 'https://www.sxrtv.com/' }, cache: 'no-store' })
      .then(function (r) { return r.json(); })
      .then(function (j) {
        if (j.code !== 200 || !j.data || !j.data.address) throw new Error('山西市级：itemId=' + itemId + ' 无 address (' + (j.message || j.code) + ')');
        return j.data.address;
      });
  }

  function resolve(channel) {
    var c = pick(channel);
    if (!c) return Promise.reject(new Error('山西市级：未知频道 [' + channel + ']'));
    return fetchSecret(c.itemId);
  }

  function resolveAll() {
    return Promise.all(CHANNELS.map(function (c) {
      return fetchSecret(c.itemId).then(function (url) { return { name: c.name, itemId: c.itemId, url: url }; })
        .catch(function (e) { return { name: c.name, itemId: c.itemId, error: e.message }; });
    }));
  }

  G.__RESOLVERS.shanxi_city = {
    name: '山西市级',
    site: 'https://www.sxrtv.com/tv/index.shtml',
    channels: CHANNELS,
    resolve: resolve,
    resolveAll: resolveAll,
  };
})(typeof window !== 'undefined' ? window : this);
