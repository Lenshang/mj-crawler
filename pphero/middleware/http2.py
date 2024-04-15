from scrapy.http.response.html import HtmlResponse,TextResponse
from scrapy.http import Response
import httpx

class Http2Middleware(object):
    async def process_request(self, request, spider):
        url = request.url
        headers={}
        for key in request.headers.keys():
            if type(key) is bytes:
                headers[key.decode("utf-8")]=request.headers[key].decode("utf-8")
            else:
                headers[key]=request.headers[key]
        async with httpx.AsyncClient(http2=False, verify=False,proxies=request.meta.get("proxy")) as client:
            res=await client.get(url=url, headers=headers)

        response = TextResponse(url,body=res.content,encoding='utf-8',request=request,status=res.status_code)
        return response
