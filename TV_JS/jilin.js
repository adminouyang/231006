/* ============================================================
 * 吉林    key: jilin
 * ------------------------------------------------------------
 * 来源站点：https://www.jlntv.cn/tv?id=104
 * 取流方式：腾讯云签名
 * 频道数：15      最后更新：2026-10-16
 *
 * 本文件是 TVLive 的「吉林」分组订阅文件，可直接手工修改后重新上传。
 * 改完记得同步 index.json 里本文件的 sha256（不想校验就写空字符串）。
 * ============================================================ */

/* ---- 1) 频道表：TVLive 启动时会读走这一段 ----
 * name      显示名（分组标题已写省份，这里不用再重复前缀）
 * url       兜底直连地址；带时效签名的台靠下面解析器现算，这里填旧的没关系
 * provider  解析器名，对应下面第 2 段里注册的名字；不需要就整行删掉
 * param     传给解析器的参数，一般是流名或频道 id
 */
TVRemote.define({
  key: "jilin",
  group: "吉林",
  updated: "2026-10-16",
  note: "省级 6 + 地市 9，腾讯云签名本地重算",
  list: [
    { number: 127, name: "吉林卫视", url: "https://hls.avap.jilintv.cn/zqvk7vpj/channel/0533b55e42354f4f802bdec78e26b571/index.m3u8?txSecret=8f1d937dde80ad0e8eaa54215b52e9d9&txTime=6ACAA716", provider: "jilin", param: "0533b55e42354f4f802bdec78e26b571" },
    { number: 128, name: "都市频道", url: "https://hls.avap.jilintv.cn/zqvk7vpj/channel/7e8474e6daea44ccaa5aa2300191439e/index.m3u8?txSecret=8f1d937dde80ad0e8eaa54215b52e9d9&txTime=6ACAA716", provider: "jilin", param: "7e8474e6daea44ccaa5aa2300191439e" },
    { number: 129, name: "生活频道", url: "https://hls.avap.jilintv.cn/zqvk7vpj/channel/0a76740c72b74fabae611845aa21e06a/index.m3u8?txSecret=8f1d937dde80ad0e8eaa54215b52e9d9&txTime=6ACAA716", provider: "jilin", param: "0a76740c72b74fabae611845aa21e06a" },
    { number: 130, name: "影视频道", url: "https://hls.avap.jilintv.cn/zqvk7vpj/channel/906341e6f19b4c4bacdc89941eb85d12/index.m3u8?txSecret=8f1d937dde80ad0e8eaa54215b52e9d9&txTime=6ACAA716", provider: "jilin", param: "906341e6f19b4c4bacdc89941eb85d12" },
    { number: 131, name: "乡村频道", url: "https://hls.avap.jilintv.cn/zqvk7vpj/channel/3ffc4824dce54b92be185555923ce382/index.m3u8?txSecret=8f1d937dde80ad0e8eaa54215b52e9d9&txTime=6ACAA716", provider: "jilin", param: "3ffc4824dce54b92be185555923ce382" },
    { number: 132, name: "综艺·文化频道", url: "https://hls.avap.jilintv.cn/zqvk7vpj/channel/b3925adaf01e41f287f482f0aea3d233/index.m3u8?txSecret=8f1d937dde80ad0e8eaa54215b52e9d9&txTime=6ACAA716", provider: "jilin", param: "b3925adaf01e41f287f482f0aea3d233" },
    { number: 133, name: "长春综合", url: "https://stream2.jlntv.cn/jlcc/sd/live.m3u8" },
    { number: 134, name: "吉林新闻综合", url: "https://stream2.jlntv.cn/jilin1/sd/live.m3u8" },
    { number: 135, name: "四平新闻综合", url: "https://stream2.jlntv.cn/sptv/sd/live.m3u8" },
    { number: 136, name: "辽源新闻综合", url: "https://stream2.jlntv.cn/liaoyuan1/sd/live.m3u8" },
    { number: 137, name: "通化新闻综合", url: "https://live-master.jlntv.cn/thhd/sd/live.m3u8" },
    { number: 138, name: "白山新闻综合", url: "https://stream2.jlntv.cn/baishan1/sd/live.m3u8" },
    { number: 139, name: "白城新闻综合", url: "https://stream2.jlntv.cn/baicheng1/sd/live.m3u8" },
    { number: 140, name: "松原新闻综合", url: "https://stream2.jlntv.cn/sytv/sd/live.m3u8" },
    { number: 141, name: "延边卫视", url: "https://stream2.jlntv.cn/jlyb/sd/live.m3u8" }
  ]
});

