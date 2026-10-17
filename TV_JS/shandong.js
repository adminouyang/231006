/* ============================================================
 * 山东    key: shandong
 * ------------------------------------------------------------
 * 来源站点：http://v.iqilu.com/  +  http://www.qtv.com.cn/
 * 取流方式：齐鲁云签名
 * 频道数：9      最后更新：2026-10-16
 *
 * 本文件是 TVLive 的「山东」分组订阅文件，可直接手工修改后重新上传。
 * 改完记得同步 index.json 里本文件的 sha256（不想校验就写空字符串）。
 * ============================================================ */

/* ---- 1) 频道表：TVLive 启动时会读走这一段 ----
 * name      显示名（分组标题已写省份，这里不用再重复前缀）
 * url       兜底直连地址；带时效签名的台靠下面解析器现算，这里填旧的没关系
 * provider  解析器名，对应下面第 2 段里注册的名字；不需要就整行删掉
 * param     传给解析器的参数，一般是流名或频道 id
 */
TVRemote.define({
  key: "shandong",
  group: "山东",
  updated: "2026-10-16",
  note: "齐鲁云 AES-128-CBC + md5 签名",
  list: [
    { number: 162, name: "山东卫视", url: "https://tstreamlive302.iqilu.com/21/cb1628e9b65a4cfd985b1760809696ee/playlist.m3u8?k=8b4b1e6dd71f27914090a788ab8b326a&t=1791686266", provider: "iqilu", param: "sdws" },
    { number: 163, name: "齐鲁频道", url: "https://tstreamlive302.iqilu.com/291/5de861e29cdd4f9589327c8dd783172a/playlist.m3u8?k=f1f9b2647b59c2ac85286d0ad9336ee9&t=1791686267", provider: "iqilu", param: "ql" },
    { number: 164, name: "新闻频道", url: "https://streamlive302.iqilu.com/21/ae3cd441fafb45f29168af2a3bf8e116/playlist.m3u8?n=736841d0314968b7face24cd0372b417&m=1791686267", provider: "iqilu", param: "xw" },
    { number: 165, name: "体育休闲频道", url: "https://tstreamlive302.iqilu.com/291/d9c0aba79a944b41a7f4f1ac422d9808/playlist.m3u8?k=9f0d510fd8e6545d94acc7685f233f63&t=1791686267", provider: "iqilu", param: "ty" },
    { number: 166, name: "生活频道", url: "https://tstreamlive302.iqilu.com/291/6e9efb8f95a543db8246f1cf06ba960b/playlist.m3u8?k=59452a45dbe9b15d44c835c0b290de58&t=1791686268", provider: "iqilu", param: "sh" },
    { number: 167, name: "综艺频道", url: "https://tstreamlive302.iqilu.com/291/dad8e4743fcf48ed925d01e64868cc7c/playlist.m3u8?k=72fb7727d9cd976625887306e6d694ea&t=1791686268", provider: "iqilu", param: "zy" },
    { number: 168, name: "农科频道", url: "https://tstreamlive302.iqilu.com/291/9664dd18b42b4b129a71fbfb68a80e3b/playlist.m3u8?k=da2091720eba9a72e25c49b19d8b40be&t=1791686268", provider: "iqilu", param: "nk" },
    { number: 169, name: "文旅频道", url: "https://tstreamlive302.iqilu.com/291/71637943d1f841c78edd6abfa120bee2/playlist.m3u8?k=6ecc4503c6a93754cc6308531d42d91d&t=1791686269", provider: "iqilu", param: "wl" },
    { number: 170, name: "少儿频道", url: "https://tstreamlive302.iqilu.com/21/990de3c3748848848daf5a96743f9c57/playlist.m3u8?k=0583d34a9dc975acbcd6beb5cade49a0&t=1791686269", provider: "iqilu", param: "se" }
  ]
});

/* ---- 2) 取流解析器：带时效签名的台靠它现算新鲜地址 ----
 * 每个解析器注册成 window.__RESOLVERS.<provider>(param) -> Promise<m3u8>
 * 不想用解析器就整段删掉，播放时会退回上面的 url。
 */
