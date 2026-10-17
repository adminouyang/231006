/* ============================================================
 * 黑龙江    key: heilongjiang
 * ------------------------------------------------------------
 * 来源站点：https://www.dbw.cn/zhibodan/zhibo_dan/
 * 取流方式：纯静态地址，无需解析器
 * 频道数：7      最后更新：2026-10-16
 *
 * 本文件是 TVLive 的「黑龙江」分组订阅文件，可直接手工修改后重新上传。
 * 改完记得同步 index.json 里本文件的 sha256（不想校验就写空字符串）。
 * ============================================================ */

/* ---- 1) 频道表：TVLive 启动时会读走这一段 ----
 * name      显示名（分组标题已写省份，这里不用再重复前缀）
 * url       兜底直连地址；带时效签名的台靠下面解析器现算，这里填旧的没关系
 * provider  解析器名，对应下面第 2 段里注册的名字；不需要就整行删掉
 * param     传给解析器的参数，一般是流名或频道 id
 */
TVRemote.define({
  key: "heilongjiang",
  group: "黑龙江",
  updated: "2026-10-16",
  note: "静态地址，无需解析",
  list: [
    { number: 142, name: "黑龙江卫视", url: "https://idclive.hljtv.com:4430/live/hljws_own.m3u8" },
    { number: 143, name: "都市频道", url: "https://idclive.hljtv.com:4430/live/dushi_hd.m3u8" },
    { number: 144, name: "影视频道", url: "https://idclive.hljtv.com:4430/live/hljys_hd.m3u8" },
    { number: 145, name: "文体频道", url: "https://idclive.hljtv.com:4430/live/hljwy_hd.m3u8" },
    { number: 146, name: "农业·科教频道", url: "https://idclive.hljtv.com:4430/live/hljgg_hd.m3u8" },
    { number: 147, name: "新闻法治频道", url: "https://idclive.hljtv.com:4430/live/hljxw_hd.m3u8" },
    { number: 148, name: "少儿频道", url: "https://idclive.hljtv.com:4430/live/hljse_hd.m3u8" }
  ]
});

/* ---- 2) 本组全部是静态地址，不需要解析器 ---- */
