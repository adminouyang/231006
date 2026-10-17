/* ============================================================
 * 江西    key: jiangxi
 * ------------------------------------------------------------
 * 来源站点：https://www.jxntv.cn/live/
 * 取流方式：token 换址（含共用 md5）
 * 频道数：8      最后更新：2026-10-16
 *
 * 本文件是 TVLive 的「江西」分组订阅文件，可直接手工修改后重新上传。
 * 改完记得同步 index.json 里本文件的 sha256（不想校验就写空字符串）。
 * ============================================================ */

/* ---- 1) 频道表：TVLive 启动时会读走这一段 ----
 * name      显示名（分组标题已写省份，这里不用再重复前缀）
 * url       兜底直连地址；带时效签名的台靠下面解析器现算，这里填旧的没关系
 * provider  解析器名，对应下面第 2 段里注册的名字；不需要就整行删掉
 * param     传给解析器的参数，一般是流名或频道 id
 */
TVRemote.define({
  key: "jiangxi",
  group: "江西",
  updated: "2026-10-16",
  note: "先换 token 再拼地址",
  list: [
    { number: 187, name: "江西卫视", url: "https://yun-live.jxtvcn.com.cn/live-jxtv/tv_jxtv1.m3u8?source=pc&t=179165117311685&token=f10ae7119a2b9425855073c235394b83&uuid=0120660c001c", provider: "jiangxi", param: "tv_jxtv1.m3u8" },
    { number: 188, name: "都市频道", url: "https://yun-live.jxtvcn.com.cn/live-jxtv/tv_jxtv2.m3u8?source=pc&t=179165117311685&token=f10ae7119a2b9425855073c235394b83&uuid=0120660c001c", provider: "jiangxi", param: "tv_jxtv2.m3u8" },
    { number: 189, name: "经济生活频道", url: "https://yun-live.jxtvcn.com.cn/live-jxtv/tv_jxtv3_hd.m3u8?source=pc&t=179165117311685&token=f10ae7119a2b9425855073c235394b83&uuid=0120660c001c", provider: "jiangxi", param: "tv_jxtv3_hd.m3u8" },
    { number: 190, name: "公共·农业频道", url: "https://yun-live.jxtvcn.com.cn/live-jxtv/tv_jxtv5.m3u8?source=pc&t=179165117311685&token=f10ae7119a2b9425855073c235394b83&uuid=0120660c001c", provider: "jiangxi", param: "tv_jxtv5.m3u8" },
    { number: 191, name: "少儿频道", url: "https://yun-live.jxtvcn.com.cn/live-jxtv/tv_jxtv6.m3u8?source=pc&t=179165117311685&token=f10ae7119a2b9425855073c235394b83&uuid=0120660c001c", provider: "jiangxi", param: "tv_jxtv6.m3u8" },
    { number: 192, name: "新闻频道", url: "https://yun-live.jxtvcn.com.cn/live-jxtv/tv_jxtv7.m3u8?source=pc&t=179165117311685&token=f10ae7119a2b9425855073c235394b83&uuid=0120660c001c", provider: "jiangxi", param: "tv_jxtv7.m3u8" },
    { number: 193, name: "移动电视频道", url: "https://yun-live.jxtvcn.com.cn/live-jxtv/tv_jxtv8.m3u8?source=pc&t=179165117311685&token=f10ae7119a2b9425855073c235394b83&uuid=0120660c001c", provider: "jiangxi", param: "tv_jxtv8.m3u8" },
    { number: 194, name: "陶瓷频道", url: "https://yun-live.jxtvcn.com.cn/live-jxtv/tv_taoci.m3u8?source=pc&t=179165117311685&token=f10ae7119a2b9425855073c235394b83&uuid=0120660c001c", provider: "jiangxi", param: "tv_taoci.m3u8" }
  ]
});

/* ---- 2) 取流解析器：带时效签名的台靠它现算新鲜地址 ----
 * 每个解析器注册成 window.__RESOLVERS.<provider>(param) -> Promise<m3u8>
 * 不想用解析器就整段删掉，播放时会退回上面的 url。
 */
