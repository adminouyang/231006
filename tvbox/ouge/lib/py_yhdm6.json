#coding=utf-8
#!/usr/bin/python
import sys
sys.path.append('..') 
from base.spider import Spider
import json
import time
import base64
import re
from urllib import request, parse
import urllib
import urllib.request
import time


class Spider(Spider):  # 元类 默认的元类 type
	def getName(self):
		return "樱花动漫6"#6才是本体
	def init(self,extend=""):
		print("============{0}============".format(extend))
		pass
	def isVideoFormat(self,url):
		pass
	def manualVideoCheck(self):
		pass
	def homeContent(self,filter):
		result = {}
		cateManual = {
			"日本动漫":"1",
			"国产动漫":"4",
			"动漫电影":"2",
			"欧美动漫":"3"
		}
		classes = []
		for k in cateManual:
			classes.append({
				'type_name':k,
				'type_id':cateManual[k]
			})
		result['class'] = classes
		if(filter):
			result['filters'] = self.config['filter']
		return result
	def homeVideoContent(self):
		htmlTxt=self.custom_webReadFile(urlStr='https://yhdm6.top/')
		videos = self.custom_list(html=htmlTxt,patternTxt=r'<a class="vodlist_thumb lazyload" href="(?P<url>.+?)" title="(?P<title>.+?)" data-original="(?P<img>.+?)".+?><span class=".*?<span class="pic_text text_right">(?P<renew>.+?)</span></a>')
		result = {
			'list':videos
		}
		return result
	def categoryContent(self,tid,pg,filter,extend):
		result = {}
		videos=[]
		types=""
		if 'types' in extend.keys():
			if extend['types'].find('全部')<0:
				types='class/{0}/'.format(urllib.parse.quote(extend['types']))
		letter=''
		if 'letter' in extend.keys():
			if extend['letter'].find('全部')<0:
				letter='letter/{0}/'.format(extend['letter'])
		year=''
		if 'year' in extend.keys():
			if extend['year'].find('全部')<0:
				year='/year/{0}'.format(extend['year'])
		by=''
		if 'by' in extend.keys():
			by='by/{0}/'.format(extend['by'])
		Url='https://yhdm6.top/index.php/vod/show/{2}{3}id/{0}/{5}{1}{4}.html'.format(tid,'page/'+pg,by,types,year,letter)
		# print(url)
		#https://yhdm6.top/index.php/vod/show/by/score/class/%E7%A7%91%E5%B9%BB/id/3/letter/W/year/2022.html
		htmlTxt=self.custom_webReadFile(urlStr=Url)
		videos = self.custom_list(html=htmlTxt,patternTxt=r'<a class="vodlist_thumb lazyload" href="(?P<url>.+?)" title="(?P<title>.+?)" data-original="(?P<img>.+?)"><span class="play hidden_xs"></span><span class="pic_text text_right">(?P<renew>.+?)</span></a>')
		result['list'] = videos
		result['page'] = pg
		result['pagecount'] = pg if len(videos)<60 else int(pg)+1
		result['limit'] = 90
		result['total'] = 999999
		return result
	def detailContent(self,array):
		aid = array[0].split('###')
		idUrl=aid[1]
		title=aid[0]
		pic=aid[2]
		url=idUrl
		htmlTxt =  self.custom_webReadFile(urlStr=url,codeName='utf-8')

		
		line=self.custom_RegexGetTextLine(Text=htmlTxt,RegexText=r'<a href="javascript:void\(0\);" alt="(.+?)">',Index=1)
		if len(line)<1:
			return  {'list': []}
		playFrom = []
		videoList=[]
		vodItems = []
		circuit=self.custom_lineList(Txt=htmlTxt,mark=r'<ul class="content_playlist',after='</ul>')
		playFrom=line
		for v in circuit:
			vodItems = self.custom_EpisodesList(html=v,RegexText=r'<li><a href="(?P<url>.+?)">(?P<title>.+?)</a></li>')
			joinStr = "#".join(vodItems)
			videoList.append(joinStr)

		vod_play_from='$$$'.join(playFrom)
		vod_play_url = "$$$".join(videoList)

		typeName=self.custom_RegexGetText(Text=htmlTxt,RegexText=r'<a href="/index.php/vod/search/class/.+?" target="_blank">(.+?)</a>',Index=1)
		year=self.custom_RegexGetText(Text=htmlTxt,RegexText=r'<a href="/index.php/vod/search/year/\d{4}.html" target="_blank">(\d{4})</a>',Index=1)
		area=typeName
		act=self.custom_RegexGetText(Text=htmlTxt,RegexText=r'<a href="/index.php/vod/search/actor/.+?.html" target="_blank">(.+?)</a>',Index=1)
		temporary=self.custom_RegexGetTextLine(Text=htmlTxt,RegexText=r'<a href="/index.php/vod/search/director/.+?.html" target="_blank">(.+?)</a>',Index=1)
		dir='/'.join(temporary)
		cont=self.custom_RegexGetText(Text=htmlTxt,RegexText=r'剧情介绍</h2>(.+?)</span>',Index=1)
		vod = {
			"vod_id": array[0],
			"vod_name": title,
			"vod_pic": pic,
			"type_name":self.custom_removeHtml(txt=typeName),
			"vod_year": self.custom_removeHtml(txt=year),
			"vod_area": area,
			"vod_remarks": '',
			"vod_actor":  self.custom_removeHtml(txt=act),
			"vod_director": self.custom_removeHtml(txt=dir),
			"vod_content": self.custom_removeHtml(txt=cont)
		}
		vod['vod_play_from'] = vod_play_from
		vod['vod_play_url'] = vod_play_url

		result = {
			'list': [
				vod
			]
		}
		return result
	def searchContent(self,key,quick):
		url='https://yhdm6.top/index.php/vod/search.html?wd={0}&submit='.format(urllib.parse.quote(key))
		htmlTxt=self.custom_webReadFile(urlStr=url)
		videos = self.custom_list(html=htmlTxt,patternTxt=r'<a class="vodlist_thumb lazyload" href="(?P<url>.+?)" title="(?P<title>.+?)" data-original="(?P<img>.+?)".+?><span class=".*?<span class="pic_text text_right">(?P<renew>.+?)</span></a>')
		result = {
			'list':videos
		}
		return result
	def playerContent(self,flag,id,vipFlags):
		result = {}
		Url=id
		htmlTxt =self.custom_webReadFile(urlStr=Url,codeName='utf-8')
		parse=0
		UrlStr=''
		temporary=self.custom_lineList(Txt=htmlTxt,mark=r'var player_aaaa=',after=r'}</script>')
		if len(temporary)==1:
			jo=json.loads(temporary[0][16:]+"}")
			UrlStr=urllib.parse.unquote(jo['url'])
		if UrlStr.find('.m3u8')<2:
			Url=id
			parse=1
		else:
			Url=UrlStr
		result["parse"] = parse#0=直接播放、1=嗅探
		result["playUrl"] =''
		result["url"] = Url
		# result['jx'] = jx#VIP解析,0=不解析、1=解析
		result["header"] = ''	
		return result


	config = {
		"player": {},
		"filter": {
		"1":[
		{"key":"types","name":"类型:","value":[{"n":"全部","v":"全部"},{"n":"喜剧","v":"喜剧"},{"n":"爱情","v":"爱情"},{"n":"恐怖","v":"恐怖"},{"n":"动作","v":"动作"},{"n":"科幻","v":"科幻"},{"n":"剧情","v":"剧情"},{"n":"战争","v":"战争"},{"n":"犯罪","v":"犯罪"},{"n":"奇幻","v":"奇幻"},{"n":"冒险","v":"冒险"},{"n":"悬疑","v":"悬疑"},{"n":"惊悚","v":"惊悚"},{"n":"古装","v":"古装"},{"n":"历史","v":"历史"},{"n":"运动","v":"运动"},{"n":"儿童","v":"儿童"}]},
		{"key":"year","name":"年份:","value":[{"n":"全部","v":"全部"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"},{"n":"2009","v":"2009"},{"n":"2008","v":"2008"},{"n":"2007","v":"2007"},{"n":"2006","v":"2006"},{"n":"2005","v":"2005"},{"n":"2004","v":"2004"},{"n":"2003","v":"2003"},{"n":"2002","v":"2002"},{"n":"2001","v":"2001"},{"n":"2000","v":"2000"}]},
		{"key":"letter","name":"字母:","value":[{"n":"全部","v":"全部"},{"n":"A","v":"A"},{"n":"B","v":"B"},{"n":"C","v":"C"},{"n":"D","v":"D"},{"n":"E","v":"E"},{"n":"F","v":"F"},{"n":"G","v":"G"},{"n":"H","v":"H"},{"n":"I","v":"I"},{"n":"J","v":"J"},{"n":"K","v":"K"},{"n":"L","v":"L"},{"n":"M","v":"M"},{"n":"N","v":"N"},{"n":"O","v":"O"},{"n":"P","v":"P"},{"n":"Q","v":"Q"},{"n":"R","v":"R"},{"n":"S","v":"S"},{"n":"T","v":"T"},{"n":"U","v":"U"},{"n":"V","v":"V"},{"n":"W","v":"W"},{"n":"X","v":"X"},{"n":"Y","v":"Y"},{"n":"Z","v":"Z"},{"n":"0-9","v":"0-9"}]},
		{"key":"by","name":"排序:","value":[{"n":"按最新","v":"time"},{"n":"按最热","v":"按最热"},{"n":"按评分","v":"按评分"}]}
		],
		"4":[
		{"key":"types","name":"类型:","value":[{"n":"全部","v":"全部"},{"n":"喜剧","v":"喜剧"},{"n":"爱情","v":"爱情"},{"n":"恐怖","v":"恐怖"},{"n":"动作","v":"动作"},{"n":"科幻","v":"科幻"},{"n":"剧情","v":"剧情"},{"n":"战争","v":"战争"},{"n":"犯罪","v":"犯罪"},{"n":"奇幻","v":"奇幻"},{"n":"冒险","v":"冒险"},{"n":"悬疑","v":"悬疑"},{"n":"惊悚","v":"惊悚"},{"n":"古装","v":"古装"},{"n":"历史","v":"历史"},{"n":"运动","v":"运动"},{"n":"儿童","v":"儿童"}]},
		{"key":"year","name":"年份:","value":[{"n":"全部","v":"全部"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"},{"n":"2009","v":"2009"},{"n":"2008","v":"2008"},{"n":"2007","v":"2007"},{"n":"2006","v":"2006"},{"n":"2005","v":"2005"},{"n":"2004","v":"2004"},{"n":"2003","v":"2003"},{"n":"2002","v":"2002"},{"n":"2001","v":"2001"},{"n":"2000","v":"2000"}]},
		{"key":"letter","name":"字母:","value":[{"n":"全部","v":"全部"},{"n":"A","v":"A"},{"n":"B","v":"B"},{"n":"C","v":"C"},{"n":"D","v":"D"},{"n":"E","v":"E"},{"n":"F","v":"F"},{"n":"G","v":"G"},{"n":"H","v":"H"},{"n":"I","v":"I"},{"n":"J","v":"J"},{"n":"K","v":"K"},{"n":"L","v":"L"},{"n":"M","v":"M"},{"n":"N","v":"N"},{"n":"O","v":"O"},{"n":"P","v":"P"},{"n":"Q","v":"Q"},{"n":"R","v":"R"},{"n":"S","v":"S"},{"n":"T","v":"T"},{"n":"U","v":"U"},{"n":"V","v":"V"},{"n":"W","v":"W"},{"n":"X","v":"X"},{"n":"Y","v":"Y"},{"n":"Z","v":"Z"},{"n":"0-9","v":"0-9"}]},
		{"key":"by","name":"排序:","value":[{"n":"按最新","v":"time"},{"n":"按最热","v":"hits"},{"n":"按评分","v":"score"}]}
		],
		"2":[
		{"key":"types","name":"类型:","value":[{"n":"全部","v":"全部"},{"n":"喜剧","v":"喜剧"},{"n":"爱情","v":"爱情"},{"n":"恐怖","v":"恐怖"},{"n":"动作","v":"动作"},{"n":"科幻","v":"科幻"},{"n":"剧情","v":"剧情"},{"n":"战争","v":"战争"},{"n":"犯罪","v":"犯罪"},{"n":"奇幻","v":"奇幻"},{"n":"冒险","v":"冒险"},{"n":"悬疑","v":"悬疑"},{"n":"惊悚","v":"惊悚"},{"n":"古装","v":"古装"},{"n":"历史","v":"历史"},{"n":"运动","v":"运动"},{"n":"儿童","v":"儿童"}]},
		{"key":"year","name":"年份:","value":[{"n":"全部","v":"全部"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"},{"n":"2009","v":"2009"},{"n":"2008","v":"2008"},{"n":"2007","v":"2007"},{"n":"2006","v":"2006"},{"n":"2005","v":"2005"},{"n":"2004","v":"2004"},{"n":"2003","v":"2003"},{"n":"2002","v":"2002"},{"n":"2001","v":"2001"},{"n":"2000","v":"2000"}]},
		{"key":"letter","name":"字母:","value":[{"n":"全部","v":"全部"},{"n":"A","v":"A"},{"n":"B","v":"B"},{"n":"C","v":"C"},{"n":"D","v":"D"},{"n":"E","v":"E"},{"n":"F","v":"F"},{"n":"G","v":"G"},{"n":"H","v":"H"},{"n":"I","v":"I"},{"n":"J","v":"J"},{"n":"K","v":"K"},{"n":"L","v":"L"},{"n":"M","v":"M"},{"n":"N","v":"N"},{"n":"O","v":"O"},{"n":"P","v":"P"},{"n":"Q","v":"Q"},{"n":"R","v":"R"},{"n":"S","v":"S"},{"n":"T","v":"T"},{"n":"U","v":"U"},{"n":"V","v":"V"},{"n":"W","v":"W"},{"n":"X","v":"X"},{"n":"Y","v":"Y"},{"n":"Z","v":"Z"},{"n":"0-9","v":"0-9"}]},
		{"key":"by","name":"排序:","value":[{"n":"按最新","v":"time"},{"n":"按最热","v":"hits"},{"n":"按评分","v":"score"}]}
		],
		"3":[
		{"key":"types","name":"类型:","value":[{"n":"全部","v":"全部"},{"n":"喜剧","v":"喜剧"},{"n":"爱情","v":"爱情"},{"n":"恐怖","v":"恐怖"},{"n":"动作","v":"动作"},{"n":"科幻","v":"科幻"},{"n":"剧情","v":"剧情"},{"n":"战争","v":"战争"},{"n":"犯罪","v":"犯罪"},{"n":"奇幻","v":"奇幻"},{"n":"冒险","v":"冒险"},{"n":"悬疑","v":"悬疑"},{"n":"惊悚","v":"惊悚"},{"n":"古装","v":"古装"},{"n":"历史","v":"历史"},{"n":"运动","v":"运动"},{"n":"儿童","v":"儿童"}]},
		{"key":"year","name":"年份:","value":[{"n":"全部","v":"全部"},{"n":"2023","v":"2023"},{"n":"2022","v":"2022"},{"n":"2021","v":"2021"},{"n":"2020","v":"2020"},{"n":"2019","v":"2019"},{"n":"2018","v":"2018"},{"n":"2017","v":"2017"},{"n":"2016","v":"2016"},{"n":"2015","v":"2015"},{"n":"2014","v":"2014"},{"n":"2013","v":"2013"},{"n":"2012","v":"2012"},{"n":"2011","v":"2011"},{"n":"2010","v":"2010"},{"n":"2009","v":"2009"},{"n":"2008","v":"2008"},{"n":"2007","v":"2007"},{"n":"2006","v":"2006"},{"n":"2005","v":"2005"},{"n":"2004","v":"2004"},{"n":"2003","v":"2003"},{"n":"2002","v":"2002"},{"n":"2001","v":"2001"},{"n":"2000","v":"2000"}]},
		{"key":"letter","name":"字母:","value":[{"n":"全部","v":"全部"},{"n":"A","v":"A"},{"n":"B","v":"B"},{"n":"C","v":"C"},{"n":"D","v":"D"},{"n":"E","v":"E"},{"n":"F","v":"F"},{"n":"G","v":"G"},{"n":"H","v":"H"},{"n":"I","v":"I"},{"n":"J","v":"J"},{"n":"K","v":"K"},{"n":"L","v":"L"},{"n":"M","v":"M"},{"n":"N","v":"N"},{"n":"O","v":"O"},{"n":"P","v":"P"},{"n":"Q","v":"Q"},{"n":"R","v":"R"},{"n":"S","v":"S"},{"n":"T","v":"T"},{"n":"U","v":"U"},{"n":"V","v":"V"},{"n":"W","v":"W"},{"n":"X","v":"X"},{"n":"Y","v":"Y"},{"n":"Z","v":"Z"},{"n":"0-9","v":"0-9"}]},
		{"key":"by","name":"排序:","value":[{"n":"按最新","v":"time"},{"n":"按最热","v":"hits"},{"n":"按评分","v":"score"}]}
		]
		}
		}
	header = {
		'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36'
	}
	def localProxy(self,param):
		return [200, "video/MP2T", action, ""]
	#-----------------------------------------------自定义函数-----------------------------------------------
		#正则取文本
	def custom_RegexGetText(self,Text,RegexText,Index):
		returnTxt=""
		Regex=re.search(RegexText, Text, re.M|re.S)
		if Regex is None:
			returnTxt=""
		else:
			returnTxt=Regex.group(Index)
		return returnTxt	
	#分类取结果
	def custom_list(self,html,patternTxt):
		ListRe=re.finditer(patternTxt, html, re.M|re.S)
		videos = []
		head="https://yhdm6.top"
		for vod in ListRe:
			url = vod.group('url')
			title =self.custom_removeHtml(txt=vod.group('title'))
			img =vod.group('img')
			renew=vod.group('renew')
			if len(url) == 0:
				continue
			# print(renew)
			videos.append({
				"vod_id":"{0}###{1}###{2}".format(title,head+url,img),
				"vod_name":title,
				"vod_pic":img,
				"vod_remarks":renew
			})
		return videos
	#删除html标签
	def custom_removeHtml(self,txt):
		soup = re.compile(r'<[^>]+>',re.S)
		txt =soup.sub('', txt)
		return txt.replace("&nbsp;"," ")
		#访问网页
	def custom_webReadFile(self,urlStr,header=None,codeName='utf-8'):
		html=''
		if header==None:
			header={
				"Referer":urlStr,
				'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36',
				"Host":self.custom_RegexGetText(Text=urlStr,RegexText='https*://(.*?)(/|$)',Index=1)
			}
		# import ssl
		# ssl._create_default_https_context = ssl._create_unverified_context#全局取消证书验证
		req=urllib.request.Request(url=urlStr,headers=header)#,headers=header
		with  urllib.request.urlopen(req)  as response:
			html = response.read().decode(codeName)
		return html
	#判断是否要调用vip解析
	def ifJx(self,urlTxt):
		Isjiexi=0
		RegexTxt=r'(youku.com|v.qq|bilibili|iqiyi.com)'
		if self.get_RegexGetText(Text=urlTxt,RegexText=RegexTxt,Index=1)!='':
			Isjiexi=1
		return Isjiexi
	#取集数
	def custom_EpisodesList(self,html,RegexText):
		ListRe=re.finditer(RegexText, html, re.M|re.S)
		videos = []
		head="https://yhdm6.top"
		for vod in ListRe:
			url = vod.group('url')
			title =vod.group('title')
			if len(url) == 0:
				continue
			videos.append(title+"$"+head+url)
		return videos
	#取剧集区
	def custom_lineList(self,Txt,mark,after):
		circuit=[]
		origin=Txt.find(mark)
		while origin>8:
			end=Txt.find(after,origin)
			circuit.append(Txt[origin:end])
			origin=Txt.find(mark,end)
		return circuit	
	#正则取文本,返回数组	
	def custom_RegexGetTextLine(self,Text,RegexText,Index):
		returnTxt=[]
		pattern = re.compile(RegexText, re.M|re.S)
		ListRe=pattern.findall(Text)
		if len(ListRe)<1:
			return returnTxt
		for value in ListRe:
			returnTxt.append(value)	
		return returnTxt
# T=Spider()
# l=T.searchContent(key='柯南',quick='')
# l=T.homeVideoContent()
# extend={'types':'科幻',"by":"score"}
# l=T.categoryContent(tid='1',pg='1',filter=False,extend={})
# for x in l['list']:
# 	print(x['vod_name'])
# mubiao= '机动警察###https://yhdm6.top/index.php/vod/detail/id/18293.html###https://pic.lzzypic.com/upload/vod/20230825-1/c4b3a6eb89c83879b81e5aa996d5e212.jpg'
# playTabulation=T.detailContent(array=[mubiao,])
# print(playTabulation)
# m3u8=T.playerContent(flag='',id='https://yhdm6.top/index.php/vod/play/id/18293/sid/1/nid/6.html',vipFlags=True)
# print(m3u8)
# print(T.config['filter'])