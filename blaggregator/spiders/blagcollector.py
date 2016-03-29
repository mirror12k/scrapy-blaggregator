# -*- coding: utf-8 -*-
import scrapy


class BlagcollectorSpider(scrapy.Spider):
	name = "blagcollector"
	start_urls = []

	def __init__(self, *args, **kwargs):
		super(BlagcollectorSpider, self).__init__(*args, **kwargs)
		self.start_urls.append('http://www.redblue.team/2016/02/a-soft-introduction-to-malware-analysis.html')
	def parse(self, res):
		print res.body
