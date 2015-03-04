from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.utils.serialize import ScrapyJSONEncoder
from twisted.internet.task import LoopingCall


class DockerhubExtension(object):

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.crawler = crawler
        self.job_path = crawler.settings.get('JOB_PATH')
        if not self.job_path:
            raise NotConfigured('no JOB_PATH set')

        self.json_encoder = ScrapyJSONEncoder()
        self.looping_call = LoopingCall(self.store_job_info)
        self.looping_call.start(5)
        crawler.signals.connect(self.store_job_info,
                                signal=signals.spider_closed)

    def store_job_info(self):
        with open(self.job_path, 'w') as f:
            stats = self.crawler.stats.get_stats()
            job_info = {
                'stats': stats
            }
            job_info_json = self.json_encoder.encode(job_info)
            f.write(job_info_json)
