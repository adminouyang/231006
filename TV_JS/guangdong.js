/* ============================================================
 * 广东    key: guangdong
 * ------------------------------------------------------------
 * 来源站点：https://www.gdtv.cn/tvChannelDetail/43
 * 取流方式：itouchtv 签名链
 * 频道数：17      最后更新：2026-10-16
 *
 * 本文件是 TVLive 的「广东」分组订阅文件，可直接手工修改后重新上传。
 * 改完记得同步 index.json 里本文件的 sha256（不想校验就写空字符串）。
 * ============================================================ */

/* ---- 1) 频道表：TVLive 启动时会读走这一段 ----
 * name      显示名（分组标题已写省份，这里不用再重复前缀）
 * url       兜底直连地址；带时效签名的台靠下面解析器现算，这里填旧的没关系
 * provider  解析器名，对应下面第 2 段里注册的名字；不需要就整行删掉
 * param     传给解析器的参数，一般是流名或频道 id
 */
TVRemote.define({
  key: "guangdong",
  group: "广东",
  updated: "2026-10-16",
  note: "itouchtv 多级签名链",
  list: [
    { number: 214, name: "广东卫视", url: "https://tcdn.itouchtv.cn/live/gdws.m3u8?t_token=77214d736ec48941a715001192a8df84-qWcaChPGzWD%2BaHER6tttDLaxhOoPc0Y3yaJ7vpZZ%2FUtyzZy%2FcpGl1CLjapQpKrx1ZnKySJ7P%2FqnJ3VjnPVipbc%2BIQPyYk33bhz%2BPYv9MA6DSvRUYXtaeYMk4OT3UWw0ZDo6nVtu0lhLBkaVmRguT0dy0ZF1iHQ%2B%2FczP3jAhNGNJKIL5FbTCiD%2Far9LW%2FD7HJNGM85luwPcuSldTIsV4M3w%2BlD06AMwzehZnqQ7eMlNxc%2F2zyG9MLv0QNuZZIK6YUvO7ODdQLZly%2FJi4fFXQoh7E4rfM2ZW2IlqIJw8LaUQjK%2BO1sMdwOnZVMVaAt5sIfHtKqJGBSoP2ihInwFfqbSB4YleLB66r3Y4IXjmVU7d68g4O7uxz51JqNoKLBZ3UOl5PCZH0gJG21BgrP59w6pQ%3D%3D", provider: "guangdong", param: "gdws" },
    { number: 215, name: "广东珠江", url: "https://tcdn.itouchtv.cn/live/gdzj.m3u8?t_token=7c7ce093ebfac49780c106f68eab14ed-YrksPDDFpngKjmHIqQynrUGX107tJnNsmKU44WvAyqSd4YDL9N6%2FPJQADFMweqZRUmvn5YwwXEdz6Ew78fXmxEPlAifNDWh5P57HfpqTiKJH58BrOA6l%2BJZvQ1aMoO4vqrbyP6ONVFK50LcGaBwVXmmZGEmxWkmmrCEYZYVc8WCdZ2%2B7yy9pTNaLeVwubQENB7xadVYVzfT6JtHpr4jjkIhUHii4ini62oQ9W7bUvqKWarP6zQC4PfA%2Bvj8pNvwUMfK1N22HRHafu56qKgQCpOT9YKW7ICHPkK3WB0xREuiWalYblWZg4fX6zPWiDmbT6lfvt8WOxqjAWgqxA19Sv6DVO01uTJg2%2F2XvFCHZCSy8z7YiTp785BIDpTyKMXIxsEdaW%2FsM%2B%2BITo9bAxdsXDQ%3D%3D", provider: "guangdong", param: "gdzj" },
    { number: 216, name: "广东新闻", url: "https://tcdn.itouchtv.cn/live/xwpd.m3u8?t_token=9fef1a1038318d5fb2db4b0c194d9143-bewVVBW4i4Trdg%2FriHE1%2F3DCh4KrqFIsnhOKNhGWAnsrWOhE79ThHzdSneT%2BSLf2stnYz%2FBLCN1dhgd70Q4stfJ4JpMM26GcsLkRgIsDDvYBBki9W98OAoTTm3AKO7H9azDqAUj2F5ZkXhYyFz5bugWZzP48xuOVazCO5atZ8mET17z4w%2FZSLuRGYp6Yb6ypOpiF4c8yjHknrYnuyx4ONnMpjCQTodF%2Bkd9YcUMBiLammT0r2K3NxpGnKtdoQFsxqYMnJyX3h5W09jA7OIrBE4tWJOR4uRqYcRWcyoIXD68vvW1f0ObzqF0dNXAVLz96p3S5iD0MeD3v9gdN9vLtIykGpJiR4HX2TF6RlQux6NtZp9VMbM9yJSvwnJ7W7xPFszIl9G9EV09kt7j1USX1eg%3D%3D", provider: "guangdong", param: "xwpd" },
    { number: 217, name: "广东民生", url: "https://tcdn.itouchtv.cn/live/gdgg.m3u8?t_token=f3d567972ca43fa9a51ee88dd3ba3562-Jq1Qom8QRZgJUQ9bOau6VjR7YvgcPsab6Ubm%2F9sKDBhxbaCD9t4Gue82LggEHBVu5D%2FwgqC3fU4VR07C%2BQoZP%2BY5oiYxUUd9GLUdRmgx8QzMnK4xkUrJcb%2BCkww6AjjP5D9a3ROl%2BJFGDXbL69AOZgykRDqbpgzBXYIK55sAfS3jOtK4wlJQuWtc5qEMZihBgeixHchSTwZMp55S%2BualH%2BHATz92DtLeJEVm68DC2g6TqJ%2FEOfaX52Vdl%2F6q7F0TcdXHjXhykrNKXSTz5Zfw4u%2BOZVbTXOnR6IvE%2FQW7I%2FMzXaPg1a%2BoKlHq4w8pmfOklVywY78j591f8V%2FzRYoI7pPS9CtAcpxJI97EJr7BOD1R8cGqJGlAn%2Bu%2BXq5iunEmj0fUsiMecxnpKFVbUJ7bZA%3D%3D", provider: "guangdong", param: "gdgg" },
    { number: 218, name: "广东体育", url: "https://tcdn.itouchtv.cn/live/gdty.m3u8?t_token=8058a9fbda389005e6621dba8e094f56-LLwx2oeyEQII3DIcb2uvyqjqaEDVw4xvMUwvIwxuijb820EaEgfB7wUlldruhhVmvnJx8GcRQGcF%2BqzmyQ5BJ5Z4kOQ3vHNydOfiQuW8XSCprjnqkf%2BAH3fQ6T7UPE7yA622%2FLr37tmzGyfPhmLjSe1zAAuUquC8HKfHv5FVWSN1rGiqN6rxyTORKMaWBbir%2Bm91HlgBBYLslCZHEQb03rh0riYUNxpKspQEYLkkOPlW6T8W%2B%2FHmLLT0Pdtqom2fTZ1B9dH%2Fb1JI3Y4xzS3%2BzWqsed4Y7fbqJVhumfLz3cNIc553IBoz6QmKnJwgtQZVOfxm%2BTDM0b6T%2FSF7%2FjaQWIPH9tEwar05lUiyBpYUzjz8wPsWYn0xEujmzfHNDLjUUEmiDQt6V6X6iIwajCbvOQ%3D%3D", provider: "guangdong", param: "gdty" },
    { number: 219, name: "大湾区卫视", url: "https://tcdn.itouchtv.cn/live/nfws.m3u8?t_token=0001a9b66d9eab7a07981fc3efcfe974-K3TjycVdE9y8VtWIG0IaVF69u9i9hXr%2FdH%2BhpT%2B9MzkLBX00mBZY2%2B5LD0ppGHHtXYTSBv7sXcsFTliYmbfxED%2BY3ttinww0jj%2F2%2BGlGuULik0nJnPjrJgscs9Oi5%2BSKh1Hsecrw8gxShy0B%2B3pgd7BUv7Ph0XXfPOCKFdDqB2CCT8QoHnDw4JO8jic5a82YzM9pemNuEgwAtZLmLtapCl5G1jgPbthCUosvJSahZ29%2BJvGfsAaWADMwJMNMmZuiv8iijO0irNENsBc7XY8siHrr8L%2BMHI2B%2B%2B%2F15HvGMKYfQEBgvslUaoBCZYI3AK1%2BPL7eVv%2Fr4O0Yu93ACZICM4EbbGPzoAcTIQGKzdhr12Y2o%2BldWgSRT9Bn1xWCycjhD14BssAkgu3TK5Ko4kIwtg%3D%3D", provider: "guangdong", param: "nfws" },
    { number: 220, name: "大湾区卫视（海外版）", url: "https://tcdn.itouchtv.cn/live/gdgj.m3u8?t_token=e49c2acc1c56fc9a3bc1d9fe425d46fa-IufdHX%2Fj5%2FmNOMKVVCkC6pKbZ23XxzvolSZ2VKAA5xAps7pa5G1yd7lrNRix2OLi4%2B825VvuBUiE0MHXH%2FNkfGFKVsg8Jd5GTuxxK1lwcYCQqAyCquNkLS%2FOSzi%2Fy2UPjIXOWqVxKNfcub7S9ai1qiimvvENTUdI%2FhNte3%2FSLWE9iuPZ%2BpYEKeyQEyoX5iXcYiuk9Q8myVHW1dyvXGQRE860iO6oZeSVd%2FCDau6j52MHDgzzhEXa5kc5HZYORiAM2TgGbIb%2Fkjr3bsjY9ipPlLmm1HgFF6OS3dq%2FKoi9OEsu6SHsDTpTl8OTOtbB9CuEjwlIEPuUgBNTzyR4yG2K4eW69u6V%2FGJ%2FW%2B2WV2XycUCKGkNzAHt05%2FAy9sfq8UGGf%2B31K2NxBOrN1E5sgmxchw%3D%3D", provider: "guangdong", param: "gdgj" },
    { number: 221, name: "广东影视", url: "https://tcdn.itouchtv.cn/live/gdys.m3u8?t_token=1dff7517c4c8d98a08617f1e8c2fb8cc-RieAwfOf2hKLlM3acXgsxxqP3gob%2FZ4Ay77MjL7U0ViOdNQzGyRb0A8JVifQO%2Fylv8v6iutzjuvf8jXTnyOwLJN2g29v2Db3x6ryxClyIz2%2BOEuT43NJyH%2BqfRgLJ1kS%2BVGw3gh8P%2F9%2B8LqwGJAFeUS5%2BHQx8lITdb%2FL0L1x8nPcGsmQV%2F2sSC9xw2BY9YPxgPw%2F3H%2FG3v8MYKBqjVwvbDpTjM%2Fn61ehUnhocRcsTDzL5keDRGhgWso0d%2FeWgFgyKgcDh8m79EHQUrtqOUPa0OShF7wuIs0vVrkT7ng9EOll49%2FNpTc56O3w6zNCG12SLhACIxCCpEkmcXvNhResDqsbZRrf47LFWEGe0wN4tMspWLu5LOpemOyK0HPej6aOuQ2y8dICIKJMQ89ZICOCRA%3D%3D", provider: "guangdong", param: "gdys" },
    { number: 222, name: "4K超高清", url: "https://tcdn.itouchtv.cn/live/gdzy.m3u8?t_token=4cb5bf050689373631242f4c4928c104-wx3rBYVZ7l%2FE4LdZ4D2MmlyFBPXlopjMHdz26f7cZTKasrEQJd6aASxq00qEOZxu%2B%2FBQhNtIXUcEnTL8OFymFm34xOA%2B8bjCs8qnDbMTo93sEwE0FZsgShoD1E73E2CwoxzLGZ65tV0v0KdxxMJ36YvEb8UNw2Mru0Vuot%2Fgz1Hld2mTAiOkdn6AHsHcFG6n8L1KpdR7zgoMjUIyssa92vOcWA7uSh%2FQEHQhDu8U9%2Fm3BP%2BmmtfU%2Fgwp7ea2NfohoYZmXJ27Ql9%2Bc8Yr1YlPN7WSJODXzTLfHrP6Hv9DjI1J%2FWqDMaHUhi810fIaNrmZCj3PAY%2Fw5%2B9HpCB04u3EWjtKqkV1NBrQQ%2B%2FpTOej7B7O0iyOgU0sNWfAozWrKcN833uqB6Zow4M7ZhWQFyv%2FyQ%3D%3D", provider: "guangdong", param: "gdzy" },
    { number: 223, name: "广东少儿", url: "https://tcdn.itouchtv.cn/live/gdse.m3u8?t_token=e83730ebe0f19adc6655c350936ec288-gfXsejqD5O984FWrFfsWWkMX5gvs8oOftghfot4YPgXg6%2FA7yeVcZAA3Xk1V6nfe4LT6aJRe%2FDhj3lxDiQ6s9wh7mLc0Zy87dEvRu2d9auGlNumqR7J5uG3%2FS76xYf9ovAL9TTcxmZzaaLxhOqcJmMjXCQzxs3YWlzb8sVoCcXCO9xcKGM8xqJk5%2FG788yxqoKDEJQF%2BSpuBD4xm5v%2BEJbYrYQM5z6K2QgU2kN8XF2%2FSxEJ7bao60ZjR8ah%2BsfMtljfaFxsV%2FlIom%2FYC%2BHTBBT7Bne5%2BGLh%2BsSpqS%2BYFw9I5ztLbBGR2oXJ6eACSmO2keQe%2FjKBi4y4mNVpEn9FNm8cRnAr83VLzO1V1wQF%2FvH3nlJZ0E9OILoi0%2FOYod%2BQsSe2TRawQ2C1xQcB4NNC5EQ%3D%3D", provider: "guangdong", param: "gdse" },
    { number: 224, name: "嘉佳卡通", url: "https://tcdn.itouchtv.cn/live/jjkt.m3u8?t_token=2d2d80c42c0f8e2067ec4db61b32ef71-g27ZIPAvotvjBSghca8FqgaGfXr47GLEBv2skfgVaGNTVQq7aewXLv1aFs8gliFVfilUoZ02STy0gDQE3jTQwfVltCIYRD7sYdjgRAF658uGozrbriF8Z4fcb56t48SX3Dp7ncUpXQpcRnGQh069pU6TAT9HzgQLHWhFx1UPevoaVE5QvCw%2BIK3FA%2B%2BWI1JQMykbVmGRWmgDk6txK7ccdEZgauscHyB98sJUxYdW4y6QIhNr%2Fb8czl%2BsHEahogm0FthFhSJ8Q7n0T3bCJDtpA%2BWo%2BjfDqJclBj3EXjRlrFZcMXdNmRH9%2FNKQiWUMI4yXitb6dI0UaXR82g9Ylx03N%2Fde8XMhP4ZUBqMbd5X%2BxGbdsqOYhzzukgLW%2FXyq6WjLqPK4DNB5Eg3obp7yaRWhLQ%3D%3D", provider: "guangdong", param: "jjkt" },
    { number: 225, name: "南方购物", url: "https://tcdn.itouchtv.cn/live/nfgw.m3u8?t_token=eb4ad01ec18079a6743fab47baf4c057-r%2FxLRrAWfssQjHndHEu01GhtFG6CaFM3V7jHSHeGw%2F%2BmJCkJOZQCioOBBbLyFA52%2F1Qip38XIPDYLcZHuAQkejceqAeTZFvTWSDzEGkO0l%2BfT%2FYRIaYaVNUUv6G1g2Ya5WtD3A33O%2BPh79QE%2BvAg0%2FVC5sUk%2B0GY7cZEfG%2FkL0COOA9XbvQe3%2BakFw%2B%2B7Z%2FxwrXQc1pt1YWvBtQ2I85FS4KA5Xs%2B4Cvu7osvrsm5%2B2LlY611o%2FlazhVa3XEHKCAMKi9wSkdMXCNQjyhsb10ZkMdJxdGGUvX2EimuHTaAYI07beco%2BoDecx9LA4sqKGnYVQ0WF443K6ory9yfPHXIl7tCofCh0JviX02MSS0rcixbWMlHtbZ3aMW19t6yzpBZeWa%2FAiH4N1jGACGC3xL3iA%3D%3D", provider: "guangdong", param: "nfgw" },
    { number: 226, name: "岭南戏曲", url: "https://tcdn.itouchtv.cn/live/lnxq.m3u8?t_token=b35b3baf1fb597a03be0e6474668d9d7-7uZagvhpyUGPN2mLbqyPToiQ%2F1DED7RQIryromfGnYH98GNf6jMTcyswOYAyyCNmk1xdHoHkaonA%2FpQgUVYOuftOm5QfBGDTbQxdWiEqOc0nuk4ShYSJD7FAhNQsdqOMoZuZ2DqHHUeIp9%2FwQ9VTG4jMpJlhBH%2FOd9ITYOXSIYpctlh69YtmLtZ4iOIxszaFXMu9s2lsAvXi5fSfCFuT8%2BRhcJiwmg3kPSJw0UKeJoT9t9yUrIOCzZYJBGVh4XCw%2FHDLhH%2Btp8VeAGxB8IU561QNOROLkGHnqE04Emn2zsuCRi68AwfEpU9FXEXxjZIlxxJ6bEa%2F5ZNLEdBG8rQxeMl40npwUd6wX4qew%2FysLSivwiV5CBPS3jLgu60fWhU3AkO2jONoVVTndWeblbL7mA%3D%3D", provider: "guangdong", param: "lnxq" },
    { number: 227, name: "广东移动", url: "https://tcdn.itouchtv.cn/live/ydpd.m3u8?t_token=2671f1e384b6276f6bcd4866a6f44cda-POSwPU8crtemOGHD2%2B4YbTBHH5nuEX9geTvDzwkI9Sja1WmhT1sFxS5H4iybTPvBDRaM%2FMyVJTb5ofYvygMozVVfZUM0eR3Nn0RO9jDefhOJToy0IM88Jo7la1%2FCBpAyRqru7LR4Lx9z9BmR7OoUUXVOvqqaAVJMi0cODKkDW9w3nWBDImnkbjFef2E79z0Z6E32kcNLXutPwRwF1VRTsPA2LUXkMIz4gg9y6CuOt1Ipo4Hx%2FdD6YCFU1sKj9HdQepZQaKnksF%2BgBFBH3RspaKYsTg4cw2t8yFjLomOKR6JeD31kNty%2Fnt%2BJ76%2B%2B%2FUSjtTXGxhWZryUVk9P3tdqHkIHsvq%2FUlUBDcsLg%2FrcRP4dU5yUqcIqJCtPW2XfVsMgs0LRbgNFHTvzJs0GMdPBn0Q%3D%3D", provider: "guangdong", param: "ydpd" },
    { number: 228, name: "广东台经典剧", url: "https://tcdn.itouchtv.cn/live/lizhi.m3u8?t_token=fb44f5d077347923a6a79577633b071c-yooc30YZ%2BzQ0hDHERkYiY%2BWuuUptN7T1PJZ%2BSRlo9UITcsVUD8lShIRrhEsdLVMDu%2Bg6OmZjCgSybR3ppzvNrdpqh7UVK9vGKOtzi%2F4SEPQ4VmpS6W9J1UMEIavExrmFO4oB%2Fgrb4YEdXH3YaXhCiWT1XwN22QTD6y%2F1DhICL9yYhftCVVw2dEBUDo6PqeyLWpz%2BuhcrhnPOlBk1ZqBY2Em6bdxt5PX2fpxFyJ21hnPfIDJ7TnLwlrQAeSmnabnd2qC1GrtXFsFbrXRP368PlxxwdZn7p%2BzXRNomUKpPQd1v%2FxJWT1BzBYFNnxW8bxsuKBeicgcMRp2sRngGBofKQmUQiaLTKpIPEBK3Fb1XQWR1%2FFHK6uoC0fCdu2dXjxYdzZtNP2VXzJOPtlsgo%2FQBRA%3D%3D", provider: "guangdong", param: "lizhi" },
    { number: 229, name: "健康", url: "https://tcdn.itouchtv.cn/live/health.m3u8?t_token=f6ddd06c3199c49905f6b498c3d1c3fe-Jz7ovUml8llZ%2FgGhFmmDNEEaznEzbuFisqaO2wDKo5ntOXB2K45g7TZtFUB65UIUGXYsaB7loyfwl8%2FrdE7tJNIi75nrth4fHeogUmrMPlUZOs202X5maxSrqB42GYIbCB%2FSW7LiG%2Bqa8yVVLN1O3Q0%2BaYfK2l1ugLmucPHdRHZks9rlVsunXwzkYYyzzM4vWTjVIR65pwdkB8%2BP3KjFl6868swWNr4cOzlrN7K%2BfgWyEByDUxMahJi9dDjvFffzO38NwF6z20734rJbmmoYMsyfEQcbyZMsoTsBxf3nSsNd9KFyxSVrC3ihFv0bcn%2BTk1zbw8fEcBzHSJj5ISQTKXNtlc398bmLpuKKumTmPM%2FAoghnKhqFuHUB2eBbn0hZK5BWwnSbKaQHOjAfqgAftw%3D%3D", provider: "guangdong", param: "health" },
    { number: 230, name: "GRTN生活", url: "https://tcdn.itouchtv.cn/live/life.m3u8?t_token=ff9eef1dad69d35b174c9b1a08483f1c-VPAHiftoWOLQ9yp4f%2Femnsqeyz8wYDHUu3z%2BWk5IjdQMJs9RWXtFFaKdxm21Z7FzCbKSPgYrQ6ha8Y%2FmBWPov%2FZqteZ0d4XS%2FoFESr9M5B3r00cBSKKzQRekfsLCw6om%2FTEE%2F0au4lUgRBSxIZO6En81%2BIM%2FiQJ0u%2B9h6EZn4kEs5F%2B%2F1EJ1bX%2F40RpjT34GaNh67%2FtJ0mAgDtS0MgS7hkTrrZx6l2IWr7pmlqltrEWK%2BQHVM%2B%2Bdr2OuotK7vupbTvg2uEbdVbGASHfbbD%2Fvognw0rV%2FAsnITH48QdVgUXqqBxAEKOd8TXPdA%2BPfOSHmDSHMmUP6BkbrDWz8Lhnp8yKEJKMI%2FLd9a097xAmnXPOK3tzf1HezlNUfQITiIl9bSAENK3v7LaiUonny7a8f6Q%3D%3D", provider: "guangdong", param: "life" }
  ]
});

