from datetime import datetime
import json
from logging import debug
from queue import Queue
import time
from dateutil.rrule import YEARLY
import os
import requests
import scrapy
import scrapy.http
import ua_generator
from scrapy import item
from pphero.model.PromptHero import PromptHeroItem
from pphero.model.MidJourney import MidJourneyItem
from pphero.utils.ex_scrapy_obj import ExScrapyObj
from ExObject.ExObject import ExObject
from ExObject.DateTime import DateTime
from scrapy.http import Request
from scrapy.http.response.html import HtmlResponse
from urllib import parse
import random as rd
class PromptHero(scrapy.Spider):
    name = 'mj'
    allowed_domains = ['midjourney.com']
    DEBUG=False
    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
        'REACTOR_THREADPOOL_MAXSIZE': 3,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 3,
        "CONCURRENT_REQUESTS_PER_IP": 3,
        "DOWNLOAD_DELAY": 0,
        'DOWNLOAD_TIMEOUT':0,
        "DEPTH_PRIORITY": 0,
        "RETRY_TIMES": 200,
        "COOKIES_ENABLED": False,
        "HTTPERROR_ALLOWED_CODES": [500,503,429],
        "MEDIA_ALLOW_REDIRECTS":True,
        "DEPTH_PRIORITY":1,
        "RETRY_HTTP_CODES":[],
        "ITEM_PIPELINES": {
            'pphero.pipelines.ImagePipeline.ImagePipeline': 100,
        },
        'DOWNLOADER_MIDDLEWARES' : {
            'pphero.middleware.retry.RetryMiddleware': 300,
            # 'pphero.middleware.http2.Http2Middleware': 400,
            'pphero.middleware.http2.TLSMiddleware': 400,
        }
    }
    headers = {
        "accept": "*/*",
        "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
        "sec-ch-ua": "\"Chromium\";v=\"122\", \"Not(A:Brand\";v=\"24\", \"Microsoft Edge\";v=\"122\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-csrf-protection": "1",
        "Referer": "https://www.midjourney.com/explore",
        "Referrer-Policy": "origin-when-cross-origin",
        "user-agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0"
    }

    def __init__(self, c=0,search=1,*args, **kwargs):
        super().__init__(*args, **kwargs)
        self.p=0
        self.proxies={}
        self.cookies= []
        
        with open("./mj_cookies.txt","r") as f:
            for line in f.readlines():
                if line:
                    self.cookies.append(line.strip())
        # with open("./proxy.json","r") as f:
        #      rawstr="".join(f.readlines())
        #      raw=json.loads(rawstr)
        #      self.proxies = {
        #         "http": "http://%(user)s:%(pwd)s@%(proxy)s/" % {"user": raw["username"], "pwd": raw["password"], "proxy": raw["tunnel"]},
        #         "https": "http://%(user)s:%(pwd)s@%(proxy)s/" % {"user": raw["username"], "pwd": raw["password"], "proxy": raw["tunnel"]}
        #     }
        self.c=int(c)
        self.search=int(search)
        self.save_path="/mnt/images"
        # self.save_path="D://midjourney"
        self.batch_size=5
        self.crawled=[]
        self.block_ua={}
        self.search_queue=Queue()
    def get_random_cookies(self):
        return self.cookies[rd.randint(0,len(self.cookies)-1)]
    def start_requests(self):
        self.logger.info("启动")

        if self.c==1:
            for item in os.listdir(self.save_path+"/info"):
                if item.endswith(".json"):
                    search_id=item[:-5]
                    url=f"https://www.midjourney.com/api/app/vector-search?prompt={search_id}&page=0&_ql=explore"

                    yield Request(url, callback=self.parse_data,headers=self.create_header(self.get_random_cookies()),dont_filter=True,meta={
                        "page":0,
                        "search_id":search_id
                    })
        elif self.c==2:
            kw=[]
            with open("./search_words.txt","r") as f:
                for line in f.readlines():
                    if line:
                        kw.append(parse.quote(line.strip()))
            for search_id in kw:
                url=f"https://www.midjourney.com/api/app/vector-search?prompt={search_id}&page=0&_ql=explore"

                yield Request(url, callback=self.parse_data,headers=self.create_header(self.get_random_cookies()),dont_filter=True,meta={
                    "page":0,
                    "search_id":search_id
                })
        else:
            for i in range(0,self.batch_size):
                url=f"https://www.midjourney.com/api/app/recent-jobs?amount=50&page={str(i)}&feed=random&_ql=explore"
                yield Request(url, callback=self.parse_data,headers=self.create_header(self.get_random_cookies()),dont_filter=True,meta={
                    "page":i,
                    "search_id":"",
                })


    def parse_data(self,response):
        jObj=ExObject.loadJson(response.text)
        for item in jObj["jobs"]:
            id=item["id"].ToString()
            _item=MidJourneyItem()
            _item["raw_json"]=json.dumps(item.ToOriginal())
            _item["id"]=id
            _item["img_url"]=f"https://cdn.midjourney.com/{item['parent_id'].ToString()}/0_0.webp"
            _item["file_path"]=self.save_path+"/image/"+id+".webp" #os.path.join(self.save_path,"./image/"+id+".webp")
            _item["raw_file_path"]=self.save_path+"/info/"+id+".json" #os.path.join(self.save_path,"./info/"+id+".json")

            if id not in self.crawled and "_ql=explore" in response.url and self.search==1:
                # self.search_queue.put(id)
                self.crawled.append(id)
                next_page=0
                url=f"https://www.midjourney.com/api/app/vector-search?prompt={id}&page=0&_ql=explore"
                yield Request(url, callback=self.parse_data,headers=self.create_header(self.get_random_cookies()),dont_filter=True,meta={
                    "page":next_page,
                    "search_id":id
                })
            yield _item
        if len(jObj["jobs"])==0:
            # next_page=0
            # search_id=self.search_queue.get()
            # url=f"https://www.midjourney.com/api/app/vector-search?prompt={search_id}&page=0&_ql=explore"
            # yield Request(url, callback=self.parse_data,headers=self.create_header(self.get_random_cookies()),dont_filter=True,meta={
            #     "page":next_page,
            #     "search_id":search_id
            # })
            return
        else:
            if response.meta['search_id']:
                next_page=response.meta["page"]+1
                url=f"https://www.midjourney.com/api/app/vector-search?prompt={response.meta['search_id']}&page={str(next_page)}&_ql=explore"
            else:
                next_page=response.meta["page"]+self.batch_size
                url=f"https://www.midjourney.com/api/app/recent-jobs?amount=50&page={str(next_page)}&feed=random&_ql=explore"
            yield Request(url, callback=self.parse_data,headers=self.create_header(self.get_random_cookies()),dont_filter=True,meta={
                "page":next_page,
                "search_id":response.meta['search_id']
            })

    def create_header(self,cookie:str):
        headers=self.headers.copy()
        # _header = self.get_ua()
        # headers = {
        #     "accept": "*/*",
        #     "accept-language": "en,zh-CN;q=0.9,zh;q=0.8,en-GB;q=0.7,en-US;q=0.6,zh-TW;q=0.5",
        #     "sec-ch-ua": _header["sec-ch-ua"],
        #     "sec-ch-ua-mobile": _header["sec-ch-ua-mobile"],
        #     "sec-ch-ua-platform": _header["sec-ch-ua-platform"],
        #     "sec-fetch-dest": "empty",
        #     "sec-fetch-mode": "cors",
        #     "sec-fetch-site": "same-origin",
        #     "x-csrf-protection": "1",
        #     "Referer": "https://www.midjourney.com/explore",
        #     "Referrer-Policy": "origin-when-cross-origin",
        #     "user-agent":_header["user-agent"]
        # }
        headers["cookie"]=cookie
        return headers
    
    
    def get_ua(self,level=0):
        if level>10:
            self.logger.info("没有可用UA,等待1分钟")
            time.sleep(60)
        elif level>20:
            self.logger.info("没有可用UA,等待10分钟")
            time.sleep(60*10)
        
        _header = ua_generator.generate(device='desktop', browser=('chrome', 'edge')).headers.get()
        ua=_header.get("user-agent")
        if not ua:
            ua=_header.get("User-Agent")
            _header["user-agent"]=_header["User-Agent"]
            del _header["User-Agent"]
        now=DateTime.Now()
        if self.block_ua.get(ua) and (now-self.block_ua.get(ua)).TotalMinute<120:
            return self.get_ua(level+1)
        # print("GETUA:"+ua)
        return _header
    
    def before_request(self, request:scrapy.Request):
        # if request.meta.get("retry_times") and request.meta["retry_times"]>1:
        #     # 切代理
        #     self.p+=1
        #     params={"name":self.proxies[self.p%len(self.proxies)]}
        #     url="http://192.168.31.153:9090/proxies/GLOBAL"
        #     r=requests.put(url, json=params, headers={
        #         'content-type': 'application/json',
        #         "Authorization":"Bearer "
        #         })
        # request.meta['proxy'] = "http://127.0.0.1:8888"
        
        if "cdn.midjourney.com" in request.url:
            _header = self.get_ua()
            header = {
                "Connection":"keep-alive",
                "sec-ch-ua":_header["sec-ch-ua"],
                "sec-ch-ua-mobile":_header["sec-ch-ua-mobile"],
                "sec-ch-ua-platform":_header["sec-ch-ua-platform"],
                "Upgrade-Insecure-Requests":"1",
                "User-Agent":_header["user-agent"],
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-User":"?1",
                "Sec-Fetch-Dest": "document",
                "Accept-Encoding":"gzip, deflate, br, zstd",
                "accept-language": "zh-CN,zh;q=0.9",
            }
            request.headers=header
            # request.meta['proxy'] = self.proxies["http"]
        return request
    
    def before_response(self, request:scrapy.Request,response:scrapy.http.TextResponse):
        raw=response.text
        if "cdn.midjourney.com" in request.url:
            if response.status==500:
                return request
            elif response.status==429 or raw[0:9]=="<!DOCTYPE":
                self.logger.info("check 429!")
                time.sleep(3)
                _ua=request.headers.get("User-Agent")
                if not _ua:
                    _ua=request.headers["user-agent"]
                self.block_ua[_ua]=DateTime.Now()
                _header = self.get_ua()
                header = {
                    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                    "accept-language": "zh-CN,zh;q=0.9",
                    "sec-fetch-dest": "document",
                    "sec-fetch-mode": "navigate",
                    "sec-fetch-site": "none",
                    "Sec-Fetch-User":"?1",
                    "x-csrf-protection": "1",
                    "Connection":"keep-alive",
                    "Upgrade-Insecure-Requests":"1",
                    **_header
                }
                request.headers=header
                return request
        return response
