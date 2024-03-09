#coding=utf-8
#!/usr/bin/python
import sys
sys.path.append('..')
from base.spider import Spider
import re
from urllib import request, parse
import urllib
import urllib.request
import json
class Spider(Spider):  # 元类 默认的元类 type
	def getName(self):
		return "卡通站(kt30)"
	def init(self,extend=""):
		pass
	def isVideoFormat(self,url):
		pass
	def manualVideoCheck(self):
		pass
	def homeContent(self,filter):
		result = {}
		cateManual = {
			"日本动漫": "r",
			"国产动漫": "g",
			"港台动漫": "gm",
			"动画电影": "v",
			"欧美动漫": "o"
		}
		classes = []
		for k in cateManual:
			classes.append({
				'type_name': k,
				'type_id': cateManual[k]
			})

		result['class'] = classes
		if (filter):
			result['filters'] = self.config['filter']
		return result
	def homeVideoContent(self):
		htmlTxt = self.webReadFile(urlStr="http://kt30.com/",header=self.header)
		videos = self.get_list(html=htmlTxt,patternTxt=r'a class="stui-vodlist__thumb lazyload" href="(?P<url>.+?)" title="(?P<title>.+?)" data-original="(?P<img>.+?)".+?"><span class="play hidden-xs"></span><span class="pic-text text-right">(?P<renew>.+?)</span></a>')
		result = {
			'list': videos
		}
		return result

	def categoryContent(self,tid,pg,filter,extend):
		result = {}
		year='0'#年份
		types='0'#类型
		area='all'#地区
		url = 'http://kt30.com/{0}/index_{1}.html'.format(tid,pg)
		htmlTxt=self.webReadFile(urlStr=url,header=self.header)
		videos=[]
		videos = self.get_list(html=htmlTxt,patternTxt=r'<a class="stui-vodlist__thumb lazyload" href="(?P<url>.+?)" title="(?P<title>.+?)" data-original="(?P<img>.+?)".+?"><span class="play hidden-xs"></span><span class="pic-text text-right">(?P<renew>.+?)</span></a>')
		numvL = len(videos)
		result['list'] = videos
		result['page'] = pg
		result['pagecount'] = pg if numvL<17 else 9999
		result['limit'] = numvL
		result['total'] = numvL
		return result

	def detailContent(self,array):
		aid = array[0].split('###')
		idUrl=aid[1]
		title=aid[0]
		pic=aid[2]
		playFrom = []
		vodItems = []
		videoList=[]
		htmlTxt = self.webReadFile(urlStr=idUrl,header=self.header)
		if len(htmlTxt)<5:
			return {'list': []}
		line=self.get_RegexGetTextLine(Text=htmlTxt,RegexText=r'</span><h3 class="title">(.+?)</h3></div>',Index=1)
		playFrom=[self.removeHtml(txt=vod) for vod in line]
		
		if len(line)<1:
			return {'list': []}
		circuit=self.get_lineList(Txt=htmlTxt,mark='<ul class="stui-content__playlist',after='</ul>')
		# print(circuit[0])
		# return
		for vod in circuit:
			vodItems = self.get_EpisodesList(html=vod,RegexText=r'<a href="(?P<url>.+?)">(?P<title>.+?)</a>')
			joinStr = "#".join(vodItems)
			videoList.append(joinStr)
		
		temporary=self.get_RegexGetTextLine(Text=htmlTxt,RegexText=r'<a href="/vodsearch/----%|\w+?---------.html" target="_blank">(.+?)</a>',Index=1)
		typeName="/".join(temporary)
		year=self.get_RegexGetText(Text=htmlTxt,RegexText=r'<a href="/vodsearch/-------------\d{4}.html" target="_blank">(\d{4})</a>',Index=1)
		temporary=self.get_RegexGetTextLine(Text=htmlTxt,RegexText=r'<a href="/vodsearch/-.+?------------.html" target="_blank">(.+?)</a>',Index=1)
		act="/".join(temporary)
		temporary=self.get_RegexGetTextLine(Text=htmlTxt,RegexText=r'<a href="/vodsearch/-----%+?|\w+?--------.html" target="_blank">(.+?)</a>',Index=1)
		dir="/".join(temporary)
		area=self.get_RegexGetText(Text=htmlTxt,RegexText=r'地区：</b>(.*?)<b>',Index=1)
		
		#area=self.get_RegexGetText(Text=htmlTxt,RegexText=r'>语言：\s{0,4}(.*?)</p>',Index=1)
		cont=self.get_RegexGetText(Text=htmlTxt,RegexText=r'简介：(.+?)<a href="#desc">详情',Index=1)
		

		vod = {
			"vod_id": array[0],
			"vod_name": title,
			"vod_pic": pic,
			"type_name": self.removeHtml(txt=typeName),
			"vod_year": year,
			"vod_area": self.removeHtml(txt=area),
			"vod_remarks": "",
			"vod_actor":  self.removeHtml(txt=act),
			"vod_director": self.removeHtml(txt=dir),
			"vod_content": self.removeHtml(txt=cont)
		}
		vod['vod_play_from'] = '$$$'.join(playFrom)
		vod['vod_play_url'] =  "$$$".join(videoList)

		result = {
			'list': [
				vod
			]
		}
		return result

	def verifyCode(self):
		pass

	def searchContent(self,key,quick):
		Url='http://kt30.com/vodsearch/-------------.html?wd={0}'.format(urllib.parse.quote(key))
		htmlTxt = self.webReadFile(urlStr=Url,header=self.header)
		videos = self.get_list(html=htmlTxt,patternTxt=r'<a class="v-thumb stui-vodlist__thumb lazyload" href="(?P<url>.+?)" title="(?P<title>.+?)" data-original="(?P<img>.+?)".+?</span><span class="pic-text text-right">(?P<renew>.+?)</span></a>')
		result = {
				'list': videos
			}
		return result

	def playerContent(self,flag,id,vipFlags):
		result = {}
		parse=1
		jx=0
		url=id
		htmlTxt=self.webReadFile(urlStr=url,header=self.header)
		temporary=self.get_lineList(Txt=htmlTxt,mark=r'var player_aaaa=',after='</script>')
		
		if len(temporary)>0:
			jRoot=json.loads(temporary[0][16:])
			url=jRoot['url']
			if len(url)<5:
				url=id		
			else:	
				parse=0
		result["parse"] = parse#1=嗅探,0=播放
		result["playUrl"] = ''
		result["url"] = url
		result['jx'] = jx#1=VIP解析,0=不解析
		result["header"] = ''	
		return result
	config = {
		"player": {},
		"filter": {}
	}
	header = {
		"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.54 Safari/537.36",
		'Host': 'kt30.com',
		"Referer": "http://kt30.com/"
		}

	def localProxy(self,param):
		return [200, "video/MP2T", action, ""]
