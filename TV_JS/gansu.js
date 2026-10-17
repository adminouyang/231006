/* ============================================================
 * 甘肃    key: gansu
 * ------------------------------------------------------------
 * 来源站点：https://www.gstv.com.cn/
 * 取流方式：纯静态地址，无需解析器
 * 频道数：6      最后更新：2026-10-16
 *
 * 本文件是 TVLive 的「甘肃」分组订阅文件，可直接手工修改后重新上传。
 * 改完记得同步 index.json 里本文件的 sha256（不想校验就写空字符串）。
 * ============================================================ */

/* ---- 1) 频道表：TVLive 启动时会读走这一段 ----
 * name      显示名（分组标题已写省份，这里不用再重复前缀）
 * url       兜底直连地址；带时效签名的台靠下面解析器现算，这里填旧的没关系
 * provider  解析器名，对应下面第 2 段里注册的名字；不需要就整行删掉
 * param     传给解析器的参数，一般是流名或频道 id
 */
TVRemote.define({
  key: "gansu",
  group: "甘肃",
  updated: "2026-10-16",
  note: "静态地址，无需解析",
  list: [
    { number: 195, name: "甘肃卫视", url: "https://live.gstv.com.cn/live/oxfhvoy.m3u8" },
    { number: 196, name: "甘肃文化影视", url: "https://live.gstv.com.cn/live/lg2va3a.m3u8" },
    { number: 197, name: "甘肃移动电视", url: "https://live.gstv.com.cn/live/j6od116.m3u8" },
    { number: 198, name: "甘肃少儿频道", url: "https://live.gstv.com.cn/live/456r6be.m3u8" },
    { number: 199, name: "甘肃科教频道", url: "https://live.gstv.com.cn/live/8lr1gvm.m3u8" },
    { number: 200, name: "甘肃公共应急", url: "https://live.gstv.com.cn/live/c6gljof.m3u8" }
  ]
});

/* ---- 2) 本组全部是静态地址，不需要解析器 ---- */
