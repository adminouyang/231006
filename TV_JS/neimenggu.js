/* ============================================================
 * 内蒙古    key: neimenggu
 * ------------------------------------------------------------
 * 来源站点：https://www.nmtv.cn/liveTv
 * 取流方式：腾讯云签名
 * 频道数：20      最后更新：2026-10-16
 *
 * 本文件是 TVLive 的「内蒙古」分组订阅文件，可直接手工修改后重新上传。
 * 改完记得同步 index.json 里本文件的 sha256（不想校验就写空字符串）。
 * ============================================================ */

/* ---- 1) 频道表：TVLive 启动时会读走这一段 ----
 * name      显示名（分组标题已写省份，这里不用再重复前缀）
 * url       兜底直连地址；带时效签名的台靠下面解析器现算，这里填旧的没关系
 * provider  解析器名，对应下面第 2 段里注册的名字；不需要就整行删掉
 * param     传给解析器的参数，一般是流名或频道 id
 */
TVRemote.define({
  key: "neimenggu",
  group: "内蒙古",
  updated: "2026-10-16",
  note: "省级 8 + 盟市 12，腾讯云签名本地重算",
  list: [
    { number: 107, name: "内蒙古卫视", url: "https://livestream-bt.nmtv.cn/nmtv/3621481general.m3u8?txSecret=a0b8cc66a1124cf66791a507195b9093&txTime=6D58FFD0&token=b3233d3db98f4302b81136226951a5c7", provider: "nmtv", param: "3621481" },
    { number: 108, name: "内蒙古蒙古语卫视", url: "https://livestream-bt.nmtv.cn/nmtv/2315general.m3u8?txSecret=4971666599ef9411629213c9a300bf66&txTime=771EF880&token=cc576ef06c6b4f81a22f2529324737ea", provider: "nmtv", param: "2315" },
    { number: 109, name: "内蒙古新闻综合", url: "https://livestream-bt.nmtv.cn/nmtv/2316general.m3u8?txSecret=b4373417a82ed64e52b0982a66da8df2&txTime=771E8800&token=593015adc42341bba2c99455941386d0", provider: "nmtv", param: "2316" },
    { number: 110, name: "内蒙古经济生活", url: "https://livestream-bt.nmtv.cn/nmtv/2317general.m3u8?txSecret=112b2c4c872de52b0f37aff6ead63ef0&txTime=771E8800&token=9bf604764f464d38b8bcd2d7a196541f", provider: "nmtv", param: "2317" },
    { number: 111, name: "内蒙古少儿", url: "https://livestream-bt.nmtv.cn/nmtv/2318general.m3u8?txSecret=a2c948908728a0733cecbe1fadea23dc&txTime=771E8800&token=cbc421b97e594c7e805652883d43e746", provider: "nmtv", param: "2318" },
    { number: 112, name: "内蒙古文体娱乐", url: "https://livestream-bt.nmtv.cn/nmtv/2319general.m3u8?txSecret=c7b5c515d2bb6df442492d54955329a3&txTime=771E8800&token=f4129474232d499dabf808628fc3390e", provider: "nmtv", param: "2319" },
    { number: 113, name: "内蒙古农牧", url: "https://livestream-bt.nmtv.cn/nmtv/2320general.m3u8?txSecret=4d368a175afa19737a9f5be10af24fe2&txTime=771E8800&token=b37a4903fce64a238060440024621609", provider: "nmtv", param: "2320" },
    { number: 114, name: "内蒙古蒙古语文化", url: "https://livestream-bt.nmtv.cn/nmtv/2321general.m3u8?txSecret=d9d0fd7a252ef56b515c46a2e21830f4&txTime=771E8800&token=cd6cd87f528a4cfc8e482876b19370c2", provider: "nmtv", param: "2321" },
    { number: 115, name: "呼和浩特", url: "https://livestream-bt.nmtv.cn/nmtv/2331general.m3u8?txSecret=4d7342ca5cd74480526ab6d292247aff&txTime=771E8800&token=c65a4f0a34654207a4241b80a79970bb", provider: "nmtv", param: "2331" },
    { number: 116, name: "包头", url: "https://livestream-bt.nmtv.cn/nmtv/2358general.m3u8?txSecret=98390a77c143a68f0fd64bfe6e181dcb&txTime=771E8800&token=3f9a73adf0b940b1ad7a5fdd54e97923", provider: "nmtv", param: "2358" },
    { number: 117, name: "乌海", url: "https://livestream-bt.nmtv.cn/nmtv/2355general.m3u8?txSecret=c623c5c66e83e43b566ebe90f49c4b06&txTime=771E8800&token=02eb0c695a3c48c7a2ce782616647f6b", provider: "nmtv", param: "2355" },
    { number: 118, name: "赤峰", url: "https://livestream-bt.nmtv.cn/nmtv/2351general.m3u8?txSecret=8857087aeec2cec44d178a18550fdb8a&txTime=771E8800&token=1555feb7302a48af916733305c2b213e", provider: "nmtv", param: "2351" },
    { number: 119, name: "呼伦贝尔", url: "https://livestream-bt.nmtv.cn/nmtv/2356general.m3u8?txSecret=ff186bf3aac1022cd17068bcc0c78414&txTime=771E8800&token=f3b8f11f95fe40fdbd143cd530746ee1", provider: "nmtv", param: "2356" },
    { number: 120, name: "兴安盟", url: "https://livestream-bt.nmtv.cn/nmtv/2357general.m3u8?txSecret=9fa7524fa6e7380395e4a7a91bd3bcc8&txTime=771E8800&token=fefc91dc74e34ccd919a12344c0c2730", provider: "nmtv", param: "2357" },
    { number: 121, name: "通辽", url: "https://livestream-bt.nmtv.cn/nmtv/2353general.m3u8?txSecret=96a2008eff039ef4ad07179e367b838b&txTime=771E8800&token=ab130d1ab0ff4f14bbe4dc76d6047260", provider: "nmtv", param: "2353" },
    { number: 122, name: "锡林郭勒", url: "https://livestream-bt.nmtv.cn/nmtv/2346general.m3u8?txSecret=4917fb7aee368c8f4d8099847182a791&txTime=771E8800&token=79eb9f05718642408eabee1b97166e62", provider: "nmtv", param: "2346" },
    { number: 123, name: "乌兰察布", url: "https://livestream-bt.nmtv.cn/nmtv/2354general.m3u8?txSecret=cf5f71d0000862b18f5813607b3dfd5b&txTime=771E8800&token=8072d044f0ab46f7aecf75cabdb4baed", provider: "nmtv", param: "2354" },
    { number: 124, name: "鄂尔多斯", url: "https://livestream-bt.nmtv.cn/nmtv/2349general.m3u8?txSecret=e44477052aba305cadeea45aaf1c674a&txTime=771E8800&token=dd725fd734f147de9f43ecde0a13870d", provider: "nmtv", param: "2349" },
    { number: 125, name: "巴彦淖尔", url: "https://livestream-bt.nmtv.cn/nmtv/2348general.m3u8?txSecret=6a4ddce077e41b976fe33619fbef2b30&txTime=771E8800&token=e54426e5fe314104b9de8675d7bb80e7", provider: "nmtv", param: "2348" },
    { number: 126, name: "阿拉善", url: "https://livestream-bt.nmtv.cn/nmtv/2347general.m3u8?txSecret=7516318a05754a7c1513eb01e1c66b77&txTime=771E8800&token=e443a7ace0e4467dae2d30080c7344ab", provider: "nmtv", param: "2347" }
  ]
});

