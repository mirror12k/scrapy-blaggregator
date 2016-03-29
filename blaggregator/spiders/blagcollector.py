# -*- coding: utf-8 -*-
import scrapy
import urlparse
import re

from blaggregator.items import RSSLinkItem



class BlagcollectorSpider(scrapy.Spider):
	name = "blagcollector"
	start_urls = []

	def __init__(self, *args, **kwargs):
		super(BlagcollectorSpider, self).__init__(*args, **kwargs)
		self.start_urls.append('http://www.redblue.team/2016/02/a-soft-introduction-to-malware-analysis.html')

		self.crawled = {}
		for url in self.start_urls:
			self.crawled[urlparse.urlparse(url).netloc] = True
		self.toCrawl = []

		self.activeCrawling = 1
		self.maxActiveCrawling = 10
	def parse(self, res):
		location = urlparse.urlparse(res.url).netloc
		# print 'crawled', location

		self.crawled[location] = True
		self.activeCrawling -= 1

		if isinstance(res, scrapy.http.HtmlResponse):
			rssLinks = res.xpath('//link[@type = "application/rss+xml"]/@href')
			if len(rssLinks) > 0:
				# get the rss url
				rss = rssLinks[0].extract()
				# print 'rss: ', rss

				rss = urlparse.urljoin(res.url, rss)

				yield RSSLinkItem(domain=location, link=rss)

				# get regular links
				links = [ urlparse.urlparse(link) for link in res.xpath('//a/@href').extract() ]
				links = filter(lambda url: url.scheme == 'http' or url.scheme == 'https', links) # filter http urls
				links = filter(lambda url: url.netloc != location, links) # filter remote urls
				links = filter(lambda url: not re.search(r'\.(png|jpe?g|zip|tar(\.[gx]z)?)\Z', url.path, flags=re.I), links) # filter url file extensions

				# unique the urls
				uniqueLinks = {}
				for link in links:
					uniqueLinks[link.netloc] = link

				# add them to the tocrawl list
				self.addCrawlLinks(uniqueLinks)

		for req in self.nextRequests():
			yield req



	def addCrawlLinks(self, links):
		for location, link in links.iteritems():
			if self.crawled.get(location) is None:
				# print 'adding link:', link.geturl()
				self.crawled[link.netloc] = True
				self.toCrawl.append(link.geturl())

	def nextRequests(self):
		while self.activeCrawling < self.maxActiveCrawling:
			self.activeCrawling += 1
			yield scrapy.Request(self.toCrawl.pop(0), callback=self.parse, errback=self.onError)

	def onError(self, err):
		print "error occured:", err
		self.activeCrawling -= 1
		for req in self.nextRequests():
			yield req
