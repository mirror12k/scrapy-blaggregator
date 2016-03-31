# -*- coding: utf-8 -*-
import scrapy
import urlparse
import re

from blaggregator.items import RSSLinkItem

from scrapy import optional_features
optional_features.remove('boto')


class BlagcollectorSpider(scrapy.Spider):
	name = "blagcollector"


	def __init__(self, *args, **kwargs):
		super(BlagcollectorSpider, self).__init__(*args, **kwargs)
		# self.start_urls.append('http://www.redblue.team/2016/02/a-soft-introduction-to-malware-analysis.html')
		self.start_urls = []
		self.start_urls.append('http://blog.h3xstream.com/')

		self.crawled = {}

		self.localAdded = 0
		self.localRequests = 0
		self.remoteAdded = 0
		self.remoteRequests = 0

	def parse(self, res):
		if isinstance(res, scrapy.http.HtmlResponse): # make sure we have an html response
			location = urlparse.urlparse(res.url).netloc
			# print 'crawled', location

			# collect all of the text on page into a single giant string
			text = ' '.join(map(lambda s: s.strip(), res.xpath('//*[not(self::script) and not(self::style)]/text()').extract()))

			# extract any keywords that we are looking for
			words = re.findall(r'''\s(
				java(?:script)?|
				js|
				ajax|
				node\-?js|
				python|
				PHP|
				perl|
				ruby|
				assembly|
				x86(?:[\-_ ]64)?|
				(?:my)?sql(?:i|lite)?|
				\.net|
				databases?|

				computers?|
				security|

				microsoft|
				ubuntu|
				linux|
				gentoo|
				redhat|

				cryptography|
				hash|
				md5|
				sha(?:1|2|3|256|512)?|
				blowfish|
				cipher|
				aes(?:128|256)?|
				des|
				rc4|

				buffering|
				crawl(?:ing)?|
				spider(?:ing)?|
				malware|
				exploit(?:s|ing|\-?kits?)?|
				rop|
				xss|
				file inclusions?|
				deserialization|
				networks?|
				(?:event ?)?logs?|
				sandbox|
				analyst|
				(?:zero|0)\-?day|
				cyber|
				malicious|

				https?|
				(?:open\-?)?ssl|tls|

				wordpress|
				Joomla|
				Drupal|
				cms|
				plugins?
			)\b''', text, flags=re.I|re.X)

			# unique the words
			words = list(set(map(lambda s: s.lower(), words)))

			# print text
			# print "words:", words
			if len(words) > 5:
				# print "words:", ', '.join(words)

				# get the rss link if we can find one
				rssLinks = res.xpath('//link[@type = "application/rss+xml"]/@href')
				if rssLinks:
					# get the rss url
					rss = urlparse.urljoin(res.url, rssLinks[0].extract())
					# produce the rss link
					yield RSSLinkItem(domain=location, link=rss, keywords=words)
					# print 'rss: ', rss

				# get regular links
				links = self.extractLinks(res)
				localLinks = filter(lambda url: url.netloc == location, links) # get local urls finding more remote urls
				remoteLinks = filter(lambda url: url.netloc != location, links) # get remote urls for finding more blogs

				# add the remote urls
				for item in self.addRemoteLinks(remoteLinks, True):
					yield item

				localLinks = list(set(localLinks))

				# by using 5 .. len(words), got about 1/5th the links from local pages
				# get some local links
				for i in range(0, len(remoteLinks) / 5):
					if localLinks:
						url = localLinks.pop(0)
						# print "adding local link: ", url.geturl()
						yield scrapy.Request(url.geturl(), callback=self.parseRemoteLinks)

	def extractLinks(self, res):
		links = [ urlparse.urlparse(link) for link in res.xpath('//a/@href').extract() ]
		links = filter(lambda url: url.scheme == 'http' or url.scheme == 'https', links) # filter http urls
		links = filter(lambda url: not re.search(r'\.(png|jpe?g|webm|mp[34]|avi|gif|zip|tar(\.[gx]z)?|exe|pdf)\Z', url.path, flags=re.I), links) # filter url file extensions
		return links

	def parseRemoteLinks(self, res):
		if isinstance(res, scrapy.http.HtmlResponse): # make sure we have an html response
			location = urlparse.urlparse(res.url).netloc

			links = self.extractLinks(res)
			remoteLinks = filter(lambda url: url.netloc != location, links) # get remote urls for finding more blogs

			for item in self.addRemoteLinks(remoteLinks, False):
				yield item


	def addRemoteLinks(self, links, isRemote):
		added = 0
		# unique the urls
		uniqueLinks = {}
		for link in links:
			uniqueLinks[link.netloc] = link

		# add them to the tocrawl list
		# self.addCrawlLinks(uniqueLinks)
		for location, link in uniqueLinks.iteritems():
			if self.crawled.get(location) is None:
				# print 'adding link:', link.geturl()
				self.crawled[link.netloc] = True
				yield scrapy.Request(link.geturl())
				added += 1
		if isRemote:
			self.remoteRequests += 1
			self.remoteAdded += added
			if self.localRequests > 0:
				print "added: remote:", self.remoteAdded / self.remoteRequests, "vs local:", self.localAdded / self.localRequests
		else:
			self.localRequests += 1
			self.localAdded += added



