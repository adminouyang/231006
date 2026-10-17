/* ============================================================
 * 陕西    key: shaanxi
 * ------------------------------------------------------------
 * 来源站点：http://live.snrtv.com/
 * 取流方式：AES 解密
 * 频道数：8      最后更新：2026-10-16
 *
 * 本文件是 TVLive 的「陕西」分组订阅文件，可直接手工修改后重新上传。
 * 改完记得同步 index.json 里本文件的 sha256（不想校验就写空字符串）。
 * ============================================================ */

/* ---- 1) 频道表：TVLive 启动时会读走这一段 ----
 * name      显示名（分组标题已写省份，这里不用再重复前缀）
 * url       兜底直连地址；带时效签名的台靠下面解析器现算，这里填旧的没关系
 * provider  解析器名，对应下面第 2 段里注册的名字；不需要就整行删掉
 * param     传给解析器的参数，一般是流名或频道 id
 */
TVRemote.define({
  key: "shaanxi",
  group: "陕西",
  updated: "2026-10-16",
  note: "AES-128-CBC ZeroPadding 解密",
  list: [
    { number: 179, name: "陕西卫视", url: "http://stream.snrtv.com/sxbc-star-muADFU.m3u8", provider: "shaanxi", param: "star" },
    { number: 180, name: "新闻资讯", url: "http://stream.snrtv.com/sxbc-1-acdpQ8.m3u8", provider: "shaanxi", param: "1" },
    { number: 181, name: "都市青春", url: "http://stream.snrtv.com/sxbc-2-hEST13.m3u8", provider: "shaanxi", param: "2" },
    { number: 182, name: "银龄频道", url: "http://stream.snrtv.com/sxbc-3-lBTWX8.m3u8", provider: "shaanxi", param: "3" },
    { number: 183, name: "秦腔频道", url: "http://stream.snrtv.com/sxbc-5-cmprt6.m3u8", provider: "shaanxi", param: "5" },
    { number: 184, name: "体育休闲", url: "http://stream.snrtv.com/sxbc-7-cqsvF6.m3u8", provider: "shaanxi", param: "7" },
    { number: 185, name: "农林卫视", url: "http://stream.snrtv.com/sxbc-nl-aequE5.m3u8", provider: "shaanxi", param: "nl" },
    { number: 186, name: "移动电视", url: "http://stream.snrtv.com/sxbc-yd-dfhksT.m3u8", provider: "shaanxi", param: "11" }
  ]
});

/* ---- 2) 取流解析器：带时效签名的台靠它现算新鲜地址 ----
 * 每个解析器注册成 window.__RESOLVERS.<provider>(param) -> Promise<m3u8>
 * 不想用解析器就整段删掉，播放时会退回上面的 url。
 */
/* ============================================================
 * 陕西 直播解析器  (window.__RESOLVERS.shaanxi)
 * 站点: http://live.snrtv.com/
 * ------------------------------------------------------------
 * 原理:
 *   页面脚本 http://res.cnwest.com/.../snrtv2020/js/dress.js 定义:
 *     function Undress(k,iv,c){ return CryptoJS.AES.decrypt(c,
 *         CryptoJS.enc.Utf8.parse(k),
 *         {iv:CryptoJS.enc.Utf8.parse(iv), mode:CBC, padding:ZeroPadding}
 *       ).toString(CryptoJS.enc.Utf8); }
 *     mapTV = JSON.parse(Undress(sTV[0:16], sRadio[0:16], sTV[16:]))
 *   sTV / sRadio 是 http://toutiao.cnwest.com/static/v1/group/stream.js
 *   里的两个长 base64 变量 (sTV 前16字符当 key, sRadio 前16当 iv)。
 *   解密后 mapTV.sxbc[标识].m3u8 即当前可播地址。
 *   地址带动态 token(形如 sxbc-star-besLR4.m3u8)，会周期刷新，
 *   所以必须每次实时抓取 stream.js 再解密，不能写死。
 * ------------------------------------------------------------
 * 纯浏览器 JS：AES-128-CBC 自实现，无 require，无 crypto.subtle 依赖。
 * ============================================================ */