/* ---- 2) 取流解析器：带时效签名的台靠它现算新鲜地址 ----
 * 每个解析器注册成 window.__RESOLVERS.<provider>(param) -> Promise<m3u8>
 * 不想用解析器就整段删掉，播放时会退回上面的 url。
 */
/* ============================================================
 * 吉林广播电视台 省级频道 直播解析器  (window.__RESOLVERS.jilin)
 * 站点: https://www.jlntv.cn/   (吉祥新闻)
 * ------------------------------------------------------------
 * 接口:  GET https://clientapi.jlntv.cn/broadcast/list?page=1&size=10000&type=1
 *   - 请求头 encrypt: 111  ->  服务端直接返回明文 JSON
 *     (不加该头则返回 XXTEA(base64) 密文, key = 5b28bae827e651b3,
 *      本文件同时也实现了 XXTEA 解密做兜底)
 *   - 返回: {code:0, data:[ {title, subTitle, data:{streamUrl}} ... ]}
 *   - streamUrl 形如:
 *     https://hls.avap.jilintv.cn/zqvk7vpj/channel/<channelId>/index.m3u8?txSecret=..&txTime=..
 *     腾讯云签名, txTime(hex 秒) 约 4 小时过期 —— 每次实时调接口刷新。
 *   - 该接口里还混有 15 个频道，其中前 6 个是省级台(走 avap 签名地址)，
 *     其余是各市/延边的老 stream2.jlntv.cn 静态地址（不在本题范围）。
 * ------------------------------------------------------------
 * 用法:
 *   await window.__RESOLVERS.jilin('吉林卫视')                       // 频道名
 *   await window.__RESOLVERS.jilin('0533b55e42354f4f802bdec78e26b571') // channelId
 *   await window.__RESOLVERS.jilin.resolve('都市频道')
 *   await window.__RESOLVERS.jilin.resolveAll()   // { 频道名: m3u8 }
 * ============================================================ */