/* ---- 2) 取流解析器：带时效签名的台靠它现算新鲜地址 ----
 * 每个解析器注册成 window.__RESOLVERS.<provider>(param) -> Promise<m3u8>
 * 不想用解析器就整段删掉，播放时会退回上面的 url。
 */
/* ============================================================
 * 内蒙古广播电视台 直播解析器  (window.__RESOLVERS.nmtv)
 * 站点: https://www.nmtv.cn/   (奔腾融媒)
 * ------------------------------------------------------------
 * 接口:  POST https://api-bt.nmtv.cn/broadcast/list
 *   - 请求头 : Client-Type: web , Content-Type: application/json
 *              (Referer / Origin 都非必须，实测不带也 200)
 *   - 请求体 : 明文 JSON {type:1, page:1, size:100}
 *              用 XXTEA 加密成 base64 后整体当作 body 发送
 *   - 响应体 : 形如 "xxxxx==" 的 JSON 字符串字面量，
 *              去掉引号后是 XXTEA(base64) 密文，
 *              解密后得到 {code:0, data:[ {id, title, data:{streamUrl}} ... ]}
 *   - XXTEA key = 5b28bae827e651b3
 *   - 分页   : 默认 size=10 只回 10 个，必须显式传 size（>=20）才能拿全 20 个台
 * ------------------------------------------------------------
 * 输出: data[].data.streamUrl
 *   https://livestream-bt.nmtv.cn/nmtv/<id>general.m3u8?txSecret=..&txTime=..&token=..
 *   腾讯云签名，txTime 到点后会失效 —— 所以每次都实时调接口。
 * ------------------------------------------------------------
 * 用法:
 *   await window.__RESOLVERS.nmtv('内蒙古卫视')   // 传频道名
 *   await window.__RESOLVERS.nmtv(2316)            // 传频道 id
 *   await window.__RESOLVERS.nmtv.resolve('呼和浩特')
 *   await window.__RESOLVERS.nmtv.resolveAll()     // { 频道名: m3u8 }
 * ============================================================ */