(function (G) {
  'use strict';
  G.__RESOLVERS = G.__RESOLVERS || {};

  // ---------- AES-128-CBC 解密 (ZeroPadding / 无填充) ----------
  var Sbox = [
    0x63, 0x7c, 0x77, 0x7b, 0xf2, 0x6b, 0x6f, 0xc5, 0x30, 0x01, 0x67, 0x2b, 0xfe, 0xd7, 0xab, 0x76,
    0xca, 0x82, 0xc9, 0x7d, 0xfa, 0x59, 0x47, 0xf0, 0xad, 0xd4, 0xa2, 0xaf, 0x9c, 0xa4, 0x72, 0xc0,
    0xb7, 0xfd, 0x93, 0x26, 0x36, 0x3f, 0xf7, 0xcc, 0x34, 0xa5, 0xe5, 0xf1, 0x71, 0xd8, 0x31, 0x15,
    0x04, 0xc7, 0x23, 0xc3, 0x18, 0x96, 0x05, 0x9a, 0x07, 0x12, 0x80, 0xe2, 0xeb, 0x27, 0xb2, 0x75,
    0x09, 0x83, 0x2c, 0x1a, 0x1b, 0x6e, 0x5a, 0xa0, 0x52, 0x3b, 0xd6, 0xb3, 0x29, 0xe3, 0x2f, 0x84,
    0x53, 0xd1, 0x00, 0xed, 0x20, 0xfc, 0xb1, 0x5b, 0x6a, 0xcb, 0xbe, 0x39, 0x4a, 0x4c, 0x58, 0xcf,
    0xd0, 0xef, 0xaa, 0xfb, 0x43, 0x4d, 0x33, 0x85, 0x45, 0xf9, 0x02, 0x7f, 0x50, 0x3c, 0x9f, 0xa8,
    0x51, 0xa3, 0x40, 0x8f, 0x92, 0x9d, 0x38, 0xf5, 0xbc, 0xb6, 0xda, 0x21, 0x10, 0xff, 0xf3, 0xd2,
    0xcd, 0x0c, 0x13, 0xec, 0x5f, 0x97, 0x44, 0x17, 0xc4, 0xa7, 0x7e, 0x3d, 0x64, 0x5d, 0x19, 0x73,
    0x60, 0x81, 0x4f, 0xdc, 0x22, 0x2a, 0x90, 0x88, 0x46, 0xee, 0xb8, 0x14, 0xde, 0x5e, 0x0b, 0xdb,
    0xe0, 0x32, 0x3a, 0x0a, 0x49, 0x06, 0x24, 0x5c, 0xc2, 0xd3, 0xac, 0x62, 0x91, 0x95, 0xe4, 0x79,
    0xe7, 0xc8, 0x37, 0x6d, 0x8d, 0xd5, 0x4e, 0xa9, 0x6c, 0x56, 0xf4, 0xea, 0x65, 0x7a, 0xae, 0x08,
    0xba, 0x78, 0x25, 0x2e, 0x1c, 0xa6, 0xb4, 0xc6, 0xe8, 0xdd, 0x74, 0x1f, 0x4b, 0xbd, 0x8b, 0x8a,
    0x70, 0x3e, 0xb5, 0x66, 0x48, 0x03, 0xf6, 0x0e, 0x61, 0x35, 0x57, 0xb9, 0x86, 0xc1, 0x1d, 0x9e,
    0xe1, 0xf8, 0x98, 0x11, 0x69, 0xd9, 0x8e, 0x94, 0x9b, 0x1e, 0x87, 0xe9, 0xce, 0x55, 0x28, 0xdf,
    0x8c, 0xa1, 0x89, 0x0d, 0xbf, 0xe6, 0x42, 0x68, 0x41, 0x99, 0x2d, 0x0f, 0xb0, 0x54, 0xbb, 0x16];
  var Rsbox = (function () { var r = new Array(256); for (var i = 0; i < 256; i++) r[Sbox[i]] = i; return r; })();
  function xtime(a) { a <<= 1; return (a > 255) ? (a ^ 0x1b) & 0xff : a; }
  function gmul(a, b) { var p = 0; while (b) { if (b & 1) p ^= a; a = xtime(a); b >>= 1; } return p & 0xff; }
  function expandKey(key) {
    var rk = new Array(176);
    for (var i = 0; i < 16; i++) rk[i] = key[i];
    var Rcon = 1, t = new Array(4), i, j;
    for (i = 16; i < 176; i += 4) {
      for (j = 0; j < 4; j++) t[j] = rk[i - 4 + j];
      if (i % 16 === 0) {
        var tmp = t[0];
        t[0] = Sbox[t[1]] ^ Rcon; t[1] = Sbox[t[2]]; t[2] = Sbox[t[3]]; t[3] = Sbox[tmp];
        Rcon = xtime(Rcon);
      }
      for (j = 0; j < 4; j++) rk[i + j] = rk[i - 16 + j] ^ t[j];
    }
    return rk;
  }
  function invShiftRows(s) {
    var t = s.slice();
    for (var r = 1; r < 4; r++)
      for (var c = 0; c < 4; c++)
        s[c * 4 + r] = t[((c + 4 - r) % 4) * 4 + r];
  }
  function decryptBlock(rk, inp) {
    var s = inp.slice(), i, round, c;
    for (i = 0; i < 16; i++) s[i] ^= rk[160 + i];
    for (round = 9; round >= 1; round--) {
      invShiftRows(s);
      for (i = 0; i < 16; i++) s[i] = Rsbox[s[i]];
      for (i = 0; i < 16; i++) s[i] ^= rk[round * 16 + i];
      for (c = 0; c < 4; c++) {
        var a0 = s[c * 4], a1 = s[c * 4 + 1], a2 = s[c * 4 + 2], a3 = s[c * 4 + 3];
        s[c * 4] = gmul(a0, 14) ^ gmul(a1, 11) ^ gmul(a2, 13) ^ gmul(a3, 9);
        s[c * 4 + 1] = gmul(a0, 9) ^ gmul(a1, 14) ^ gmul(a2, 11) ^ gmul(a3, 13);
        s[c * 4 + 2] = gmul(a0, 13) ^ gmul(a1, 9) ^ gmul(a2, 14) ^ gmul(a3, 11);
        s[c * 4 + 3] = gmul(a0, 11) ^ gmul(a1, 13) ^ gmul(a2, 9) ^ gmul(a3, 14);
      }
    }
    invShiftRows(s);
    for (i = 0; i < 16; i++) s[i] = Rsbox[s[i]];
    for (i = 0; i < 16; i++) s[i] ^= rk[i];
    return s;
  }
  function aesCbcDecrypt(key, iv, ct) {
    var rk = expandKey(key), out = new Array(ct.length), prev = iv.slice();
    for (var b = 0; b < ct.length; b += 16) {
      var d = decryptBlock(rk, ct.slice(b, b + 16));
      for (var i = 0; i < 16; i++) out[b + i] = d[i] ^ prev[i];
      prev = ct.slice(b, b + 16);
    }
    return out;
  }
  function b64ToBytes(b64) {
    if (typeof atob === 'function') {
      var bin = atob(b64), a = new Array(bin.length);
      for (var i = 0; i < bin.length; i++) a[i] = bin.charCodeAt(i);
      return a;
    }
    var B = G.Buffer; // 兼容 node 测试环境
    var buf = B.from(b64, 'base64'), out = new Array(buf.length);
    for (var j = 0; j < buf.length; j++) out[j] = buf[j];
    return out;
  }
  function strToBytes(str) { var a = []; for (var i = 0; i < str.length; i++) a.push(str.charCodeAt(i) & 0xff); return a; }
  function bytesToStr(bytes) {
    var s = '', CH = 8192;
    for (var i = 0; i < bytes.length; i += CH) {
      var part = bytes.slice(i, i + CH), buf = [];
      for (var k = 0; k < part.length; k++) buf.push(part[k]);
      s += String.fromCharCode.apply(null, buf);
    }
    return s;
  }
  function utf8Decode(bytes) {
    var bin = bytesToStr(bytes);
    if (typeof TextDecoder !== 'undefined') return new TextDecoder('utf-8').decode(new Uint8Array(bytes));
    // 回退：手写 UTF-8 解码
    var out = '', i = 0, n = bin.length;
    while (i < n) {
      var c = bin.charCodeAt(i++);
      if (c < 0x80) out += String.fromCharCode(c);
      else if (c < 0xE0) out += String.fromCharCode(((c & 0x1F) << 6) | (bin.charCodeAt(i++) & 0x3F));
      else if (c < 0xF0) out += String.fromCharCode(((c & 0x0F) << 12) | ((bin.charCodeAt(i++) & 0x3F) << 6) | (bin.charCodeAt(i++) & 0x3F));
      else { var cp = ((c & 0x07) << 18) | ((bin.charCodeAt(i++) & 0x3F) << 12) | ((bin.charCodeAt(i++) & 0x3F) << 6) | (bin.charCodeAt(i++) & 0x3F); cp -= 0x10000; out += String.fromCharCode(0xD800 + (cp >> 10), 0xDC00 + (cp & 0x3FF)); }
    }
    return out;
  }
  function undress(keyStr, ivStr, ctB64) {
    var key = strToBytes(keyStr).slice(0, 16);
    var iv = strToBytes(ivStr).slice(0, 16);
    var ct = b64ToBytes(ctB64);
    // base64 长度补齐到 16 的倍数
    while (ct.length % 16 !== 0) ct.push(0);
    var pt = aesCbcDecrypt(key, iv, ct);
    // 去掉 ZeroPadding 的尾部 0x00
    var end = pt.length;
    while (end > 0 && pt[end - 1] === 0) end--;
    var bytes = pt.slice(0, end);
    return utf8Decode(bytes);
  }

  // ---------- 站点逻辑 ----------
  var STREAM_JS = 'http://toutiao.cnwest.com/static/v1/group/stream.js';

  // 名称 <-> 标识 (来自 http://live.snrtv.com/ 页面 .btnStream li[data-num])
  var CHANNELS = [
    { key: 'star', name: '陕西卫视' },
    { key: '1', name: '新闻资讯' },
    { key: '2', name: '都市青春' },
    { key: '3', name: '银龄频道' },
    { key: '5', name: '秦腔频道' },
    { key: '7', name: '体育休闲' },
    { key: 'nl', name: '农林卫视' },
    { key: '11', name: '移动电视' },
  ];
  // 常用别名
  var ALIAS = { '银龄': '3', '都市青春频道': '2', '新闻资讯频道': '1', '体育休闲频道': '7', '农林': 'nl' };

  function pickKey(ch) {
    if (ch == null) return null;
    for (var i = 0; i < CHANNELS.length; i++) {
      if (CHANNELS[i].key === ch || CHANNELS[i].name === ch) return CHANNELS[i].key;
    }
    if (ALIAS[ch]) return ALIAS[ch];
    // 包含式匹配
    for (var j = 0; j < CHANNELS.length; j++) {
      if (ch.indexOf(CHANNELS[j].name) >= 0 || CHANNELS[j].name.indexOf(ch) >= 0) return CHANNELS[j].key;
    }
    return null;
  }

  function extractVar(src, name) {
    var re = new RegExp('var\\s+' + name + '\\s*=\\s*"([^"]*)"');
    var m = src.match(re);
    if (!m) throw new Error('未找到变量 ' + name + '（页面结构可能已变）');
    return m[1];
  }

  function getMapTV(src) {
    var sTV = extractVar(src, 'sTV');
    var sRadio = extractVar(src, 'sRadio');
    var json = undress(sTV.substring(0, 16), sRadio.substring(0, 16), sTV.substring(16));
    return JSON.parse(json);
  }

  function fetchStreamJs() {
    // 静态资源偶发 403（限流），带 Referer 并重试
    var tries = 0;
    function attempt() {
      return fetch(STREAM_JS, {
        headers: { 'Referer': 'http://live.snrtv.com/', 'Accept': '*/*' },
        cache: 'no-store',
      }).then(function (r) {
        if (!r.ok) throw new Error('stream.js HTTP ' + r.status);
        return r.text();
      }).catch(function (e) {
        if (++tries < 3) return new Promise(function (res) { setTimeout(res, 500); }).then(attempt);
        throw e;
      });
    }
    return attempt();
  }

  // 返回频道 -> m3u8 的全量映射（顺带提供）
  function resolveAll() {
    return fetchStreamJs().then(function (src) {
      var mapTV = getMapTV(src);
      var g = mapTV['sxbc'] || {};
      var out = {};
      for (var k in g) out[k] = { name: g[k].name, m3u8: g[k].m3u8 };
      return out;
    });
  }

  // 主入口：输入频道标识(名称或 key)，输出当次可播 m3u8
  function resolve(channel) {
    var key = pickKey(channel);
    if (key == null) key = channel; // 直接当作 key 试
    return fetchStreamJs().then(function (src) {
      var mapTV = getMapTV(src);
      var g = mapTV['sxbc'] || {};
      var node = g[key];
      if (!node || !node.m3u8) throw new Error('陕西：频道 [' + channel + '] 无直播流 (key=' + key + ')');
      return node.m3u8;
    });
  }

  G.__RESOLVERS.shaanxi = {
    name: '陕西',
    site: 'http://live.snrtv.com/',
    channels: CHANNELS,
    resolve: resolve,
    resolveAll: resolveAll,
  };
})(typeof window !== 'undefined' ? window : this);
