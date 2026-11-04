/* ============================================================
 * 央视公共频道    key: cctv
 * ------------------------------------------------------------
 * 来源：央视频 TV 页（https://www.yangshipin.cn/tv/home）的公开频道
 * 取流方式：pid（央视频整页播放），不需要解析器
 * 频道数：21      最后更新：2026-11-04
 *
 * 这一组以前是「装在 APK 里」的，v2.4 起统一挪到 TV_JS 远程，
 * 改台 / 改 pid / 加台标都只改这个文件，不用重新打包。
 *
 * 字段速查（详细说明见 README）：
 *   number    频道号（只是排序提示，App 会按位置重排）
 *   name      显示名
 *   short     简称，可空（台标文字用）
 *   pid       央视频频道 id —— 有它就按「央视频整页」播
 *   fallback  备用网页地址（央视网直播页），可空
 *   url       直连流地址（m3u8 / ts）—— 有它就优先当直连流播
 *   urls      多条线路，写成一个数组
 *   logo      台标图片地址，可空
 *   epg       EPG 里的频道 id（tvg-id），可空
 *   premium   付费频道标记，可空
 * ============================================================ */

TVRemote.define({
  key: "cctv",
  group: "央视公共频道",
  updated: "2026-11-04",
  note: "CCTV-1~17 及 4K / 8K，央视频公开源",
  list: [
    { number: 1,  name: "CCTV-1 综合",       short: "CCTV-1",  pid: "600001859", fallback: "https://tv.cctv.com/live/cctv1/",      logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV1.png",  epg: "CCTV1" },
    { number: 2,  name: "CCTV-2 财经",       short: "CCTV-2",  pid: "600001800", fallback: "https://tv.cctv.com/live/cctv2/",      logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV2.png",  epg: "CCTV2" },
    { number: 3,  name: "CCTV-3 综艺",       short: "CCTV-3",  pid: "600001801", fallback: "https://tv.cctv.com/live/cctv3/",      logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV3.png",  epg: "CCTV3" },
    { number: 4,  name: "CCTV-4 中文国际",   short: "CCTV-4",  pid: "600001814", fallback: "https://tv.cctv.com/live/cctv4/",      logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV4.png",  epg: "CCTV4" },
    { number: 5,  name: "CCTV-5 体育",       short: "CCTV-5",  pid: "600001818", fallback: "https://tv.cctv.com/live/cctv5/",      logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV5.png",  epg: "CCTV5" },
    { number: 6,  name: "CCTV-5+ 体育赛事",  short: "CCTV-5+", pid: "600001817", fallback: "" },
    { number: 7,  name: "CCTV-6 电影",       short: "CCTV-6",  pid: "600108442", fallback: "https://tv.cctv.com/live/cctv6/",      logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV6.png",  epg: "CCTV6" },
    { number: 8,  name: "CCTV-7 国防军事",   short: "CCTV-7",  pid: "600004092", fallback: "https://tv.cctv.com/live/cctv7/",      logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV7.png",  epg: "CCTV7" },
    { number: 9,  name: "CCTV-8 电视剧",     short: "CCTV-8",  pid: "600001803", fallback: "https://tv.cctv.com/live/cctv8/",      logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV8.png",  epg: "CCTV8" },
    { number: 10, name: "CCTV-9 纪录",       short: "CCTV-9",  pid: "600004078", fallback: "https://tv.cctv.com/live/cctvjilu/",   logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV9.png",  epg: "CCTV9" },
    { number: 11, name: "CCTV-10 科教",      short: "CCTV-10", pid: "600001805", fallback: "https://tv.cctv.com/live/cctv10/",     logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV10.png", epg: "CCTV10" },
    { number: 12, name: "CCTV-11 戏曲",      short: "CCTV-11", pid: "600001806", fallback: "https://tv.cctv.com/live/cctv11/",     logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV11.png", epg: "CCTV11" },
    { number: 13, name: "CCTV-12 社会与法",  short: "CCTV-12", pid: "600001807", fallback: "https://tv.cctv.com/live/cctv12/",     logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV12.png", epg: "CCTV12" },
    { number: 14, name: "CCTV-13 新闻",      short: "CCTV-13", pid: "600001811", fallback: "https://tv.cctv.com/live/cctv13/",     logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV13.png", epg: "CCTV13" },
    { number: 15, name: "CCTV-14 少儿",      short: "CCTV-14", pid: "600001809", fallback: "https://tv.cctv.com/live/cctvchild/",  logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV14.png", epg: "CCTV14" },
    { number: 16, name: "CCTV-15 音乐",      short: "CCTV-15", pid: "600001815", fallback: "https://tv.cctv.com/live/cctv15/",     logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV15.png", epg: "CCTV15" },
    { number: 17, name: "CCTV-16 奥林匹克",  short: "CCTV-16", pid: "600098637", fallback: "https://tv.cctv.com/live/cctv16/",     logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV16.png", epg: "CCTV16" },
    { number: 18, name: "CCTV-16 奥林匹克 4K", short: "CCTV-16 4K", pid: "600099502", fallback: "" },
    { number: 19, name: "CCTV-17 农业农村",  short: "CCTV-17", pid: "600001810", fallback: "https://tv.cctv.com/live/cctv17/",     logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CCTV17.png", epg: "CCTV17" },
    { number: 20, name: "CCTV-4K 超高清",    short: "CCTV-4K", pid: "600002264", fallback: "" },
    { number: 21, name: "CCTV-8K 超高清",    short: "CCTV-8K", pid: "600156816", fallback: "" }
  ]
});