(function (G) {
  'use strict';
  G.__RESOLVERS = G.__RESOLVERS || {};

  /* ---------- 极简 md5（纯 JS，无依赖） ---------- */
  function md5(str) {
    function rl(n, c) { return (n << c) | (n >>> (32 - c)); }
    function au(x, y) { var l = (x & 0xFFFF) + (y & 0xFFFF); return (((x >> 16) + (y >> 16) + (l >> 16)) << 16) | (l & 0xFFFF); }
    function cmn(q, a, b, x, s, t) { return au(rl(au(au(a, q), au(x, t)), s), b); }
    function ff(a, b, c, d, x, s, t) { return cmn((b & c) | (~b & d), a, b, x, s, t); }
    function gg(a, b, c, d, x, s, t) { return cmn((b & d) | (c & ~d), a, b, x, s, t); }
    function hh(a, b, c, d, x, s, t) { return cmn(b ^ c ^ d, a, b, x, s, t); }
    function ii(a, b, c, d, x, s, t) { return cmn(c ^ (b | ~d), a, b, x, s, t); }
    function blk(s) {
      var i, n = ((s.length + 8) >> 6) + 1, blks = new Array(n * 16), o = 0;
      for (i = 0; i < n * 16; i++) blks[i] = 0;
      for (i = 0; i < s.length; i++) blks[(i >> 2)] |= s.charCodeAt(i) << ((i % 4) * 8);
      blks[s.length >> 2] |= 0x80 << ((s.length % 4) * 8);
      blks[n * 16 - 2] = s.length * 8;
      return blks;
    }
    var x = blk(unescape(encodeURIComponent(str))), a = 1732584193, b = -271733879,
      c = -1732584194, d = 271733878, i;
    for (i = 0; i < x.length; i += 16) {
      var oa = a, ob = b, oc = c, od = d;
      a = ff(a, b, c, d, x[i], 7, -680876936); d = ff(d, a, b, c, x[i + 1], 12, -389564586);
      c = ff(c, d, a, b, x[i + 2], 17, 606105819); b = ff(b, c, d, a, x[i + 3], 22, -1044525330);
      a = ff(a, b, c, d, x[i + 4], 7, -176418897); d = ff(d, a, b, c, x[i + 5], 12, 1200080426);
      c = ff(c, d, a, b, x[i + 6], 17, -1473231341); b = ff(b, c, d, a, x[i + 7], 22, -45705983);
      a = ff(a, b, c, d, x[i + 8], 7, 1770035416); d = ff(d, a, b, c, x[i + 9], 12, -1958414417);
      c = ff(c, d, a, b, x[i + 10], 17, -42063); b = ff(b, c, d, a, x[i + 11], 22, -1990404162);
      a = ff(a, b, c, d, x[i + 12], 7, 1804603682); d = ff(d, a, b, c, x[i + 13], 12, -40341101);
      c = ff(c, d, a, b, x[i + 14], 17, -1502002290); b = ff(b, c, d, a, x[i + 15], 22, 1236535329);
      a = gg(a, b, c, d, x[i + 1], 5, -165796510); d = gg(d, a, b, c, x[i + 6], 9, -1069501632);
      c = gg(c, d, a, b, x[i + 11], 14, 643717713); b = gg(b, c, d, a, x[i], 20, -373897302);
      a = gg(a, b, c, d, x[i + 5], 5, -701558691); d = gg(d, a, b, c, x[i + 10], 9, 38016083);
      c = gg(c, d, a, b, x[i + 15], 14, -660478335); b = gg(b, c, d, a, x[i + 4], 20, -405537848);
      a = gg(a, b, c, d, x[i + 9], 5, 568446438); d = gg(d, a, b, c, x[i + 14], 9, -1019803690);
      c = gg(c, d, a, b, x[i + 3], 14, -187363961); b = gg(b, c, d, a, x[i + 8], 20, 1163531501);
      a = gg(a, b, c, d, x[i + 13], 5, -1444681467); d = gg(d, a, b, c, x[i + 2], 9, -51403784);
      c = gg(c, d, a, b, x[i + 7], 14, 1735328473); b = gg(b, c, d, a, x[i + 12], 20, -1926607734);
      a = hh(a, b, c, d, x[i + 5], 4, -378558); d = hh(d, a, b, c, x[i + 8], 11, -2022574463);
      c = hh(c, d, a, b, x[i + 11], 16, 1839030562); b = hh(b, c, d, a, x[i + 14], 23, -35309556);
      a = hh(a, b, c, d, x[i + 1], 4, -1530992060); d = hh(d, a, b, c, x[i + 4], 11, 1272893353);
      c = hh(c, d, a, b, x[i + 7], 16, -155497632); b = hh(b, c, d, a, x[i + 10], 23, -1094730640);
      a = hh(a, b, c, d, x[i + 13], 4, 681279174); d = hh(d, a, b, c, x[i], 11, -358537222);
      c = hh(c, d, a, b, x[i + 3], 16, -722521979); b = hh(b, c, d, a, x[i + 6], 23, 76029189);
      a = hh(a, b, c, d, x[i + 9], 4, -640364487); d = hh(d, a, b, c, x[i + 12], 11, -421815835);
      c = hh(c, d, a, b, x[i + 15], 16, 530742520); b = hh(b, c, d, a, x[i + 2], 23, -995338651);
      a = ii(a, b, c, d, x[i], 6, -198630844); d = ii(d, a, b, c, x[i + 7], 10, 1126891415);
      c = ii(c, d, a, b, x[i + 14], 15, -1416354905); b = ii(b, c, d, a, x[i + 5], 21, -57434055);
      a = ii(a, b, c, d, x[i + 12], 6, 1700485571); d = ii(d, a, b, c, x[i + 3], 10, -1894986606);
      c = ii(c, d, a, b, x[i + 10], 15, -1051523); b = ii(b, c, d, a, x[i + 1], 21, -2054922799);
      a = ii(a, b, c, d, x[i + 8], 6, 1873313359); d = ii(d, a, b, c, x[i + 15], 10, -30611744);
      c = ii(c, d, a, b, x[i + 6], 15, -1560198380); b = ii(b, c, d, a, x[i + 13], 21, 1309151649);
      a = ii(a, b, c, d, x[i + 4], 6, -145523070); d = ii(d, a, b, c, x[i + 11], 10, -1120210379);
      c = ii(c, d, a, b, x[i + 2], 15, 718787259); b = ii(b, c, d, a, x[i + 9], 21, -343485551);
      a = au(a, oa); b = au(b, ob); c = au(c, oc); d = au(d, od);
    }
    return hex(a) + hex(b) + hex(c) + hex(d);
    function hex(n) {
      var s = '', j;
      for (j = 0; j < 4; j++) s += ('0' + ((n >> (j * 8)) & 0xFF).toString(16)).slice(-2);
      return s;
    }
  }

  G.__RESOLVERS._md5 = md5;


/* ================= 江西（先换 token 再拼地址） ================= */
  (function () {
    var SALT = 'gXmNaQROStYfd';
    var UUID = '0120660c001c';
    var ALPHA = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678oOLl9gqVvUuI1';

    function tag() {
      var s = '', i;
      for (i = 0; i < 8; i++) s += ALPHA.charAt(Math.floor(Math.random() * ALPHA.length));
      return s;
    }

    function resolve(param) {
      var stream = String(param || '').trim();
      if (!stream) return Promise.reject(new Error('jiangxi: 缺少流名'));
      var t = Math.floor(Date.now() / 1000);
      var etag = tag();
      var auth = md5(t + stream + etag + SALT);
      return fetch('https://cdnauth.jxgdw.com/liveauth/pc', {
        method: 'POST',
        cache: 'no-store',
        referrer: 'https://www.jxntv.cn/',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': auth,
          'etag': etag
        },
        body: JSON.stringify({ t: t, stream: stream, uuid: UUID })
      })
        .then(function (r) { return r.json(); })
        .then(function (j) {
          if (!j || !j.token) throw new Error('jiangxi: 鉴权接口没给 token');
          return 'https://yun-live.jxtvcn.com.cn/live-jxtv/' + stream
            + '?source=pc&t=' + j.t + '&token=' + j.token + '&uuid=' + UUID;
        });
    }
    resolve.resolve = resolve;
    resolve.displayName = '江西(赣云)';
    resolve.site = 'https://www.jxntv.cn/live/';
    G.__RESOLVERS.jiangxi = resolve;
  })();

})(typeof window !== 'undefined' ? window : this);