/* ---- 2) 取流解析器：带时效签名的台靠它现算新鲜地址 ----
 * 每个解析器注册成 window.__RESOLVERS.<provider>(param) -> Promise<m3u8>
 * 不想用解析器就整段删掉，播放时会退回上面的 url。
 */
/* ============================================================
 * 广东 荔枝网(gdtv.cn / itouchtv.cn) 直播解析器
 *   window.__RESOLVERS.guangdong(param)  ->  当次可播 m3u8
 * 站点: https://www.gdtv.cn/tvChannelDetail/<pk>
 * ------------------------------------------------------------
 * 真实链路（全程抓包实测）:
 *   (0) 所有 gdtv-api / tcdn-api 请求必须带 5 个签名头，由 gdtv.cn 的
 *       WASM 签名器(vendor_w_*.js，模块 265)生成:
 *         sign(method, 完整URL, deviceId, "WEB_PC", body, undefined)
 *           -> Map{
 *                "Content-Type":"application/json",
 *                "X-ITOUCHTV-Ca-Timestamp": <ms>,
 *                "X-ITOUCHTV-Ca-Key": "89541943007407288657755311868534",
 *                "X-ITOUCHTV-Ca-Signature": "<base64>",
 *                "X-ITOUCHTV-CLIENT": "WEB_PC",
 *                "X-ITOUCHTV-DEVICE-ID": "WEB_<uuid>"
 *              }
 *       deviceId 可自造 "WEB_<uuid4>"。
 *   (1) GET https://tcdn-api.itouchtv.cn/getParam            (带签名头)
 *         -> { "node": "<hash>-<enc>-1" }
 *       取 node 去掉结尾 "-1" 后 base64(btoa) 作为下一步的 node。
 *   (2) GET https://gdtv-api.gdtv.cn/api/tv/v2/tvChannel/<pk>
 *             ?tvChannelPk=<pk>&node=<b64node>               (带签名头)
 *         -> { pk, name, ..., "playUrl": "{\"hd\":\"https://tcdn.itouchtv.cn/live/<code>.m3u8?t_token=..\"}" }
 *       playUrl 是 JSON 字符串，取 .hd/.sd 即为可播 m3u8。
 *       (t_token 为会话级签名, 失效后重新走本流程即可)
 * ------------------------------------------------------------
 * 纯浏览器 JS: 无 require。WASM 签名器运行时从 CDN 拉取本地执行。
 * param: 下表 pk 数字 / 短码(code) / 中文名 三者任一。
 * ============================================================ */
