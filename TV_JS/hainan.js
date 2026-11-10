/* ============================================================
 * 海南    key: hainan 
 * ------------------------------------------------------------
 * 来源站点： https://www.hnntv.cn/
 * 取流方式：纯静态地址，无需解析器
 * 频道数：3      最后更新：2026-11-10
 *
 * 本文件是 TVLive 的「海南」分组订阅文件，可直接手工修改后重新上传。
 * 改完记得同步 index.json 里本文件的 sha256（不想校验就写空字符串）。
 * ============================================================ */

/* ---- 1) 频道表：TVLive 启动时会读走这一段 ----
 * name      显示名（分组标题已写省份，这里不用再重复前缀）
 * url       兜底直连地址；带时效签名的台靠下面解析器现算，这里填旧的没关系
 * provider  解析器名，对应下面第 2 段里注册的名字；不需要就整行删掉
 * param     传给解析器的参数，一般是流名或频道 id
 */
TVRemote.define({
  key: "hainan",
  group: "海南",
  updated: "2026-11-10",
  note: "静态地址，无需解析",
  list: [
    { number: 1, name: "海南卫视", url: "http://hainan.lbds.us.ci/?id=13" },
    { number: 2, name: "三沙卫视", url: "http://hainan.lbds.us.ci/?id=5 },
    { number: 3, name: "海南自贸", url: "http://hainan.lbds.us.ci/?id=1" },
	{ number: 4, name: "海南新闻", url: "http://hainan.lbds.us.ci/?id=3" },
	{ number: 5, name: "海南社会与法", url: "http://hainan.lbds.us.ci/?id=4" },
	{ number: 6, name: "海南文旅", url: "http://hainan.lbds.us.ci/?id=6" },
	{ number: 7, name: "海南少儿", url: "http://hainan.lbds.us.ci/?id=7" }
  ]
});

/* ---- 2) 本组全部是Cloudflare Worker，不需要解析器 ---- */
