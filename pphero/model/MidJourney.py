
import scrapy
class MidJourneyItem(scrapy.Item):
    id=scrapy.Field()
    img_url=scrapy.Field()
    raw_json=scrapy.Field()
    raw_file_path=scrapy.Field()
    file_path=scrapy.Field()
