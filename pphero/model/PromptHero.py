
import scrapy
class PromptHeroItem(scrapy.Item):
    url=scrapy.Field()
    img_url=scrapy.Field()
    prompt_text=scrapy.Field()
    file_path=scrapy.Field()
