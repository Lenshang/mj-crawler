from scrapy.http import Request,Response
from scrapy.exceptions import IgnoreRequest
class RequestMiddleware:
    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        dirSpider=dir(spider)
        if "before_request" in dirSpider:
            spider.before_request(request)