(function (G) {
  'use strict';
  G.__RESOLVERS = G.__RESOLVERS || {};

  var KEY = '5b28bae827e651b3';
  var API = 'https://api-bt.nmtv.cn/broadcast/list';
  var DELTA = 0x9E3779B9; // 2654435769

  /* ---------- 纯浏览器 字节/字符串/base64 工具 (不依赖 Node) ---------- */
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
    for (var i = 0; i < bytes.length; i += CH) {
      s += String.fromCharCode.apply(null, bytes.subarray(i, i + CH));
    }
    return btoa(s);
  }

  /* ---------- 纯 JS XXTEA (与站点 bundle 完全一致) ---------- */
  function i32(x) { return x & 4294967295; }
  function mx(sum, y, z, p, e, k) {
    return ((z >>> 5 ^ y << 2) + (y >>> 3 ^ z << 4)) ^ ((sum ^ y) + (k[(p & 3) ^ e] ^ z));
  }
  function fixKey(k) {
    if (k.length < 16) { var t = new Uint8Array(16); t.set(k); return t; }
    return k;
  }
  function toUint32Array(bytes, includeLength) {
    var len = bytes.length, n = len >> 2;
    if ((len & 3) !== 0) ++n;
    var v;
    if (includeLength) { v = new Uint32Array(n + 1); v[n] = len; }
    else { v = new Uint32Array(n); }
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
  function encryptUint32Array(v, k) {
    var R = v.length, H = R - 1, F, M, N, E, P, j;
    for (M = v[H], N = 0, j = Math.floor(6 + 52 / R) | 0; j > 0; --j) {
      N = i32(N + DELTA); E = (N >>> 2) & 3;
      for (P = 0; P < H; ++P) { F = v[P + 1]; M = v[P] = i32(v[P] + mx(N, F, M, P, E, k)); }
      F = v[0]; M = v[H] = i32(v[H] + mx(N, F, M, H, E, k));
    }
    return v;
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

  function xxteaEncryptB64(plain) {
    var k = toUint32Array(fixKey(strToBytes(KEY)), false);
    var v = toUint32Array(strToBytes(plain), true);
    return bytesToB64(toBytes(encryptUint32Array(v, k), false));
  }
  function xxteaDecryptB64(b64) {
    var k = toUint32Array(fixKey(strToBytes(KEY)), false);
    var v = toUint32Array(b64ToBytes(b64), false);
    return bytesToStr(toBytes(decryptUint32Array(v, k), true));
  }

  /* ---------- 频道表 (param 可用 名称 / 别名 / id) ---------- */
  var CHANNELS = [
    { name: '内蒙古卫视', id: 3621481 },
    { name: '内蒙古蒙古语卫视', id: 2315, alias: ['蒙古语卫视'] },
    { name: '新闻综合', id: 2316, alias: ['内蒙古新闻综合', '新闻综合频道'] },
    { name: '经济生活', id: 2317, alias: ['内蒙古经济生活', '经济生活频道'] },
    { name: '少儿频道', id: 2318, alias: ['内蒙古少儿', '少儿'] },
    { name: '文体娱乐', id: 2319, alias: ['内蒙古文体娱乐', '文体娱乐频道'] },
    { name: '农牧频道', id: 2320, alias: ['内蒙古农牧', '农牧'] },
    { name: '内蒙古蒙古语文化频道', id: 2321, alias: ['内蒙古蒙古语文化', '蒙古语文化', '蒙古语文化频道'] },
    { name: '呼和浩特', id: 2331, alias: ['呼和浩特新闻综合'] },
    { name: '包头', id: 2358 },
    { name: '乌海', id: 2355 },
    { name: '赤峰', id: 2351 },
    { name: '呼伦贝尔', id: 2356 },
    { name: '兴安盟', id: 2357 },
    { name: '通辽', id: 2353 },
    { name: '锡林郭勒', id: 2346 },
    { name: '乌兰察布', id: 2354 },
    { name: '鄂尔多斯', id: 2349 },
    { name: '巴彦淖尔', id: 2348 },
    { name: '阿拉善', id: 2347 }
  ];

  function norm(s) { return String(s == null ? '' : s).replace(/[\s·・\-—_（）()【】\[\]]/g, ''); }

  // 把 param 归一到 id（优先）或 API title
  function normalizeParam(param) {
    if (param == null) return { id: null, title: null };
    var p = String(param).trim();
    if (/^\d+$/.test(p)) return { id: parseInt(p, 10), title: null };
    var np = norm(p);
    for (var i = 0; i < CHANNELS.length; i++) {
      var c = CHANNELS[i];
      if (norm(c.name) === np) return { id: c.id, title: c.name };
      if (c.alias) for (var j = 0; j < c.alias.length; j++) if (norm(c.alias[j]) === np) return { id: c.id, title: c.name };
    }
    // 模糊包含匹配
    for (var m = 0; m < CHANNELS.length; m++) {
      var cc = CHANNELS[m];
      if (np && (norm(cc.name).indexOf(np) >= 0 || np.indexOf(norm(cc.name)) >= 0)) return { id: cc.id, title: cc.name };
      if (cc.alias) for (var n = 0; n < cc.alias.length; n++) {
        if (np && (norm(cc.alias[n]).indexOf(np) >= 0 || np.indexOf(norm(cc.alias[n])) >= 0)) return { id: cc.id, title: cc.name };
      }
    }
    return { id: null, title: p };
  }

  /* ---------- 拉取 + 解密全量列表 ---------- */
  function fetchList() {
    return fetch(API, {
      method: 'POST',
      headers: { 'Client-Type': 'web', 'Content-Type': 'application/json' },
      body: xxteaEncryptB64(JSON.stringify({ type: 1, page: 1, size: 100 })),
      cache: 'no-store',
      credentials: 'omit'
    }).then(function (r) {
      if (!r.ok) throw new Error('内蒙古：接口 HTTP ' + r.status);
      return r.text();
    }).then(function (txt) {
      var s = txt.trim();
      // 有时是 JSON 字符串字面量再包一层
      if (s.charAt(0) === '"') { try { s = JSON.parse(s); } catch (e) { /* ignore */ } }
      // 兼容 {"code":0,"data":"<base64>"} 这种包装
      if (s.charAt(0) === '{') {
        try { var j = JSON.parse(s); if (j && typeof j.data === 'string') s = j.data; } catch (e) { /* ignore */ }
      }
      var plain;
      try { plain = xxteaDecryptB64(s); }
      catch (e) { throw new Error('内蒙古：XXTEA 解密失败 ' + e.message); }
      var obj = JSON.parse(plain);
      var arr = obj && obj.data ? obj.data : obj;
      if (!Array.isArray(arr)) throw new Error('内蒙古：返回结构异常 ' + plain.slice(0, 120));
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
    // 1) id 命中
    if (t.id != null) {
      for (i = 0; i < list.length; i++) if (Number(list[i].id) === Number(t.id)) return list[i];
    }
    // 2) title 精确
    if (t.title) {
      for (i = 0; i < list.length; i++) { it = list[i]; if ((it.title || '') === t.title || (it.subTitle || '') === t.title) return it; }
      // 3) 归一化包含
      var nt = norm(t.title);
      for (i = 0; i < list.length; i++) {
        it = list[i];
        var nit = norm(it.title || '');
        if (nt && (nit.indexOf(nt) >= 0 || nt.indexOf(nit) >= 0)) return it;
      }
    }
    return null;
  }

  /* ---------- 对外 API ---------- */
  async function resolve(param) {
    var list = await fetchList();
    var hit = pick(list, param);
    if (!hit) throw new Error('内蒙古：未找到频道 [' + param + ']，可用: ' + list.map(function (x) { return x.title; }).join('/'));
    var url = streamOf(hit);
    if (!url) throw new Error('内蒙古：频道 [' + param + '] 无 streamUrl');
    return url;
  }

  async function resolveAll() {
    var list = await fetchList();
    var out = {};
    list.forEach(function (x) { var u = streamOf(x); if (u) out[x.title] = u; });
    return out;
  }

  var fn = resolve;                 // window.__RESOLVERS.nmtv 本身是可调用函数
  try { Object.defineProperty(fn, 'name', { value: '内蒙古', configurable: true }); } catch (e) { fn.displayName = '内蒙古'; }
  fn.displayName = '内蒙古';
  fn.site = 'https://www.nmtv.cn/';
  fn.channels = CHANNELS;
  fn.resolve = resolve;
  fn.resolveAll = resolveAll;
  fn._xxteaEncrypt = xxteaEncryptB64;
  fn._xxteaDecrypt = xxteaDecryptB64;
  G.__RESOLVERS.nmtv = fn;
})(typeof window !== 'undefined' ? window : this);
