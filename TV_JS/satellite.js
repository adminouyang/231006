/* ============================================================
 * 卫星电视（省级卫视 + 中国教育电视台）    key: satellite
 * ------------------------------------------------------------
 * 来源：央视频公开频道，pid 取流
 * 频道数：33     最后更新：2026-11-04
 *
 * 想给某个卫视换成本地直连流，两种写法：
 *   1) 加 url  → 就按直连流播，不再走央视频页面
 *   2) 加 urls → 一个台挂多条线路，右侧「线路选择」可手动切
 * 例：
 *   { name: "湖南卫视", url: "http://x.x.x.x:808/hls/204/index.m3u8",
 *     logo: "https://.../hunan.png", epg: "湖南卫视" }
 * ============================================================ */

TVRemote.define({
  key: "satellite",
  group: "卫星电视",
  updated: "2026-11-04",
  note: "32 个省级卫视 + CETV-1",
  list: [
    { number: 41, name: "北京卫视",     short: "北京卫视", pid: "600002309", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002309", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/北京卫视.png", epg: "北京卫视" },
    { number: 42, name: "江苏卫视",     short: "江苏卫视", pid: "600002521", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002521", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/江苏卫视.png", epg: "江苏卫视" },
    { number: 43, name: "东方卫视",     short: "东方卫视", pid: "600002483", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002483", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/东方卫视.png", epg: "东方卫视" },
    { number: 44, name: "浙江卫视",     short: "浙江卫视", pid: "600002520", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002520", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/浙江卫视.png", epg: "浙江卫视" },
    { number: 45, name: "湖南卫视",     short: "湖南卫视", pid: "600002475", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002475", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/湖南卫视.png", epg: "湖南卫视" },
    { number: 46, name: "湖北卫视",     short: "湖北卫视", pid: "600002508", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002508", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/湖北卫视.png", epg: "湖北卫视" },
    { number: 47, name: "广东卫视",     short: "广东卫视", pid: "600002485", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002485", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/广东卫视.png", epg: "广东卫视" },
    { number: 48, name: "广西卫视",     short: "广西卫视", pid: "600002509", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002509", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/广西卫视.png", epg: "广西卫视" },
    { number: 49, name: "黑龙江卫视",   short: "黑龙江卫视", pid: "600002498", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002498", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/黑龙江卫视.png", epg: "黑龙江卫视" },
    { number: 50, name: "海南卫视",     short: "海南卫视", pid: "600002506", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002506", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/海南卫视.png", epg: "海南卫视" },
    { number: 51, name: "重庆卫视",     short: "重庆卫视", pid: "600002531", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002531", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/重庆卫视.png", epg: "重庆卫视" },
    { number: 52, name: "深圳卫视",     short: "深圳卫视", pid: "600002481", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002481", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/深圳卫视.png", epg: "深圳卫视" },
    { number: 53, name: "四川卫视",     short: "四川卫视", pid: "600002516", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002516", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/四川卫视.png", epg: "四川卫视" },
    { number: 54, name: "河南卫视",     short: "河南卫视", pid: "600002525", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002525", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/河南卫视.png", epg: "河南卫视" },
    { number: 55, name: "福建东南卫视", short: "东南卫视", pid: "600002484", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002484", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/东南卫视.png", epg: "东南卫视" },
    { number: 56, name: "贵州卫视",     short: "贵州卫视", pid: "600002490", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002490", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/贵州卫视.png", epg: "贵州卫视" },
    { number: 57, name: "江西卫视",     short: "江西卫视", pid: "600002503", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002503", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/江西卫视.png", epg: "江西卫视" },
    { number: 58, name: "辽宁卫视",     short: "辽宁卫视", pid: "600002505", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002505", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/辽宁卫视.png", epg: "辽宁卫视" },
    { number: 59, name: "安徽卫视",     short: "安徽卫视", pid: "600002532", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002532", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/安徽卫视.png", epg: "安徽卫视" },
    { number: 60, name: "河北卫视",     short: "河北卫视", pid: "600002493", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002493", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/河北卫视.png", epg: "河北卫视" },
    { number: 61, name: "山东卫视",     short: "山东卫视", pid: "600002513", fallback: "https://m.yangshipin.cn/video?type=2&pid=600002513", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/山东卫视.png", epg: "山东卫视" },
    { number: 62, name: "天津卫视",     short: "天津卫视", pid: "600152137", fallback: "https://m.yangshipin.cn/video?type=2&pid=600152137", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/天津卫视.png", epg: "天津卫视" },
    { number: 63, name: "吉林卫视",     short: "吉林卫视", pid: "600190405", fallback: "https://m.yangshipin.cn/video?type=2&pid=600190405", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/吉林卫视.png", epg: "吉林卫视" },
    { number: 64, name: "陕西卫视",     short: "陕西卫视", pid: "600190400", fallback: "https://m.yangshipin.cn/video?type=2&pid=600190400", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/陕西卫视.png", epg: "陕西卫视" },
    { number: 65, name: "甘肃卫视",     short: "甘肃卫视", pid: "600190408", fallback: "https://m.yangshipin.cn/video?type=2&pid=600190408", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/甘肃卫视.png", epg: "甘肃卫视" },
    { number: 66, name: "宁夏卫视",     short: "宁夏卫视", pid: "600190737", fallback: "https://m.yangshipin.cn/video?type=2&pid=600190737", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/宁夏卫视.png", epg: "宁夏卫视" },
    { number: 67, name: "内蒙古卫视",   short: "内蒙古卫视", pid: "600190401", fallback: "https://m.yangshipin.cn/video?type=2&pid=600190401", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/内蒙古卫视.png", epg: "内蒙古卫视" },
    { number: 68, name: "云南卫视",     short: "云南卫视", pid: "600190402", fallback: "https://m.yangshipin.cn/video?type=2&pid=600190402", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/云南卫视.png", epg: "云南卫视" },
    { number: 69, name: "山西卫视",     short: "山西卫视", pid: "600190407", fallback: "https://m.yangshipin.cn/video?type=2&pid=600190407", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/山西卫视.png", epg: "山西卫视" },
    { number: 70, name: "青海卫视",     short: "青海卫视", pid: "600190406", fallback: "https://m.yangshipin.cn/video?type=2&pid=600190406", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/青海卫视.png", epg: "青海卫视" },
    { number: 71, name: "西藏卫视",     short: "西藏卫视", pid: "600190403", fallback: "https://m.yangshipin.cn/video?type=2&pid=600190403", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/西藏卫视.png", epg: "西藏卫视" },
    { number: 72, name: "新疆卫视",     short: "新疆卫视", pid: "600152138", fallback: "https://m.yangshipin.cn/video?type=2&pid=600152138", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/新疆卫视.png", epg: "新疆卫视" },
    { number: 73, name: "中国教育电视台 1 频道", short: "CETV-1", pid: "600171827", fallback: "", logo: "https://gitee.com/mytv-android/myTVlogo/raw/main/img/CETV1.png", epg: "CETV1" }
  ]
});
