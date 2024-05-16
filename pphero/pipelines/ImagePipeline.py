import scrapy
import os
import random as rd
from scrapy.pipelines.files import FilesPipeline
from scrapy.pipelines.images import ImagesPipeline
from pphero.model.MidJourney import MidJourneyItem
import ua_generator
class ImagePipeline(FilesPipeline):
    def __init__(self, store_uri, download_func=None, settings=None):
        super().__init__("/", download_func, settings)

    def get_media_requests(self, item, info):
        # if info.spider.name=="mj":
        #     _ua = ua_generator.generate(device='desktop', browser=('chrome', 'edge'))
        #     _header = _ua.headers.get()
        #     header = {
        #         "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        #         "accept-language": "zh-CN,zh;q=0.9",
        #         "sec-fetch-dest": "document",
        #         "sec-fetch-mode": "navigate",
        #         "sec-fetch-site": "none",
        #         "Sec-Fetch-User":"?1",
        #         "x-csrf-protection": "1",
        #         "Connection":"keep-alive",
        #         "Upgrade-Insecure-Requests":"1",
        #         **_header
        #     }
        # else:
        #     header=info.spider.headers.copy()
        if os.path.exists(item["file_path"]):
            print("skip:"+item["file_path"])
            return None
        return [scrapy.Request(item["img_url"],meta={"dbItem":item})]

    def file_path(self, request, response=None, info=None):
        dbItem=request.meta["dbItem"]
        r=dbItem["file_path"]
        return r
    
    def item_completed(self, results, dbItem, info):
        if len(results)==0:
            return dbItem
        if not results[0][0]:
            return dbItem
        
        if type(dbItem) is MidJourneyItem:
            with open(dbItem["raw_file_path"],"w") as f:
                f.write(dbItem["raw_json"])
        info.spider.logger.info(dbItem["file_path"]+" OK")
        return dbItem
