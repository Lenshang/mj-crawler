import json
import re
from ExObject.ExObject import ExObject
from scrapy.selector.unified import SelectorList

class ExScrapyObj(ExObject):
    def xpath(self,query):
        return ExScrapyObj(self.default.xpath(query))

    def extract(self):
        return ExScrapyObj(self.default.extract())

    def FirstOrDefault(self):
        if type(self.default) is SelectorList:
            return self.extract().FirstOrDefault()
        return super().FirstOrDefault()

    def FirstOrDefaultString(self)->str:
        if type(self.default) is SelectorList:
            return self.extract().FirstOrDefaultString()
        return super().FirstOrDefaultString()

    def LastOrDefaultString(self):
        if type(self.default) is SelectorList:
            return self.extract().LastOrDefaultString()
        return super().LastOrDefaultString()

    def AllString(self):
        if type(self.default) is SelectorList:
            r=[]
            for item in self.default.extract():
                r.append(str(item))
            return "".join(r)
        return super().LastOrDefaultString()

    def __next__(self):
        try:
            if type(self.default) is SelectorList:
                if "iter" not in dir(self):
                    self.iter=self.default.__iter__()
                #return ExScrapyObj(self.default.__next__())
                return ExScrapyObj(next(self.iter))
            else:
                return ExScrapyObj(self.defaultIter.__next__())
        except:
            raise StopIteration()