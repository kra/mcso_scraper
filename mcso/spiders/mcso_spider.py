from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.item import Item, Field
from scrapy.http import Request, FormRequest

from lxml import etree
import urllib, urlparse
import StringIO
import logging

# XXX only split out so we don't have to instantiate an item to get it
def booking_mugshot_dir(booking_id):
    """ return the mugshot path for booking_id relative to the data dir """
    booking_id = int(booking_id)
    # mugshot files are partitioned by 2 1-char suffix subdirs
    ones_digit = str(booking_id % 10)
    tens_digit = str((booking_id % 100) / 10)
    return '/'.join((ones_digit, tens_digit))


class InmateItem(Item):
    url = Field()
    mugshot = Field()
    mugshot_url = Field()
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
    #parsed_arrestdate = Field()
    bookingdate = Field()
    #parsed_bookingdate = Field()
    currentstatus = Field()
    assignedfac = Field()
    projreldate = Field()
    #parsed_reldate = Field()
    cases = Field()
    releasedate = Field()
    #parsed_releasedate = Field()
    releasereason = Field()
    booking_id = Field()

    #XXX properties
    def parsed_date(self, field):
        """
        Return a sortable date string from the given string in the format
        used by mcso.
        """
        if field is None or field == 'Unknown':
            return None
        # 11/13/2011 12:29 AM -> 2012-01-11 07:14:11
        try:
            field = field.strip()
            try:
                (date, time) = field.split(None, 1)
            except:
                date = field
                hour = 0
                min = 0
            else:
                (time, ampm) = time.split()
                (hour, min) = time.split(':')
                hour = int(hour)
                min = int(min)
                if ampm == 'PM':
                    hour += 12
            (month, day, year) = date.split('/')
            month = int(month)
            day = int(day)
            return '%s-%02d-%02d %02d:%02d:00' % (year, month, day, hour, min)
        except Exception as exc:
            logging.warning('could not split date %s: %s' % (field, exc))
            return None

    def mugshot_path(self):
        """ return my mugshot path relative to the data dir """
        return '/'.join(
            (booking_mugshot_dir(str(self['booking_id'])),
             str(self['booking_id'])))


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
        (scheme, netloc, path, params, _, _) = urlparse.urlparse(response.url)
        # lop off end of current path, add url
        path = '/'.join(path.split('/')[:-1])
        path = '/'.join((path, url))
        return urlparse.urlunparse((scheme, netloc, path, params, '', ''))

    def parse(self, response):
        """ Parse the response to our start urls. """
        # XXX we may want to select 'last 7 days' or something
        return [
            FormRequest.from_response(response, callback=self.parse_inmates)]

    def parse_inmates(self, response):
        """ Parse the response to our POST to get the inmates page."""
        # XXX report on number of bookings found so we can verify scrapingness
        hxs = HtmlXPathSelector(response)
        inmate_urls = hxs.select(
            '//a[contains(@href, "BookingDetail.aspx")]/@href').extract()
        return [
            Request(self.absolute_url(response, inmate_url),
                    callback=self.parse_inmate)
            for inmate_url in inmate_urls][0:10]# XXX testing

    def parse_inmate(self, response):
        """ Parse the response to our GET of an inmate page. """
        inmate_item = InmateItem()
        inmate_item['url'] = response.url
        hxs = HtmlXPathSelector(response)

        mugshot_url = self.absolute_url(response, hxs.select(
            '//img[@id="ctl00_MainContent_mugShotImage"]/@src')[0].extract())
        inmate_item['mugshot_url'] = mugshot_url
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
