/* ============================================================
 * 河北    key: hebei
 * ------------------------------------------------------------
 * 来源站点：https://www.hebtv.com/
 * 取流方式：纯静态地址，无需解析器
 * 频道数：7      最后更新：2026-10-16
 *
 * 本文件是 TVLive 的「河北」分组订阅文件，可直接手工修改后重新上传。
 * 改完记得同步 index.json 里本文件的 sha256（不想校验就写空字符串）。
 * ============================================================ */

/* ---- 1) 频道表：TVLive 启动时会读走这一段 ----
 * name      显示名（分组标题已写省份，这里不用再重复前缀）
 * url       兜底直连地址；带时效签名的台靠下面解析器现算，这里填旧的没关系
 * provider  解析器名，对应下面第 2 段里注册的名字；不需要就整行删掉
 * param     传给解析器的参数，一般是流名或频道 id
 */
TVRemote.define({
  key: "hebei",
  group: "河北",
  updated: "2026-10-16",
  note: "长效签名，无需运行时解析",
  list: [
    { number: 84, name: "河北卫视", url: "https://tv.pull.hebtv.com/jishi/weishipindao.m3u8?t=1854721069&k=ca557faf4d869ca5959ee951a3da2817" },
    { number: 85, name: "经济生活", url: "https://tv.pull.hebtv.com/jishi/jingjishenghuo.m3u8?t=1854721069&k=d0dc5f98c0a6e6ba05ee29bcaf1e47b8" },
    { number: 86, name: "河北都市", url: "https://tv.pull.hebtv.com/jishi/dushipindao.m3u8?t=1854721069&k=50ffb8a4f5bdbdec2e065070270be4f7" },
    { number: 87, name: "文旅体育", url: "https://tv.pull.hebtv.com/zhibo/yingshijupindao.m3u8?t=1854721069&k=afb488aeb63597c27f492e9f5119db0d" },
    { number: 88, name: "少儿科教", url: "https://tv.pull.hebtv.com/jishi/shaoerkejiao.m3u8?t=1854721069&k=6ae75550d56c7015e1bde55c70d4e288" },
    { number: 89, name: "三农频道", url: "https://tv.pull.hebtv.com/jishi/nongminpindao.m3u8?t=1854721069&k=b9bdd261af5c0d350bff69068d12d055" },
    { number: 90, name: "三佳购物", url: "https://tv.pull.hebtv.com/zhibo/sanjiagouwu.m3u8?t=1854721069&k=b3c314abb1f852852c1c8c926cf36ff0" }
  ]
});

/* ---- 2) 本组全部是静态地址，不需要解析器 ---- */
