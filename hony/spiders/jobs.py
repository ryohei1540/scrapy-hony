# -*- coding: utf-8 -*-
from scrapy import Spider
from scrapy import Request
from scrapy.selector import Selector

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from datetime import datetime
import re


class JobsSpider(Spider):
    name = 'jobs'
    allowed_domains = ['humansofnewyork.com']
    start_urls = ['http://www.humansofnewyork.com/archive/']

    def parse(self, response):
        # Second argument is for calculating the current year
        for target_year in range(2009, int(datetime.now().strftime("%Y")) + 1, 1):
            target_ym = "\"year_" + str(target_year) + "\""
            months_path = '//section[@id={0}]/nav[@class="months"]/ul/li'.format(
                target_ym)
            targets = response.xpath(months_path)
            for target_month in targets:
                if target_month.xpath('a/text()').extract_first():
                    relative_target_page_url = target_month.xpath(
                        'a/@href').extract_first()
                    absolute_target_page_url = response.urljoin(
                        relative_target_page_url)
                    yield Request(absolute_target_page_url, callback=self.parse_list)

    def parse_list(self, response):
        target_date = re.search(r'2.*', response.url).group()
        if len(target_date) == 6:
            actual_target_date = target_date.replace('/', '0')
        else:
            actual_target_date = target_date.replace('/', '')
        tmp_string = '//section[@id="posts_{0}"]/div[contains(@class, "post_micro")]'.format(
            actual_target_date)
        targets = response.xpath(tmp_string)
        for target in targets:
            absolute_url = target.xpath(
                'div[@class="post_glass post_micro_glass_w_controls post_micro_glass"]/a[@class="hover"]/@href').extract_first()
            published_date = target.xpath(
                'div[@class="post_glass post_micro_glass_w_controls post_micro_glass"]/a[@class="hover"]/div[@class="hover_inner"]/span[@class="post_date"]/text()').extract_first().strip()
            notes = target.xpath(
                'div[@class="post_glass post_micro_glass_w_controls post_micro_glass"]/a[@class="hover"]/div[@class="hover_inner"]/span[@class="post_notes"]/text()').extract_first().strip()
            image_url = target.xpath(
                'div[@class="post_content"]/div[@class="post_content_inner"]/div[@class="post_thumbnail_container has_imageurl"]/@data-imageurl').extract_first()
            yield Request(absolute_url, callback=self.parse_page, meta={'Absolute_url': absolute_url, 'Image_url': image_url, 'Published_date': published_date, 'Notes': notes})

    def parse_page(self, response):
        absolute_url = response.meta.get('Absolute_url')
        image_url = response.meta.get('Image_url')
        published_date = response.meta.get('Published_date')
        notes = response.meta.get('Notes')

        options = Options()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        self.driver = webdriver.Chrome(chrome_options=options)
        self.driver.get(absolute_url)

        sel = Selector(text=self.driver.page_source)
        content = sel.xpath(
            '//div[@class="post-page-post"]/div[@class="post-text"]/p/text()').extract_first()
        word = ""
        if (content is None):
            content = ""
        else:
            content.strip()
            word = self.split_content(content)
        if (image_url is None):
            image_url = ""

        yield {
            'published_date': published_date,
            'notes': notes,
            'content': content,
            'word': word,
            'url': absolute_url,
            'image_url': image_url}

    def replace_special_character(self, string, substitutions):
        substrings = sorted(substitutions, key=len, reverse=True)
        regex = re.compile('|'.join(map(re.escape, substrings)))
        return regex.sub(lambda match: substitutions[match.group(0)], string)

    def split_content(self, content):
        lower_content = content.lower()
        removed_sign = re.sub(re.compile(
            "[\’\–\…\‘\‚\“\„\.,?!-/:-@[-`{-~]"), '', lower_content)
        substitutions = {"ā": "a", "é": "e", "ī": "i", "ō": "o", "ū": "u"}
        replaced_special_character = self.replace_special_character(
            removed_sign, substitutions)
        splited_content = replaced_special_character.split()
        return splited_content
