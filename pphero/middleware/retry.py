"""
An extension to retry failed requests that are potentially caused by temporary
problems such as a connection timeout or HTTP 500 error.
You can change the behaviour of this middleware by modifing the scraping settings:
RETRY_TIMES - how many times to retry a failed page
RETRY_HTTP_CODES - which HTTP response codes to retry
Failed pages are collected on the scraping process and rescheduled at the end,
once the spider has finished crawling all regular (non failed) pages.
"""
import logging

from scrapy.core.downloader.handlers.http11 import TunnelError
from scrapy.http import Request
from scrapy.utils.python import global_object_name
from scrapy.utils.response import response_status_message
from scrapy.exceptions import IgnoreRequest
from twisted.internet import defer
from twisted.internet.error import (
    ConnectError,
    ConnectionDone,
    ConnectionLost,
    ConnectionRefusedError,
    DNSLookupError,
    TCPTimedOutError,
    TimeoutError,
)
from twisted.web.client import ResponseFailed

logger = logging.getLogger(__name__)


class RetryMiddleware:
    # IOError is raised by the HttpCompression middleware when trying to
    # decompress an empty response
    EXCEPTIONS_TO_RETRY = (defer.TimeoutError, TimeoutError, DNSLookupError,
                           ConnectionRefusedError, ConnectionDone, ConnectError,
                           ConnectionLost, TCPTimedOutError, ResponseFailed,
                           IOError, TunnelError)

    def __init__(self, settings):
        self.max_retry_times = settings.getint('RETRY_TIMES')
        self.retry_http_codes = set(int(x) for x in settings.getlist('RETRY_HTTP_CODES'))
        self.priority_adjust = settings.getint('RETRY_PRIORITY_ADJUST')
        self.dirSpider=None
    @classmethod
    def from_crawler(cls, crawler):
        logger = crawler.spider.logger
        return cls(crawler.settings)

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
            if not request.meta.get("p_count"):
                request.meta["p_count"]=0
            request.meta["p_count"]+=1
            if request.meta["p_count"]>20:
                raise IgnoreRequest("max request")
            spider.before_request(request)
    def process_response(self, request, response, spider):
        if not self.dirSpider:
            self.dirSpider=dir(spider)
        dirSpider = self.dirSpider
        if request.meta.get('dont_retry', False):
            return response
        if response.status in self.retry_http_codes:
            reason = response_status_message(response.status)
            return self._retry(request, reason, spider) or response
        if "check_retry" in dirSpider:
            retryreq = spider.check_retry(request.copy(), response)
            if isinstance(retryreq, Request):
                reason = retryreq.meta.get("retry_reason") or "custom retry check"
                return self._retry(retryreq, reason, spider) or response
        if "before_response" in dirSpider:
            response = spider.before_response(request, response)
        return response

    def process_exception(self, request, exception, spider):
        if not self.dirSpider:
            self.dirSpider=dir(spider)
        dirSpider = self.dirSpider
        if "check_exception" in dirSpider:
            _req=request.copy()
            _req.dont_filter=True
            return spider.check_exception(_req, exception)
        if (
                isinstance(exception, self.EXCEPTIONS_TO_RETRY)
                and not request.meta.get('dont_retry', False)
        ):
            return self._retry(request, exception, spider)

    def _retry(self, request, reason, spider):
        retries = request.meta.get('retry_times', 0) + 1

        retry_times = self.max_retry_times

        if 'max_retry_times' in request.meta:
            retry_times = request.meta['max_retry_times']

        stats = spider.crawler.stats
        if retries <= retry_times:
            logger.debug("Retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})
            retryreq = request.copy()
            retryreq.meta['retry_times'] = retries
            retryreq.dont_filter = True
            retryreq.priority = request.priority + self.priority_adjust

            if isinstance(reason, Exception):
                reason = global_object_name(reason.__class__)

            stats.inc_value('retry/count')
            stats.inc_value('retry/reason_count/%s' % reason)
            return retryreq
        else:
            stats.inc_value('retry/max_reached')
            logger.error("Gave up retrying %(request)s (failed %(retries)d times): %(reason)s",
                         {'request': request, 'retries': retries, 'reason': reason},
                         extra={'spider': spider})
