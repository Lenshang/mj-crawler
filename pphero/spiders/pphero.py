from datetime import datetime
import json
from logging import debug
import time
from dateutil.rrule import YEARLY
import os
import requests
import scrapy
from scrapy import item
from pphero.model.PromptHero import PromptHeroItem
from pphero.utils.ex_scrapy_obj import ExScrapyObj
from scrapy.http import Request
from scrapy.http.response.html import HtmlResponse
from urllib import parse

class PromptHero(scrapy.Spider):
    name = 'pphero'
    allowed_domains = ['prompthero.com']
    DEBUG=False
    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'REACTOR_THREADPOOL_MAXSIZE': 1,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
        "CONCURRENT_REQUESTS_PER_IP": 1,
        "DOWNLOAD_DELAY": 0,
        'DOWNLOAD_TIMEOUT':0,
        "DEPTH_PRIORITY": 0,
        "RETRY_TIMES": 200,
        "COOKIES_ENABLED": False,
        "HTTPERROR_ALLOWED_CODES": [403,500,503],
        "MEDIA_ALLOW_REDIRECTS":True,
        "RETRY_HTTP_CODES":[],
        "ITEM_PIPELINES": {
            'pphero.pipelines.ImagePipeline.ImagePipeline': 100,
            'pphero.pipelines.SqlitePipeline.SqlitePipeline': 200,
        },
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
        "accept": "application/json, text/plain, */*",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "referer":"https://prompthero.com/"
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.p=0
        self.proxies=[]
    def start_requests(self):
        self.logger.info("启动")
        cookies={
            "_ga":"GA1.1.857909903.1711964769",
            "_ga_WKCTBRMXSP":"GS1.1.1712125075.5.1.1712125091.0.0.0",
            "cf_clearance":"yHRTbjCaMrWBFHvqeM2yire9cn8d1ICShEsyQDCKbD4-1712125075-1.0.1.1-9HjBKuy6YszVjfAG1eR7qq4Gzq1pVq8.pFC7egRjw9aY5cnbhUMBCO9z8plkiNHGH1K5tbQrrSnswFxtUuwaHw",
            "_prompthero_session":"sPm67%2FoC9Z1%2B3aclpTTQtwRXYJ4X42eQ8aCx7RO3POBoWPjAtaSW21oDT1Z7rPmYF1YLLgVjkRFFzggllT%2FRxhTKd8pLIOCUit%2BSVKQhoCNasXN%2BR8B9Ebhcw0kcG47WGkb%2F8NevjgVX7LQcsNOgNrRqXEBfy8ZKWxPGFV%2FR2Caw0zAGvwirItepC9G9NQcmyQkJgObjpnKO4%2BJvD2%2BpGHjnw6B%2FouKym9QpFCMK%2FNYU%2FU6j2vFZuz8IE6FP%2BAj9FJ%2BEnmbBtJU55yXwzNysXO%2B0Jr5GrAw9Wc1IhIyLIPIHhySoGXidY%2FFzKSCkBWQseu%2BjdXUdIsTS44DLqd%2FSHP1hVMqNtzDmgPEo%2FsMWSeGIondFbc4pORr2N%2FYVP%2FdE2EhCnlJ8KjSnBUWGhR7MpHpUe3zWywIvcDNdJrXWED%2BDynHjgKlY9gaMSuNPIwvViUPGUcQzfIPrr3c%3D--Qe6mem6zMA4cpNJY--G1cvBpWXS5jIMqDsEMjUGg%3D%3D",
            "remember_user_token":"eyJfcmFpbHMiOnsibWVzc2FnZSI6Ilcxc2lNbU15TldabVpXUXROR0ZqTWkwMFlUYzFMV0ZrWm1VdE9HTmpaVFpoWW1FNU56Z3lJbDBzSWlReVlTUXhNaVIwWW5CVlpXUjFjWFJ6TXpaVVZtSjVaR2x2Y2xGUElpd2lNVGN4TWpFeU5UQTRPUzQxTkRNd01qVTFJbDA9IiwiZXhwIjoiMjAyNC0wNC0xN1QwNjoxODowOS41NDNaIiwicHVyIjoiY29va2llLnJlbWVtYmVyX3VzZXJfdG9rZW4ifX0%3D--791885624242edc90b0d3cf558c96b4233406216"
        }
        url=f"https://prompthero.com/featured?page=1"
        yield Request(url, callback=self.parse_data,headers=self.create_header(cookies),dont_filter=True,meta={
            "page":1,
            "ck":cookies
        })

    def parse_data(self,response):
        selector=ExScrapyObj(response)
        for item in selector.xpath("//div[@id='prompt-masonry']//div[@class='prompt-card-image-backdrop']"):
            _item = PromptHeroItem()
            _item["url"]="https://prompthero.com/prompt/"+item.xpath("./@id").extract().FirstOrDefaultString().split("-")[-1]
            _item["img_url"]=item.xpath("./@style").extract().FirstOrDefaultString()
            _item["prompt_text"]=item.xpath(".//p[@class='masonry-hide-unless-hover the-prompt-text mb-1']/text()").extract().FirstOrDefaultString()
            _item["file_path"]="./download_images/"+_item["url"].split("/")[-1]+".png"

            _item["img_url"]=(_item["img_url"].replace("background-image: url('","")[:-3]
                              .replace("2988725aa75d479f95ec8c66cbedc32bdf24b6db","935666d13f63ed5aca9daa2416340e3a90b6014e")
                              .replace("QUl3T2dwellYWmxjbnNKT2hOemRXSnpZVzF3YkdWZmJXOWtaVWtpQjI5dUJqb0dSVlE2Q25OMGNtbHdWRG9PYVc1MFpYSnNZV05sVkRvTWNYVmhiR2wwZVdsQiIsImV4cCI6bnVsbCwicHVyIjoidmFyaWF0aW9uIn19","QWd3T2dwellYWmxjbnNKT2hOemRXSnpZVzF3YkdWZmJXOWtaVWtpQjI5dUJqb0dSVlE2Q25OMGNtbHdWRG9PYVc1MFpYSnNZV05sVkRvTWNYVmhiR2wwZVdsZiIsImV4cCI6bnVsbCwicHVyIjoidmFyaWF0aW9uIn19"))
            
            yield _item
        cookies=response.meta["ck"].copy()
        cookies["_prompthero_session"]=response.headers["Set-Cookie"].decode("utf-8").split(";")[0].split("=")[1]

        _meta={
            "page":response.meta["page"]+1,
            "ck":cookies
        }
        url=f"https://prompthero.com/featured?page="+str(_meta["page"])
        yield Request(url, callback=self.parse_data,headers=self.create_header(cookies),dont_filter=True,meta=_meta)
        
    def create_header(self,cookie:dict):
        headers=self.headers.copy()
        ck=[]
        for item in cookie.keys():
            parse.quote(cookie[item])
            ck.append(item+"="+parse.quote(cookie[item]))
        headers["Cookie"]=";".join(ck)
        return headers
    
    def before_request(self, request):
        if request.meta.get("retry_times") and request.meta["retry_times"]>1:
            # 切代理
            self.p+=1
            params={"name":self.proxies[self.p%len(self.proxies)]}
            url="http://192.168.31.153:9090/proxies/GLOBAL"
            r=requests.put(url, json=params, headers={
                'content-type': 'application/json',
                "Authorization":"Bearer 7f74162fc2d68bfdf74141616d30b09f5a65dcd440ffa1536f4679dd297aab70"
                })
        request.meta['proxy'] = "http://192.168.31.153:7890"
        return request