(function (G) {
  'use strict';
  G.__RESOLVERS = G.__RESOLVERS || {};

  // 频道表: code / 中文名 / pk
  var CHANNELS = [
    { code: 'gdws', name: '广东卫视', pk: 43 },
    { code: 'gdzj', name: '广东珠江', pk: 44 },
    { code: 'xwpd', name: '广东新闻', pk: 45 },
    { code: 'gdgg', name: '广东民生', pk: 48 },
    { code: 'gdty', name: '广东体育', pk: 47 },
    { code: 'nfws', name: '大湾区卫视', pk: 51 },
    { code: 'gdgj', name: '大湾区卫视海外版', pk: 46 },
    { code: 'gdys', name: '广东影视', pk: 53 },
    { code: 'gdzy', name: '4K超高清', pk: 16 },
    { code: 'gdse', name: '广东少儿', pk: 54 },
    { code: 'jjkt', name: '嘉佳卡通', pk: 66 },
    { code: 'nfgw', name: '南方购物', pk: 42 },
    { code: 'lnxq', name: '岭南戏曲', pk: 15 },
    { code: 'ydpd', name: '广东移动', pk: 74 },
    { code: 'lizhi', name: '广东台经典剧', pk: 100 },
    { code: 'health', name: '健康', pk: 99 },
    { code: 'life', name: 'GRTN生活', pk: 102 }
  ];
  var ALIAS = {
    '珠江': 'gdzj', '广东新闻频道': 'xwpd', '新闻': 'xwpd', '民生': 'gdgg', '广东公共': 'gdgg',
    '体育': 'gdty', '大湾区': 'nfws', '海外版': 'gdgj', '大湾区海外版': 'gdgj',
    '4K': 'gdzy', '4k超高清': 'gdzy', '超高清': 'gdzy', '影视': 'gdys',
    '少儿': 'gdse', '嘉佳': 'jjkt', '南方购物频道': 'nfgw', '岭南': 'lnxq',
    '移动': 'ydpd', '经典剧': 'lizhi', 'GRTN': 'life'
  };

  function pick(param) {
    if (param == null) return null;
    var p = String(param).trim();
    for (var i = 0; i < CHANNELS.length; i++) if (CHANNELS[i].code === p || CHANNELS[i].name === p) return CHANNELS[i];
    if (ALIAS[p]) { for (var k = 0; k < CHANNELS.length; k++) if (CHANNELS[k].code === ALIAS[p]) return CHANNELS[k]; }
    if (/^\d+$/.test(p)) return { code: p, name: p, pk: parseInt(p, 10) };
    for (var j = 0; j < CHANNELS.length; j++) if (p.indexOf(CHANNELS[j].name) >= 0 || CHANNELS[j].name.indexOf(p) >= 0) return CHANNELS[j];
    return null;
  }

  function uuid() {
    if (G.crypto && G.crypto.randomUUID) return G.crypto.randomUUID();
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
      var r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
    });
  }

  function readCookie(name) {
    try {
      var m = ('; ' + (G.document ? G.document.cookie : '') + '; ').match('; ' + name + '=([^;]*);');
      return m ? decodeURIComponent(m[1]) : null;
    } catch (e) { return null; }
  }

  // deviceId: 优先复用站点已下发的 DEVICEID cookie(与网页播放器完全一致),
  // 否则自造 "WEB_<uuid4>"。两次请求(getParam/tvChannel)必须用同一个 deviceId。
  function deviceId() {
    return readCookie('DEVICEID') || readCookie('deviceid') || ('WEB_' + uuid());
  }

  // ---------- 取签名器模块 265 的工厂函数 ----------
  var VENDOR_FALLBACK = 'https://img.gdtv.cn/sitecdn/platforms/gdtv/js/vendor_w_00aa955c.js';

  function findVendorUrl() {
    // 尝试从详情页拿到带哈希的真实文件名; 失败则用兜底地址
    return fetch('https://www.gdtv.cn/tvChannelDetail/43', { cache: 'no-store' })
      .then(function (r) { return r.text(); })
      .then(function (html) {
        var m = html.match(/client_([0-9a-f]+)\.js/) || html.match(/manifest_([0-9a-f]+)\.js/) || html.match(/_([0-9a-f]{8})\.js/);
        return m ? 'https://img.gdtv.cn/sitecdn/platforms/gdtv/js/vendor_w_' + m[1] + '.js' : VENDOR_FALLBACK;
      })
      .catch(function () { return VENDOR_FALLBACK; });
  }

  function loadFactoryScript(url) {
    return new Promise(function (res, rej) {
      var prev = G.webpackJsonp;
      var timer = setTimeout(function () { done(); rej(new Error('guangdong: 加载签名器超时')); }, 15000);
      function done() { clearTimeout(timer); try { if (G.webpackJsonp === hooked) G.webpackJsonp = prev; } catch (e) {} }
      var hooked = {
        push: function (arr) {
          var f = null;
          try { if (arr && arr[1] && arr[1][265]) f = arr[1][265]; } catch (e) {}
          if (f) { done(); res(f); return; }
          if (prev && typeof prev.push === 'function') prev.push(arr);
        }
      };
      G.webpackJsonp = hooked;
      var s = document.createElement('script');
      s.charset = 'utf-8';
      s.src = url;
      s.onerror = function () { done(); rej(new Error('guangdong: 签名器脚本加载失败 ' + url)); };
      (document.head || document.documentElement).appendChild(s);
    });
  }

  // 签名器 wasm 内部会校验当前站点，非 www.gdtv.cn 域名直接 panic(RuntimeError: unreachable)。
  // 定位(实测 2026-10): wasm 并不只读 location 导入，而是用一段 **动态构造的混淆 JS 函数**
  //   新Function("_$", "<obfuscated>")  作为通用属性读取器，
  //   实际执行 document["location"]["href"] / location["host"|"origin"|"href"]，
  //   拿到 file:// 的 href 后解析失败 -> panic。
  // 解决: 在加载 vendor_w 源码时做定点替换, 把一个“https://www.gdtv.cn”的假
  //   document / location 注入到 wasm 的导入实现里。
  var FAKELOC_SRC = "{href:'https://www.gdtv.cn/tvChannelDetail/43',host:'www.gdtv.cn',hostname:'www.gdtv.cn',origin:'https://www.gdtv.cn',protocol:'https:',pathname:'/tvChannelDetail/43',search:'',hash:'',port:''}";
  var PRELUDE = 'var __FAKELOC=' + FAKELOC_SRC +
    ';var __FAKEDOC={location:__FAKELOC,href:__FAKELOC.href,cookie:"",title:"",documentElement:{},createElement:function(){return {};},getElementsByTagName:function(){return [];}};';
  var T_MARK = 'function t(){var g={wbg:{}};';
  var LOC_MARK = 'return Y(i(A).location)';                       // __wbg_location
  var DOC_MARK = 'var g=i(A).document;return U(g)?0:Y(g)';        // __wbg_document

  function patchSource(src) {
    if (src.indexOf(T_MARK) < 0) return src;                       // 结构变了, 原样返回
    var out = src.replace(T_MARK, 'function t(){' + PRELUDE + 'var g={wbg:{}};');
    var hit = 0;
    if (out.indexOf(DOC_MARK) >= 0) { out = out.split(DOC_MARK).join('return Y(__FAKEDOC)'); hit++; }
    if (out.indexOf(LOC_MARK) >= 0) { out = out.split(LOC_MARK).join('return Y(__FAKELOC)'); hit++; }
    return hit ? out : src;
  }

  function extractFactory(src) {
    var i = src.indexOf('265:function(');
    if (i < 0) throw new Error('guangdong: vendor_w 结构变化');
    var fnStart = i + '265:'.length;
    var depth = 0, p = fnStart, inStr = null, esc = false, started = false;
    for (; p < src.length; p++) {
      var c = src.charAt(p);
      if (inStr) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === inStr) inStr = null; continue; }
      if (c === '"' || c === "'" || c === '`') { inStr = c; continue; }
      if (c === '{') { depth++; started = true; } else if (c === '}') { depth--; if (started && depth === 0) { p++; break; } }
    }
    return (0, eval)('(' + src.slice(fnStart, p) + ')');
  }

  var signerP = null;
  function getSigner() {
    if (signerP) return signerP;
    signerP = findVendorUrl().then(function (url) {
      // 首选: fetch 源码 -> 定点替换 location -> eval (浏览器/WebView 无跨域限制时可用)
      return fetch(url, { cache: 'no-store' }).then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.text();
      }).then(function (src) {
        return extractFactory(patchSource(src));
      }).catch(function () {
        // 兜底: <script> 方式加载(仅当页面本身在 gdtv 域名下, 或无需替换时可用)
        return loadFactoryScript(url);
      });
    }).then(function (factory) {
      var mod = { exports: {} };
      factory(mod, mod.exports, function (n) { return n === 42 ? G : (n === 146 ? mod : {}); });
      return mod.exports.default().then(function () { return mod.exports.a; });
    });
    return signerP;
  }

  // 生成一组签名头
  function signHeaders(method, url, deviceId, body) {
    return getSigner().then(function (sign) {
      var m = sign(method, url, deviceId, 'WEB_PC', body || '', undefined);
      var o = {};
      if (m && typeof m.forEach === 'function' && typeof m.get === 'function') m.forEach(function (v, k) { o[k] = v; });
      else if (m) { for (var k in m) o[k] = m[k]; }
      return o;
    });
  }

  // ---------------- 解析 ----------------
  function resolve(param) {
    var ch = pick(param);
    if (!ch || !ch.pk) return Promise.reject(new Error('guangdong: 未知频道参数 ' + param));
    var did = deviceId();
    var u1 = 'https://tcdn-api.itouchtv.cn/getParam';
    var nodeB64;
    return signHeaders('GET', u1, did, '')
      .then(function (h1) { return fetch(u1, { headers: h1, cache: 'no-store' }); })
      .then(function (r) {
        if (!r.ok) throw new Error('guangdong: getParam HTTP ' + r.status);
        return r.json();
      })
      .then(function (j1) {
        if (!j1 || !j1.node) throw new Error('guangdong: getParam 无 node');
        var node = String(j1.node).replace(/-1$/, '');
        nodeB64 = btoa(unescape(encodeURIComponent(node)));
        var u2 = 'https://gdtv-api.gdtv.cn/api/tv/v2/tvChannel/' + ch.pk + '?tvChannelPk=' + ch.pk + '&node=' + encodeURIComponent(nodeB64);
        return signHeaders('GET', u2, did, '').then(function (h2) {
          return fetch(u2, { headers: h2, cache: 'no-store' });
        });
      })
      .then(function (r) {
        if (!r.ok) throw new Error('guangdong: tvChannel HTTP ' + r.status);
        return r.json();
      })
      .then(function (j2) {
        var pu = j2 && j2.playUrl;
        try { pu = JSON.parse(pu); } catch (e) {}
        var url = pu && (pu.hd || pu.uhd || pu.sd || pu.ld || pu.hls);
        if (!url) throw new Error('guangdong: 无 playUrl pk=' + ch.pk + (j2 && j2.errorMessage ? ' (' + j2.errorMessage + ')' : ''));
        return url;
      });
  }

  resolve.resolve = resolve;
  resolve.displayName = '广东(荔枝网)';
  resolve.site = 'https://www.gdtv.cn/tvChannelDetail/43';
  resolve.channels = CHANNELS;
  resolve.pick = pick;
  resolve.signHeaders = signHeaders;
  resolve._internals = { findVendorUrl: findVendorUrl, patchSource: patchSource, extractFactory: extractFactory, getSigner: getSigner, LOC_MARK: LOC_MARK, DOC_MARK: DOC_MARK, T_MARK: T_MARK, VENDOR_FALLBACK: VENDOR_FALLBACK };

  G.__RESOLVERS.guangdong = resolve;
})(typeof window !== 'undefined' ? window : (typeof globalThis !== 'undefined' ? globalThis : this));