#-----------------------------------------------自定义函数-----------------------------------------------
	#访问网页
	def webReadFile(self,urlStr,header):
		html=''
		req=urllib.request.Request(url=urlStr,headers=header)#,headers=header
		with  urllib.request.urlopen(req)  as response:
			html = response.read().decode('utf-8')
		return html
	#正则取文本
	def get_RegexGetText(self,Text,RegexText,Index):
		returnTxt=""
		Regex=re.search(RegexText, Text, re.M|re.S)
		if Regex is None:
			returnTxt=""
		else:
			returnTxt=Regex.group(Index)
		return returnTxt
	#取集数
	def get_EpisodesList(self,html,RegexText):
		ListRe=re.finditer(RegexText, html, re.M|re.S)
		videos = []
		for vod in ListRe:
			url = vod.group('url')
			title =vod.group('title')
			if len(url) == 0:
				continue
			if url.find('http:') <0:
				url='http://kt30.com'+url
			videos.append(title+"$"+url)
		return videos
	#取剧集区
	def get_lineList(self,Txt,mark,after):
		circuit=[]
		origin=Txt.find(mark)
		
		while origin>8:
			end=Txt.find(after,origin)
			circuit.append(Txt[origin:end])
			origin=Txt.find(mark,end)
		return circuit	
	#正则取文本,返回数组	
	def get_RegexGetTextLine(self,Text,RegexText,Index):
		returnTxt=[]
		ListRe=istRe=re.finditer(RegexText, Text, re.M|re.S)
		for value in ListRe:
			t=value.group(Index)
			if t==None:
				continue
			returnTxt.append(t)	
		return returnTxt
	#分类取结果
	def get_list(self,html,patternTxt):
		ListRe=re.finditer(patternTxt, html, re.M|re.S)
		videos = []
		head="http://kt30.com"
		for vod in ListRe:
			url = vod.group('url')
			title =self.removeHtml(txt=vod.group('title'))
			img =vod.group('img')
			renew=vod.group('renew')
			if len(url) == 0:
				continue
			if len(img)<5:
				img='https://agit.ai/lanhaidixingren/Tvbox/raw/branch/master/CoverError.png'
			if self.get_RegexGetText(Text=img,RegexText='(https{0,1}:)',Index=1)=='':
				img=head+img
			# print(title)
			videos.append({
				"vod_id":"{0}###{1}###{2}".format(title,head+url,img),
				"vod_name":title,
				"vod_pic":img,
				"vod_remarks":renew
			})
		return videos
	#删除html标签
	def removeHtml(self,txt):
		soup = re.compile(r'<[^>]+>',re.S)
		txt =soup.sub('', txt)
		return txt.replace("&nbsp;"," ")
	#番剧
	def get_list_fanju(self,html):
		ListRe=re.finditer('class="jtxqj"><a href="(?P<url>.+?)" title="(?P<title>.+?)" target="_self">(?P<renew>.+?)</a>', html, re.M|re.S)
		videos = []
		head="http://ktkkt8.com"
		img='https://agit.ai/lanhaidixingren/Tvbox/raw/branch/master/%E5%B0%81%E9%9D%A2.jpeg'
		for vod in ListRe:
			url = vod.group('url')
			title =self.removeHtml(txt=vod.group('title'))
			renew=vod.group('renew')
			if len(url) == 0:
				continue
			videos.append({
				"vod_id":"{0}###{1}###{2}".format(title,head+url,img),
				"vod_name":title,
				"vod_pic":img,
				"vod_remarks":renew
			})
		return videos

# T=Spider()
# l=T.homeVideoContent()
# l=T.searchContent(key='柯南',quick='')
# l=T.categoryContent(tid='r',pg='1',filter=False,extend={})
# for x in l['list']:
# 	print(x['vod_id'])
# mubiao= l['list'][1]['vod_id']
# playTabulation=T.detailContent(array=[mubiao,])
# # print(playTabulation)
# vod_play_from=playTabulation['list'][0]['vod_play_from']
# vod_play_url=playTabulation['list'][0]['vod_play_url']
# url=vod_play_url.split('$$$')
# vod_play_from=vod_play_from.split('$$$')[0]
# url=url[0].split('$')
# url=url[1].split('#')[0]
# print(url)
# m3u8=T.playerContent(flag=vod_play_from,id=url,vipFlags=True)
# print(m3u8)