/* ============================================================
 * 山东 iqilu.com 直播解析器   window.__RESOLVERS.iqilu(param)
 * 站点: http://v.iqilu.com/   流: https://tstreamlive302.iqilu.com/...
 * ------------------------------------------------------------
 * 链路（全部实测）:
 *   1) channelMark 来自播放页 JS 里的全局变量 _pdCid
 *      (页面 http://v.iqilu.com/ 用 _pdCid 作为 channelMark 调刷新接口)。
 *      9 个频道的 mark 见下表 CHANNELS，均已实测返回可播流。
 *   2) 刷新接口:
 *        t = Date.now()                              (毫秒)
 *        s = md5(mark + t + "QZMVKTRHPLXADJNE")
 *        POST https://feiying.litenews.cn/api/v1/auth/exchange?t=<t>&s=<s>
 *        body = base64( AES-128-CBC( JSON{"channelMark":mark}, key, iv ) )
 *               key = "BWRFYSNCOGIXUTPA"   (16B)
 *               iv  = "0000000000000000"   (16B)
 *        Content-Type: text/plain
 *   3) 响应体也是 AES-128-CBC 同一 key/iv 加密，base64；
 *      解密后 JSON: { "code":1, "data":"https://tstreamlive302.iqilu.com/<id>/<hash>/playlist.m3u8?k=..&t=.." }
 *      取 .data 即为当次可播 m3u8（k/t 为下发签名，约 2 小时有效）。
 * ------------------------------------------------------------
 * 纯浏览器 JS: md5 自实现；AES 用 WebCrypto(crypto.subtle)，无 require。
 * param: 下表 key / 中文名 / channelMark 数字串 三者任一。
 * ============================================================ */
