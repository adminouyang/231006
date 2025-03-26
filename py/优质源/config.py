ip_version_priority = "ipv4"

source_urls = [
    "https://gh-proxy.com/https://raw.githubusercontent.com/Guovin/iptv-api/gd/output/result.txt",
    "https://gh-proxy.com/https://raw.githubusercontent.com/adminouyang/dszby/refs/heads/main/py/iptv源收集检测/主频道/专享频道/♪酒店标清.txt",
    "https://gh-proxy.com/https://raw.githubusercontent.com/0047ol/China-TV-Live-M3U8/refs/heads/main/tv.m3u",#全国31个省市地方的电视台官网实时最新抓取
    "https://gh-proxy.com/https://raw.githubusercontent.com/q358162111/tvshow/refs/heads/main/tvlist.txt",#rtsp協議
    "https://gh-proxy.com/https://raw.githubusercontent.com/junge3333/yrys2026/refs/heads/main/2026yrys.txt",
    "https://raw.githubusercontent.com/meilirenTV/tv/refs/heads/main/zhibo.txt",
    # "https://gh-proxy.com/https://raw.githubusercontent.com/250992941/iptv/refs/heads/main/st1.txt",#酒店源为主、港澳、广东湖南的地方台
    "https://gh-proxy.com/https://raw.githubusercontent.com/frxz751113/IPTVzb1/refs/heads/main/综合源.txt",
    # "https://gh-proxy.com/https://raw.githubusercontent.com/frxz751113/IPTVzb1/refs/heads/main/网络收集.txt",#港台为主
    #"https://gh-proxy.com/https://raw.githubusercontent.com/dengmeiqing/IPTV1/refs/heads/main/live.txt",
   "https://gh-proxy.com/https://raw.githubusercontent.com/fudong305/iptv/refs/heads/main/gl.m3u",#轮播
   "https://gh-proxy.com/https://raw.githubusercontent.com/adminouyang/231006/refs/heads/main/tvbox/直播源/手动收集.txt",
    "https://live.zhoujie218.top/tv/iptv4.txt",
    "https://gh-proxy.com/https://raw.githubusercontent.com/junge3333/yrys2026/refs/heads/main/2026yrys.txt",#港台、轮播为主
   #"https://tv.youdu.fan:666/live/",#酒店源居多
    #"http://xhztv.top/zbc.txt",
    #"https://gh-proxy.com/https://raw.githubusercontent.com/zht298/IPTVlist/refs/heads/main/bh.txt",
    "http://home.jundie.top:81/Cat/tv/live.txt",
   # "https://gh-proxy.com/https://raw.githubusercontent.com/jiangyong9977/iptv/refs/heads/main/mytv.txt",
    # "https://gh-proxy.com/https://raw.githubusercontent.com/kimwang1978/collect-tv-txt/main/merged_output.txt",
    # "https://gh-proxy.com/https://raw.githubusercontent.com/vbskycn/iptv/refs/heads/master/tv/iptv4.txt",
    # "http://www.clmy.cc:35455/tv.m3u",#肥羊IPTV聚合
    # "http://wab201.win:35455/tv.m3u",#肥羊IPTV聚合
    # "http://146.235.213.45:35455/tv.m3u",#肥羊IPTV聚合
    # "",#yy轮播
    # "http://wab201.win:35455/yylunbo.m3u",#yy轮播
    # "http://www.clmy.cc:35455/yylunbo.m3u",#yy轮播
    "https://gh-proxy.com/https://raw.githubusercontent.com/isw866/iptv/refs/heads/main/iptv4.m3u"
]

