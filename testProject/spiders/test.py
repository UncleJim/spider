# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
import sqlite3
from scrapy.selector import Selector

class TestSpider(scrapy.Spider):
    name = "test"
    #限定域范围
    allowed_domains = ["10.100.136.174"]
    #起始URL
    start_urls = (
        'http://10.100.136.174/apkcook/',
    )
    #存储到数据库
    db_name = 'urls1.db'
    db_conn = ''
    db_cursor = ''
    #cookie
    login_cookie = {'PHPSESSID': '3frtusoe99pvi62j43273cj9v3'}

    ##override，爬虫最先执行的函数
    def start_requests(self):
        self.db_conn = sqlite3.connect(self.db_name)
        self.db_cursor = self.db_conn.cursor()
        self.db_cursor.execute('create table if not exists urls(url varchar(666) UNIQUE, summary varchar(333))')
        #request为发起请求,with cookie
        return [Request(self.start_urls[0], meta = {'cookiejar' : 1}, cookies=self.login_cookie)]

    #该函数为所有响应response的callback函数
    def parse(self, response):
        try:
            self.db_cursor.execute('insert into urls(url) values(?)', (response.url,))
        except:
            pass
        summary = ''
        #格式化响应内容
        resource = Selector(response=response)
        #get title
        temp = resource.xpath('//title/text()').extract()
        if len(temp) > 0:
            summary = temp[0].split(' |')[0]
        try:
            self.db_cursor.execute('update urls set summary=? where url=?', (summary,response.url))
        except:
            pass

        #
        all_href = resource.xpath('//a/@href').extract()

        #construct form url##############所有参数均放在url中
        form_url = []
        for form in resource.xpath('//form').extract():
        	#form action
        	action = Selector(text=form).xpath('.//form/@action').extract()
        	temp = ''
        	#action is not set
        	if len(action)>0:
        		temp = action[0]
        	else:
        		continue
        	#action="#"
        	if temp == '#':
        		temp = ''
        	temp += '?'
        	for p in Selector(text=form).xpath('.//input/@name').extract():
        		temp += p + '=PARAM&'
        	for p in Selector(text=form).xpath('.//button/@name').extract():
        		temp += p + '=PARAM&'
        	
        	temp = temp.rstrip('&')
        	form_url.append(temp)
        #print form_url#########################

        all_hrefs = all_href + form_url
        
        for href in all_hrefs:
            full_url = response.urljoin(href)
            if full_url.find('logout') > -1:
            	continue
            #ignore location.hash
            # if full_url.find('#') > -1:
            #     full_url = full_url.split('#')[0]
            # if full_url.find('?') > -1:
            #     full_url = full_url.split('#')[0]
            try:
                self.db_cursor.execute('insert into urls(url) values(?)', (full_url,))
                
                #keep crawling if not duplicated, with cookies
                yield Request(full_url, meta = {'cookiejar' : response.meta['cookiejar']})
            except:
                pass
                #print 'duplicate'
        self.db_conn.commit()