(function (G) {
  'use strict';
  G.__RESOLVERS = G.__RESOLVERS || {};

  // ---------------- 纯 JS MD5 ----------------
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

  // ---------------- 常量 ----------------
  var KEY_STR = 'BWRFYSNCOGIXUTPA';
  var IV_STR = '0000000000000000';
  var MXPX = 'QZMVKTRHPLXADJNE';
  var BASE = 'https://feiying.litenews.cn/api/v1/auth/exchange';

  // 频道表: key / 中文名 / channelMark
  var CHANNELS = [
    { key: 'sdws', name: '山东卫视', mark: '24581' },
    { key: 'ql', name: '齐鲁频道', mark: '24584' },
    { key: 'xw', name: '新闻频道', mark: '24602' },
    { key: 'ty', name: '体育休闲', mark: '24587' },
    { key: 'sh', name: '生活', mark: '24596' },
    { key: 'zy', name: '综艺', mark: '24593' },
    { key: 'nk', name: '农科', mark: '24599' },
    { key: 'wl', name: '文旅', mark: '24590' },
    { key: 'se', name: '少儿', mark: '24605' }
  ];
  var ALIAS = {
    '山东卫视': 'sdws', '齐鲁': 'ql', '齐鲁频道': 'ql', '山东齐鲁': 'ql',
    '新闻': 'xw', '新闻频道': 'xw', '山东新闻': 'xw',
    '体育休闲频道': 'ty', '体育': 'ty', '体育休闲': 'ty',
    '生活频道': 'sh', '综艺频道': 'zy', '农科频道': 'nk',
    '文旅频道': 'wl', '少儿频道': 'se', '山东少儿': 'se'
  };

  function pick(param) {
    if (param == null) return null;
    var p = String(param).trim();
    for (var i = 0; i < CHANNELS.length; i++) if (CHANNELS[i].key === p || CHANNELS[i].name === p) return CHANNELS[i];
    if (ALIAS[p]) { for (var k = 0; k < CHANNELS.length; k++) if (CHANNELS[k].key === ALIAS[p]) return CHANNELS[k]; }
    if (/^\d+$/.test(p)) return { key: p, name: p, mark: p };      // 直接给 channelMark
    for (var j = 0; j < CHANNELS.length; j++) if (p.indexOf(CHANNELS[j].name) >= 0 || CHANNELS[j].name.indexOf(p) >= 0) return CHANNELS[j];
    return null;
  }

  // ---------------- AES-128-CBC (WebCrypto, PKCS#7) ----------------
  function strBuf(s) { return new TextEncoder().encode(s); }
  function abToB64(ab) { var b = new Uint8Array(ab), s = ''; for (var i = 0; i < b.length; i++) s += String.fromCharCode(b[i]); return btoa(s); }
  function b64ToAb(b64) { var s = atob(b64), b = new Uint8Array(s.length); for (var i = 0; i < s.length; i++) b[i] = s.charCodeAt(i); return b; }
  function keyPromise() {
    if (!keyPromise._p) keyPromise._p = crypto.subtle.importKey('raw', strBuf(KEY_STR), { name: 'AES-CBC' }, false, ['encrypt', 'decrypt']);
    return keyPromise._p;
  }
  function aesEnc(plain) {
    return keyPromise().then(function (k) {
      return crypto.subtle.encrypt({ name: 'AES-CBC', iv: strBuf(IV_STR) }, k, strBuf(plain));
    }).then(abToB64);
  }
  function aesDec(b64) {
    return keyPromise().then(function (k) {
      return crypto.subtle.decrypt({ name: 'AES-CBC', iv: strBuf(IV_STR) }, k, b64ToAb(b64));
    }).then(function (pt) { return new TextDecoder().decode(pt); });
  }

  // 刷新接口对 Referer 有要求(必须含 v.iqilu.com)。
  // 浏览器里 Referer 属受限头，故按“可用的方式”依次重试:
  //   1) 直接写 Referer 头   (WebView/Node 等允许自定义头的环境)
  //   2) fetch 的 referrer 选项 (部分环境/策略下可带出)
  //   3) 都不行时报明确错误
  function postExchange(url, body) {
    var variants = [
      { headers: { 'Content-Type': 'text/plain', 'Referer': 'https://v.iqilu.com/' } },
      { headers: { 'Content-Type': 'text/plain' }, referrer: 'https://v.iqilu.com/', referrerPolicy: 'unsafe-url' },
      { headers: { 'Content-Type': 'text/plain' }, referrer: 'http://v.iqilu.com/' },
      { headers: { 'Content-Type': 'text/plain' } }
    ];
    var i = 0;
    function next() {
      if (i >= variants.length) return Promise.reject(new Error('iqilu: 刷新接口 403（Referer 被浏览器拦截）'));
      var opt = variants[i++];
      return fetch(url, Object.assign({ method: 'POST', body: body, cache: 'no-store' }, opt)).then(function (r) {
        if (r.status === 403) return next();
        return r;
      });
    }
    return next();
  }

  // ---------------- 解析 ----------------
  function resolve(param) {
    var ch = pick(param);
    if (!ch || !ch.mark) return Promise.reject(new Error('iqilu: 未知频道参数 ' + param));
    var t = Date.now();
    var s = md5(ch.mark + t + MXPX);
    var url = BASE + '?t=' + t + '&s=' + s;
    return aesEnc(JSON.stringify({ channelMark: ch.mark }))
      .then(function (body) { return postExchange(url, body); })
      .then(function (r) {
        if (!r.ok) throw new Error('iqilu: 刷新接口 HTTP ' + r.status);
        return r.text();
      })
      .then(function (txt) {
        return aesDec(txt);
      })
      .then(function (plain) {
        var j = JSON.parse(plain);
        if (!j || !j.data) throw new Error('iqilu: 响应无 data (code=' + (j && j.code) + ')');
        return j.data;                       // 当次可播 m3u8
      });
  }

  // 兼容两种调用: res('sdws') 以及 res.resolve('sdws') / res.resolveAll()
  resolve.resolve = resolve;
  resolve.md5 = md5;
  resolve.displayName = '山东(齐鲁网)';
  resolve.site = 'http://v.iqilu.com/';
  resolve.channels = CHANNELS;
  resolve.pick = pick;

  G.__RESOLVERS.iqilu = resolve;
})(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : this));