url_blacklist = [
    "rtp",
    "udp",
    #"tsfile",
    "p2p",
    "P2p",
    "p3p",
    "epg.pw",
    "211.101.234.24:866",
    "113.57.111.4:1111",
    "60.7.56.33:4000",
    "zb.xmzb.xyz",
    "tv.bfsu.edu.cn",
    "p2.bdstatic.com",
"36.32.174.67:60080",
"39.170.52.236:808",
"221.226.4.10:9901",
"120.192.226.35:8009",
"60.172.130.146:352",
"227w9f5104.zicp.fun:35455",
"live1b.kxm.xmtv.cn",
"杂项代理",
"b.j.bkpcp.top",
"huanqiuzhibo.cn",
"delrvh.delacula.fun:35455",
"fy27.zbds.top",
"103.193.151.146",
"www.52sw.top:678",
"rihou.cc:555",
"61.133.118.228:5001",
"43.138.0.72:35455",
"api.olelive.com",
"t8622699o8.vicp.fun:60024",
"cdn.iptv8k.top",
"122.152.202.33",
"65.108.74.147:49366",
"58.200.131.2:1935",
"ivi.bupt.edu.cn:1935",
"cssbyd.imwork.net:8082",
"223.145.224.118",
"itv.uat.news:80",
"139.196.151.191",
"pve.grayidea.com",
"121.19.134.200:808",
"183.11.239.36:80",
"39.134.18.196",
"39.134.115.163:8080",
"183.94.1.118:8801",
"61.138.128.226:19901",
"112.123.206.32:808",
"123.182.60.29:9002",
"ldncctvwbndhwy.cntv.myhwcdn.cn",
"61.160.112.102:35455",
"push-rtmp-hs-spe-f5.douyincdn.com",
"mh0.asia:35455",
"218.93.208.172:35455",
"itv.nctv.top:35455",
    "m.951688.xyz:35455",
    "28918185.xyz:35455",
    "120.77.144.6:35455",
    "182.92.109.190:1668",
    "HlsProfileId=",
    "gouwu.pthvcdn.gitv.tv:91",
    "cookies.elementfx.com",
    "8.138.7.223",
    "isxzg.top:35455",
    "743d77.tv.netsite.cc",
    "fmbox.cc",
    "1732e975z9.zicp.fun:8082",
    "kkk.jjjj.jiduo.me",
    "stream1.freetv.fun",
    "api.livednow.org",
    "www.douzhicloud.site:35455",
    "jxcbn.ws-cdn.gitv.tv",
    "api.livednow.org",
    "3ad2a0.tv.netsite.cc",
    "gouwu.pthv.gitv.tv:91",
    "play.kankanlive.com",
    "fm1077.serv00.net",
    "150.158.112.123",
    "kxrj.site:1258",
    "kxrj.site:8081",
    "111.31.22.5",
    "223.105.252.60",
    "livetv.wqwqwq.sbs",
    "104.244.79.187:4994",
    "120.76.248.139",
    "117.161.12.116",
    "60.255.240.247:8090",
    "php.jdshipin.com",
    "2001:250",
    "111.20.40.171",
    "111.20.40.170",
    "59.49.41.41",
    "eastscreen.tv",
    "li0580.top:35455",
    "106.53.99.30",
    "p26.php?id",
    "153.99.64.96",
"cdn5.1678520.xyz:80",
    "ali.hlspull.yximgs.com",
    "38.64.72.148:80",
    "livetv.skycf.eu.org",
    "www.freetv.top",
    "cc-ynbit-wszhibo.ifengli.com:2000",
"home.zlm.cc:35455",
"audio",
"11.226.102.103:50001",
"k2p.251177.xyz:35455",
"snapshot-live-ht.ahtv.cn",
"kxrj.site:35455",
"tawangxunyuan.vicp.cc:35455",
"39.134.136.161",
"hangfun.top",
"60.246.171.122",
"119.8.31.109",
"hikvision.city",
"111.20.40.173",
"116.162.6.191",
"49.74.145.161",
"www.px663.cn",
"34.150.125.145",
"2311314.xyz",
"z.b.bkpcp.top",
"www.terrykang.xyz",
"mg.20191209.xyz",
"b.zgjok.com",
"hms3654nc3747353861.live.aikan.miguvideo.com",
"58.19.133.144",
"39.135.138.58",
"36.108.172.237",
"zw9999.cnstream.top",
"iptvrr.sh.chinamobile.com",
"hhxhhy.top",
"wanjiatv.net",
"hms3652nc3747353879.live.aikan.miguvideo.com",
"live.cooltv.top",
"php.17186.eu.org",
"2408:871a:a900:6::77",
"cdn9.1689.us.kg",
"182.40.120.186",
"hwltc.tv.cdn.zj.chinamobile.com",
"120.77.28.4:8648",
"jiaojirentv.top",
"189.1.239.118:35455",
"50.7.234.10:8278",
"iptv12k.com:35461",
"litv.zapi.us.kg",
"47.238.77.20:35455",
"szdjd.us.kg:35455",
"hulun.top:35455",
"8.138.47.46:35455",
"a21709.tv.netsite.cc",
"bf11e1.tv.netsite.cc",
"wab201.win:35455",
"dd.ddzb.fun",
"kxrj.site:64325",
"tvbox.nat.netsite.cc:8043",
"2409:8087",
"113.64.145.91",

"zhibo.hkstv.tv",

"vip.ffzy-play7.com",
"39.134.66.110",
"0472.org",
"lunbo.freetv.top",
"live.mastvnet.com",
"222.71.90.218",
"39.134.67.108",
"8.138.90.107",
"ali.hlspull.yximgs.com",
"httpdvb.slave.shuliyun.com",
"cg12.hunancatv.cn",
"tvpull.dxhmt.cn",
"live.hndachao.cn",
"livehls1.appcoo.com",
"tv.pull.hebtv.com",
"223.109.210.41",
"1.94.31.214",
"php.jdshipin.com",
"60.11.200.120:35455",
"sdytqsy.top:35455",
"3501776.xyz:35455",
"nas.zyylover.homes:35455",
"19900625.xyz:35455",
"39.108.238.101:35455",
"103.115.40.138:35455",
"189.1.219.223:35455",
"223.105.252.59",
"k44991.kylintv.tv",
"www.terrykang.cn:5678",
"203.205.220.174:80",
"r.jdshipin.com",
"116.162.6.192",
"103.95.24.37:880",
"cdn5.1678520.xyz",
"146.56.153.245:20121",
"null3",
"playtv-live.ifeng.com",
"tianhewan.top",
"203.205.220.174:80",
"cdn.132.us.kg",
"cdn3.132.us.kg",
"148.135.93.213:81",
"218.202.220.2:5000",
"cctvtxyh5c.liveplay.myqcloud.com",
"tv.iill.top",
"223.105.252.8",
"146.235.213.45:35455",
"tv.kmhlzxs.top:35455",
"47.93.13.98:35455",
"feiyang.ak47s.top:35455",
"home.dzlove.top:35455",
"tvbox6.icu",
"110.42.45.89:35455",
"gslbserv.itv.cmvideo.cn:80",
"zteres.sn.chinamobile.com:6060",
 "119.91.33.253",
"goo.bkpcp.top",
"112.74.115.68:35455",
"szd5.com:35455",
"www.52iptv.vip:35455",
"hwrr.jx.chinamobile.com:8080",
"rtsp",
"dsm.huarunguoji.top:35455",
"iptv.0564.org:35455",
"161888.xyz:35455",
"nn.7x9d.cn",
"newtv.fun:35455",
"haoyunlai.serv00.net",
"xiaoya.crccxw.top:35455",
"ttkx.cc:1380",
"115.229.24.84:8866",
"gslbserv.itv.cmvideo.cn",
"www.52iptv.vip:35455",
"lt.hxtre.com:35455",
"dl.wifi942.com:66",
"117.144.58.42:35455",
"111.170.172.113:35455",
    "13937899.xyz:35455",
"hotelplay.net",
"tv.20191209.xyz:37377",
"2000.run:35455",
"php.666230.xyz",
"36.105.100.208:35455",
"231114.xyz:35455",
"ott.eonn.cn:35455",
"1.itv.nctv.top:35455",
"http://home.wwang.pw:35455",
"36.105.100.208:35455",
"998969.xyz:35455",
"1972386346:35455",
"www.clmy.cc:35455",
"111.29.9.33:6610",
"otttv.bj.chinamobile.com",
    "tvbox6.com",
"223.105.252.57",
"app.baiyels.com:50001",
"47.92.130.115:9000",
"4330413.xyz:35455",
"yunmei.tv",
"live.wqwqwq.sbs",
"xxx.504900.xyz:35455",
"127.0.0.1",
"iptv.diyp.site",
"27.222.3.214",
"3.itv.nctv.top",
"quan2018.mycloudnas.com:51888",
"aktv.top",
"iptv.diyp.tech",
"58.144.154.93:80",
"wo.xiang.lai.ge.bi.jiao.chang.de.yu.ming.wan.wan.jie.xi.bu.zhi.dao.ke.bu.ke.xing.hk3.345888.xyz.cdn.cloudflare.net",
"kxrj.site:1333",
"148.135.34.95",
"anren.live",
"stream.qhbtv.com",
"j.x.bkpcp.top",
"www.shqsy.com",
"antvlive.ab5c6921.cdnviet.com",
"live.v1.mk",
"live.nctv.top",
"gf.you123.fun:35455",
"iptv.luas.edu.cn",
"live.goodiptv.club",
"dsk.cc",
"live.sjsrm.com",
"2d026c.tv.netsite.cc",
"bladecld.us.kg:50001",
"cdn5.163189.xyz",
"205.185.120.154:50001",
"iptv77.iptv66.eu.org:35455",
"54.200.240.27:35455",
"global.cgtn.cicc.media.caton.cloud",
"61.160.112.102:35455/itv",
"ygbh.live",
"www.yangshipin.cn",
"lu.wqwqwq.sbs",  
]
url_whitelist = [
    "ottrrs.hl.chinamobile.com",
    "39.135.133.154",
    "39.135.133.155",
    "39.135.133.157",
    "39.135.133.174",
    "39.135.133.177",
    "39.135.133.167",
    "39.135.135.28",
    "rtsp",
    "gaoma",
    "majian.ixiaobai.net:5540",


]

