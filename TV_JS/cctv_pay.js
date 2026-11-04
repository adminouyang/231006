/* ============================================================
 * 央视数字付费频道    key: cctv_pay
 * ------------------------------------------------------------
 * 来源：央视频公开频道
 * 说明：标清可看，超清需要央视频会员 —— 播不出来属正常，
 *       界面上会提示「这是付费频道」。
 * 频道数：13     最后更新：2026-11-04
 * ============================================================ */

TVRemote.define({
  key: "cctv_pay",
  group: "央视数字付费频道",
  updated: "2026-11-04",
  note: "标清免费，超清需会员",
  list: [
    { number: 28, name: "CCTV 第一剧场",     short: "第一剧场", pid: "600099655", fallback: "", premium: true },
    { number: 29, name: "CCTV 风云剧场",     short: "风云剧场", pid: "600099658", fallback: "", premium: true },
    { number: 30, name: "CCTV 怀旧剧场",     short: "怀旧剧场", pid: "600099620", fallback: "", premium: true },
    { number: 31, name: "CCTV 风云音乐",     short: "风云音乐", pid: "600099660", fallback: "", premium: true },
    { number: 32, name: "CCTV 风云足球",     short: "风云足球", pid: "600099636", fallback: "", premium: true },
    { number: 33, name: "CCTV 高尔夫·网球",  short: "高尔夫网球", pid: "600099659", fallback: "", premium: true },
    { number: 34, name: "CCTV 央视台球",     short: "央视台球", pid: "600099652", fallback: "", premium: true },
    { number: 35, name: "CCTV 兵器科技",     short: "兵器科技", pid: "600099649", fallback: "", premium: true },
    { number: 36, name: "CCTV 世界地理",     short: "世界地理", pid: "600099637", fallback: "", premium: true },
    { number: 37, name: "CCTV 女性时尚",     short: "女性时尚", pid: "600099650", fallback: "", premium: true },
    { number: 38, name: "CCTV 卫生健康",     short: "卫生健康", pid: "600099651", fallback: "", premium: true },
    { number: 39, name: "CCTV 电视指南",     short: "电视指南", pid: "600099656", fallback: "", premium: true },
    { number: 40, name: "CCTV 央视文化精品", short: "文化精品", pid: "600099653", fallback: "", premium: true }
  ]
});