(function (G) {
  'use strict';
  G.__RESOLVERS = G.__RESOLVERS || {};

  var KEY = '5b28bae827e651b3';
  var API = 'https://clientapi.jlntv.cn/broadcast/list?page=1&size=10000&type=1';
  var DELTA = 0x9E3779B9;

  /* ---------- 纯浏览器 字节/字符串/base64 工具 ---------- */
  var _enc = new TextEncoder();
  var _dec = new TextDecoder('utf-8');
  function strToBytes(s) { return _enc.encode(s); }
  function bytesToStr(b) { return _dec.decode(b); }
  function b64ToBytes(b64) {
    var bin = atob(String(b64).replace(/\s+/g, ''));
    var out = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) out[i] = bin.charCodeAt(i);
    return out;
  }
  function bytesToB64(bytes) {
    var s = '', CH = 0x8000;
    for (var i = 0; i < bytes.length; i += CH) s += String.fromCharCode.apply(null, bytes.subarray(i, i + CH));
    return btoa(s);
  }

  /* ---------- 纯 JS XXTEA（兜底解密用） ---------- */
  function i32(x) { return x & 4294967295; }
  function mx(sum, y, z, p, e, k) {
    return ((z >>> 5 ^ y << 2) + (y >>> 3 ^ z << 4)) ^ ((sum ^ y) + (k[(p & 3) ^ e] ^ z));
  }
  function fixKey(k) { if (k.length < 16) { var t = new Uint8Array(16); t.set(k); return t; } return k; }
  function toUint32Array(bytes, includeLength) {
    var len = bytes.length, n = len >> 2;
    if ((len & 3) !== 0) ++n;
    var v = includeLength ? (v = new Uint32Array(n + 1), v[n] = len, v) : new Uint32Array(n);
    for (var i = 0; i < len; ++i) v[i >> 2] |= bytes[i] << ((i & 3) << 3);
    return v;
  }
  function toBytes(v, includeLength) {
    var len = (v.length << 2);
    if (includeLength) {
      var m = v[v.length - 1];
      len -= 4;
      if (m < len - 3 || m > len) return null;
      len = m;
    }
    var bytes = new Uint8Array(len);
    for (var i = 0; i < len; ++i) bytes[i] = v[i >> 2] >> ((i & 3) << 3);
    return bytes;
  }
  function decryptUint32Array(v, k) {
    var R = v.length, H = R - 1, F, M, N, E, P, j;
    for (F = v[0], j = Math.floor(6 + 52 / R), N = i32(j * DELTA); N !== 0; N = i32(N - DELTA)) {
      E = (N >>> 2) & 3;
      for (P = H; P > 0; --P) { M = v[P - 1]; F = v[P] = i32(v[P] - mx(N, F, M, P, E, k)); }
      M = v[H]; F = v[0] = i32(v[0] - mx(N, F, M, 0, E, k));
    }
    return v;
  }
  function xxteaDecryptB64(b64) {
    var k = toUint32Array(fixKey(strToBytes(KEY)), false);
    var v = toUint32Array(b64ToBytes(b64), false);
    return bytesToStr(toBytes(decryptUint32Array(v, k), true));
  }

  /* ---------- 省级 6 台 (param 可用 channelId / 频道名) ---------- */
  var CHANNELS = [
    { name: '吉林卫视', id: '0533b55e42354f4f802bdec78e26b571' },
    { name: '都市频道', id: '7e8474e6daea44ccaa5aa2300191439e', alias: ['都市'] },
    { name: '生活频道', id: '0a76740c72b74fabae611845aa21e06a', alias: ['生活'] },
    { name: '影视频道', id: '906341e6f19b4c4bacdc89941eb85d12', alias: ['影视'] },
    { name: '乡村频道', id: '3ffc4824dce54b92be185555923ce382', alias: ['乡村'] },
    { name: '综艺·文化频道', id: 'b3925adaf01e41f287f482f0aea3d233', alias: ['综艺文化', '综艺文化频道', '综艺', '文化'] }
  ];
  var ID_SET = {};
  CHANNELS.forEach(function (c) { ID_SET[c.id] = 1; });

  function norm(s) { return String(s == null ? '' : s).replace(/[\s·・\-—_（）()【】\[\]]/g, ''); }

  function normalizeParam(param) {
    if (param == null) return { id: null, title: null };
    var p = String(param).trim();
    if (/^[0-9a-fA-F]{32}$/.test(p)) return { id: p.toLowerCase(), title: null };
    var np = norm(p);
    for (var i = 0; i < CHANNELS.length; i++) {
      var c = CHANNELS[i];
      if (norm(c.name) === np) return { id: c.id, title: c.name };
      if (c.alias) for (var j = 0; j < c.alias.length; j++) if (norm(c.alias[j]) === np) return { id: c.id, title: c.name };
    }
    for (var m = 0; m < CHANNELS.length; m++) {
      var cc = CHANNELS[m];
      if (np && (norm(cc.name).indexOf(np) >= 0 || np.indexOf(norm(cc.name)) >= 0)) return { id: cc.id, title: cc.name };
      if (cc.alias) for (var n = 0; n < cc.alias.length; n++) {
        if (np && (norm(cc.alias[n]).indexOf(np) >= 0 || np.indexOf(norm(cc.alias[n])) >= 0)) return { id: cc.id, title: cc.name };
      }
    }
    return { id: null, title: p };
  }

  function channelIdOf(url) {
    var m = /\/channel\/([0-9a-fA-F]{32})\//.exec(url || '');
    return m ? m[1].toLowerCase() : null;
  }

  /* ---------- 拉取全量列表（明文优先，密文兜底） ---------- */
  function fetchList() {
    return fetch(API, {
      method: 'GET',
      headers: { 'encrypt': '111', 'accept': 'application/json' },
      cache: 'no-store',
      credentials: 'omit'
    }).then(function (r) {
      if (!r.ok) throw new Error('吉林：接口 HTTP ' + r.status);
      return r.text();
    }).then(function (txt) {
      var s = txt.trim();
      if (s.charAt(0) === '"') { try { s = JSON.parse(s); } catch (e) { /* ignore */ } }
      if (s.charAt(0) === '{') {
        try {
          var j = JSON.parse(s);
          if (j && Array.isArray(j.data)) return j.data;
          if (j && typeof j.data === 'string') s = j.data; // 包了一层 base64
        } catch (e) { /* 可能是密文, 落到下面解密 */ }
      }
      var plain;
      try { plain = xxteaDecryptB64(s); }
      catch (e) { throw new Error('吉林：列表既非明文也非可解 XXTEA 密文 (' + e.message + ')'); }
      var obj = JSON.parse(plain);
      var arr = obj && obj.data ? obj.data : obj;
      if (!Array.isArray(arr)) throw new Error('吉林：返回结构异常 ' + plain.slice(0, 120));
      return arr;
    });
  }

  function streamOf(item) {
    if (!item) return null;
    if (item.data && item.data.streamUrl) return item.data.streamUrl;
    if (item.data && item.data.streamUrls && item.data.streamUrls[0]) return item.data.streamUrls[0];
    if (item.streamUrl) return item.streamUrl;
    return null;
  }

  function pick(list, param) {
    var t = normalizeParam(param);
    var i, it;
    if (t.id) {
      for (i = 0; i < list.length; i++) {
        it = list[i];
        if (channelIdOf(streamOf(it)) === t.id) return it;
        if ((it.title || '') === t.title) return it;
      }
    }
    if (t.title) {
      for (i = 0; i < list.length; i++) { it = list[i]; if ((it.title || '') === t.title || (it.subTitle || '') === t.title) return it; }
      var nt = norm(t.title);
      for (i = 0; i < list.length; i++) {
        it = list[i]; var nit = norm(it.title || '');
        if (nt && (nit.indexOf(nt) >= 0 || nt.indexOf(nit) >= 0)) return it;
      }
    }
    // 直接用 hex 参数比 channelId
    var raw = String(param || '').trim().toLowerCase();
    if (/^[0-9a-f]{32}$/.test(raw)) for (i = 0; i < list.length; i++) if (channelIdOf(streamOf(list[i])) === raw) return list[i];
    return null;
  }

  /* ---------- 对外 API ---------- */
  async function resolve(param) {
    var list = await fetchList();
    var hit = pick(list, param);
    if (!hit) {
      var avail = list.map(function (x) { var c = channelIdOf(streamOf(x)); return c ? x.title : null; }).filter(Boolean);
      throw new Error('吉林：未找到频道 [' + param + ']，可用: ' + avail.join('/'));
    }
    var url = streamOf(hit);
    if (!url) throw new Error('吉林：频道 [' + param + '] 无 streamUrl');
    return url;
  }

  async function resolveAll() {
    var list = await fetchList();
    var out = {};
    list.forEach(function (x) {
      var u = streamOf(x);
      if (!u) return;
      var c = channelIdOf(u);
      if (c) out[x.title] = u;   // 只收省级 6 台的 avap 地址
    });
    return out;
  }

  var fn = resolve;
  try { Object.defineProperty(fn, 'name', { value: '吉林', configurable: true }); } catch (e) { fn.displayName = '吉林'; }
  fn.displayName = '吉林';
  fn.site = 'https://www.jlntv.cn/';
  fn.channels = CHANNELS;
  fn.resolve = resolve;
  fn.resolveAll = resolveAll;
  fn._xxteaDecrypt = xxteaDecryptB64;
  G.__RESOLVERS.jilin = fn;
})(typeof window !== 'undefined' ? window : this);
