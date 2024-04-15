from scrapy.http.response.html import HtmlResponse,TextResponse
from scrapy.http import Response
import httpx
import time
class Http2Middleware(object):
    async def process_request(self, request, spider):
        try:
            url = request.url
            headers={}
            for key in request.headers.keys():
                if type(key) is bytes:
                    headers[key.decode("utf-8")]=request.headers[key].decode("utf-8")
                else:
                    headers[key]=request.headers[key]
            async with httpx.AsyncClient(http2=False, verify=False,proxies=request.meta.get("proxy")) as client:
                res=await client.get(url=url, headers=headers,timeout=10)

            response = TextResponse(url,body=res.content,encoding='utf-8',request=request,status=res.status_code)
            return response
        except Exception as e:
            spider.logger.info("retry:"+str(e))
            time.sleep(10)
            return await self.process_request(request,spider)
        
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