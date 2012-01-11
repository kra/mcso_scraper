from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.item import Item, Field
from scrapy.http import Request, FormRequest

from lxml import etree
import urllib, urlparse
import StringIO
import logging


class InmateItem(Item):
    url = Field()
    mugshot = Field()
    swisid = Field()
    name = Field()
    age = Field()
    gender = Field()
    race = Field()
    height = Field()
    weight = Field()
    hair = Field()
    eyes = Field()
    arrestingagency = Field()
    arrestdate = Field()
    bookingdate = Field()
    currentstatus = Field()
    assignedfac = Field()
    projreldate = Field()
    cases = Field()
    releasedate = Field()
    releasereason = Field()

class CaseItem(Item):
    court_case_number = Field()
    da_case_number = Field()
    citation_number = Field()
    charges = Field()


class ChargeItem(Item):
   charge = Field()
   bail = Field()
   status = Field()


class McsoSpider(BaseSpider):
    name = "mcso"
    #allowed_domains = ["www.mcso.us"]
    start_urls = [
        "http://www.mcso.us/PAID/Default.aspx"
        ]

    def absolute_url(self, response, url):
        """ Return an absolute url for given relative url and response """
        # sigh, not a named tuple
        (scheme, netloc, path, params, _, _) = urlparse.urlparse(response.url)
        # lop off end of current path, add url
        path = '/'.join(path.split('/')[:-1])
        path = '/'.join((path, url))
        return urlparse.urlunparse((scheme, netloc, path, params, '', ''))

    def parse(self, response):
        """ Parse the response to our start urls. """
        # XXX we probably want to select 'last 7 days' or something
        # XXX select yesterday's bookings, very recent bookings are not always
        #     complete
        return [
            FormRequest.from_response(response, callback=self.parse_inmates)]

    def parse_inmates(self, response):
        """ Parse the response to our POST to get the inmates page."""
        # XXX report on number of inmates found so we can verify scrapingness
        hxs = HtmlXPathSelector(response)
        inmate_urls = hxs.select(
            '//a[contains(@href, "BookingDetail.aspx")]/@href').extract()
        return [
            Request(self.absolute_url(response, inmate_url),
                    callback=self.parse_inmate)
            for inmate_url in inmate_urls][0:5]

    def parse_inmate(self, response):
        """ Parse the response to our GET of an inmate page. """
        inmate_item = InmateItem()
        inmate_item['url'] = response.url
        hxs = HtmlXPathSelector(response)

        mugshot_url = self.absolute_url(response, hxs.select(
            '//img[@id="ctl00_MainContent_mugShotImage"]/@src')[0].extract())
        inmate_item['mugshot'] = self.download_image(mugshot_url)

        for field in hxs.select(
            '//span[contains(@id, "ctl00_MainContent_label")]'):
            key = field.select('@id').extract()[0]
            key = key[len('ctl00_MainContent_label'):]
            try:
                value = field.select('text()').extract()[0]
            except IndexError:
                value = None
            # XXX rescue and log if key isn't expected rather than fail
            inmate_item[key.lower()] = value

        try:
            (case_table,) = hxs.select(
                '//table[@id="ctl00_MainContent_CaseDataList"]')
        except ValueError:
            # recent bookings are not always complete
            # this might be better handled by the pipeline validator
            logging.warning('incomplete page, try again later')
            return
        # XXX can't get scrapy's xpath to do me
        # XXX should switch earlier
        # XXX my paths are probably just wrong - start with . to anchor
        inmate_item['cases'] = []
        case_table = etree.fromstring(case_table.extract())
        # cases are tables in tds of case table
        for case in case_table.xpath('/table/tr/td/table'):
           case_item = CaseItem()
           (court_case_number, da_case_number, citation_number) = [
              elt.xpath('text()')[0]
              for elt in case.xpath(
                  './/span[contains(@id, "ctl00_MainContent_CaseDataList")]')
              if elt.xpath('@class="Data"')]
           case_item['court_case_number'] = court_case_number
           case_item['da_case_number'] = da_case_number
           case_item['citation_number'] = citation_number
           case_item['charges'] = []
           for charge_row in [
              row for row in case.xpath(
                  './/tr[@class="GridItem"]|.//tr[@class="GridAltItem"]')]:
              charge_item = ChargeItem()
              (charge, bail, status) = [
                 elt.xpath('text()')[0] for elt in charge_row.xpath('td')]
              charge_item['charge'] = charge
              charge_item['bail'] = bail
              charge_item['status'] = status
              case_item['charges'].append(charge_item)
           inmate_item['cases'].append(case_item)
        return inmate_item

    # XXX we should do this async
    def download_image(self, image_url):
        """
        Download image at image_url and return a stringio with contents
        """
        io = StringIO.StringIO()
        image = urllib.urlopen(image_url)
        while True:
            buf = image.read(65536)
            if len(buf) == 0:
                break
            io.write(buf)
        image.close()
        return io
