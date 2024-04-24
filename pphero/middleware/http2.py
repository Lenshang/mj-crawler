from scrapy.http.response.html import HtmlResponse,TextResponse
from scrapy.http import Response
import httpx, ssl, certifi
import time
import random
from curl_cffi import requests
class TLSMiddleware(object):
    async def process_request(self, request, spider):
        try:


            url = request.url
            headers={}
            for key in request.headers.keys():
                if type(key) is bytes:
                    headers[key.decode("utf-8")]=request.headers[key].decode("utf-8")
                else:
                    headers[key]=request.headers[key]

            async with requests.AsyncSession(proxy=request.meta.get("proxy")) as session:
                res = await session.get(
                    url,
                    headers=headers,
                    impersonate="chrome101"
                )

            response = TextResponse(url,body=res.content,encoding='utf-8',request=request,status=res.status_code)
            # response = TextResponse(url,body=res.content,encoding='utf-8',request=request,status=429)
            return response
        

        except Exception as e:
            spider.logger.info("retry:"+str(e))
            return TextResponse(url,body="",encoding='utf-8',request=request,status=500)
        
class Http2Middleware(object):
    def __init__(self) -> None:
        # self.context = DESAdapter().get_ssl_context()
        # self.context.load_verify_locations(certifi.where()) 
        # self.context.load_verify_locations("./mj_cert.cer")
        self.context=ssl._create_unverified_context(cafile="./mj_cert.cer")
    async def process_request(self, request, spider):
        try:
            url = request.url
            headers={}
            for key in request.headers.keys():
                if type(key) is bytes:
                    headers[key.decode("utf-8")]=request.headers[key].decode("utf-8")
                else:
                    headers[key]=request.headers[key]

            async with httpx.AsyncClient(http2=False, verify=self.context,proxies=request.meta.get("proxy")) as client:
                res=await client.get(url=url, headers=headers,timeout=60000)

            response = TextResponse(url,body=res.content,encoding='utf-8',request=request,status=res.status_code)
            # response = TextResponse(url,body=res.content,encoding='utf-8',request=request,status=429)
            return response
        except Exception as e:
            spider.logger.info("retry:"+str(e))
            return TextResponse(url,body="",encoding='utf-8',request=request,status=500)
        
    # def process_request(self, request, spider):
    #     try:
    #         url = request.url
    #         headers={}
    #         for key in request.headers.keys():
    #             if type(key) is bytes:
    #                 headers[key.decode("utf-8")]=request.headers[key].decode("utf-8")
    #             else:
    #                 headers[key]=request.headers[key]
    #         with httpx.Client(http2=False, verify=False,proxies=request.meta.get("proxy")) as client:
    #             res=client.get(url=url, headers=headers,timeout=10)

    #         response = TextResponse(url,body=res.content,encoding='utf-8',request=request,status=res.status_code)
    #         return response
    #     except Exception as e:
    #         spider.logger.info("retry:"+str(e))
    #         time.sleep(10)
    #         return self.process_request(request,spider)