announcements = [
    # {
    #     "channel": "公告",
    #     "entries": [
    #         {"name": "请阅读", "url": "https://liuliuliu.tv/api/channels/1997/stream", "logo": "http://175.178.251.183:6689/LR.jpg"},
    #         {"name": "yuanzl77.github.io", "url": "https://liuliuliu.tv/api/channels/233/stream", "logo": "http://175.178.251.183:6689/LR.jpg"},
    #         {"name": "更新日期", "url": "https://gitlab.com/lr77/IPTV/-/raw/main/%E4%B8%BB%E8%A7%92.mp4", "logo": "http://175.178.251.183:6689/LR.jpg"},
    #         {"name": None, "url": "https://gitlab.com/lr77/IPTV/-/raw/main/%E8%B5%B7%E9%A3%8E%E4%BA%86.mp4", "logo": "http://175.178.251.183:6689/LR.jpg"}
    #     ]
    # }
]

epg_urls = [
    "https://live.fanmingming.com/e.xml",
    "http://epg.51zmt.top:8000/e.xml",
    "http://epg.aptvapp.com/xml",
    "https://epg.pw/xmltv/epg_CN.xml",
    "https://epg.pw/xmltv/epg_HK.xml",
    "https://epg.pw/xmltv/epg_TW.xml"
]
