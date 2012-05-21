import common

from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request, FormRequest
from scrapy.conf import settings
import scrapy.log
import scrapy.item

import socket
from lxml import etree
import urllib, urlparse
import StringIO

# XXX only split out so we don't have to instantiate an item to get it
def booking_mugshot_dir(booking_id):
    """ return the mugshot path for booking_id relative to the data dir """
    booking_id = int(booking_id)
    # mugshot files are partitioned by 2 1-char suffix subdirs
    ones_digit = str(booking_id % 10)
    tens_digit = str((booking_id % 100) / 10)
    return '/'.join((ones_digit, tens_digit))


class ScrapyBase(object):
    def log(self, msg, level):
        super(ScrapyBase, self).log(msg, level)
        if level == scrapy.log.ERROR:
            common.log.send_mail(
                msg,
                'mcso notification from %s: %s' %
                (socket.gethostname(), msg[0:50]))


class Item(ScrapyBase, scrapy.item.Item):
    pass


class InmateItem(Item):
    url = scrapy.item.Field()
    mugshot = scrapy.item.Field()
    mugshot_url = scrapy.item.Field()
    swisid = scrapy.item.Field()
    name = scrapy.item.Field()
    age = scrapy.item.Field()
    gender = scrapy.item.Field()
    race = scrapy.item.Field()
    height = scrapy.item.Field()
    weight = scrapy.item.Field()
    hair = scrapy.item.Field()
    eyes = scrapy.item.Field()
    arrestingagency = scrapy.item.Field()
    arrestdate = scrapy.item.Field()
    #parsed_arrestdate = scrapy.item.Field()
    bookingdate = scrapy.item.Field()
    #parsed_bookingdate = scrapy.item.Field()
    currentstatus = scrapy.item.Field()
    assignedfac = scrapy.item.Field()
    projreldate = scrapy.item.Field()
    #parsed_reldate = scrapy.item.Field()
    cases = scrapy.item.Field()
    releasedate = scrapy.item.Field()
    #parsed_releasedate = scrapy.item.Field()
    releasereason = scrapy.item.Field()
    booking_id = scrapy.item.Field()

    def validate(self):
        for key in ('swisid', 'bookingdate'):
            try:
                _ = self[key]
            except KeyError:
                raise Exception('missing required key %s' % key)

    #XXX properties
    def parsed_date(self, field):
        """
        Return a sortable date string from the given string in the format
        used by mcso, or None.
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
            self.log(
                'could not split date %s: %s' % (field, exc),
                level=scrapy.log.ERROR)
            return None

    def mugshot_path(self):
        """ return my mugshot path relative to the data dir """
        return '/'.join(
            (booking_mugshot_dir(str(self['booking_id'])),
             str(self['booking_id'])))


class CaseItem(Item):
    court_case_number = scrapy.item.Field()
    da_case_number = scrapy.item.Field()
    citation_number = scrapy.item.Field()
    charges = scrapy.item.Field()


class ChargeItem(Item):
    charge = scrapy.item.Field()
    bail = scrapy.item.Field()
    status = scrapy.item.Field()

    #XXX properties
    def parsed_bail(self, field):
        """
        Return a sortable bail string from the given string in the format
        used by mcso, or None.
        """
        # keep as a string for sqlite's numeric affinity
        # might want to try/fail if the outcome isn't intable to notice bad
        # data; OTOH bad formatted data might still be useful
        if field is None:
            return None
        return field.replace('$', '').replace(',', '')


class McsoSpider(ScrapyBase, BaseSpider):
    IN_CUSTODY = 'IN_CUSTODY'
    LAST_7_DAYS = 'LAST_7_DAYS'
    name = "mcso"
    #allowed_domains = ["www.mcso.us"]
    start_urls = [
        "http://www.mcso.us/PAID/Default.aspx"
        ]

    def __init__(self, *args, **kwargs):
        self.booking_form_field = settings['BOOKINGS_TO_DOWNLOAD']
        if self.booking_form_field not in (
            self.IN_CUSTODY, self.LAST_7_DAYS):
            raise Exception(
                'unknown BOOKINGS_TO_DOWNLOAD value %s' %
                self.booking_form_field)
        super(McsoSpider, self).__init__(*args, **kwargs)

    def absolute_url(self, response, url):
        """ Return an absolute url for given relative url and response """
        (scheme, netloc, path, params, _, _) = urlparse.urlparse(response.url)
        # lop off end of current path, add url
        path = '/'.join(path.split('/')[:-1])
        path = '/'.join((path, url))
        return urlparse.urlunparse((scheme, netloc, path, params, '', ''))

    def parse(self, response):
        """ Parse the response to our start urls. """
        form_data = {}
        if self.booking_form_field == self.LAST_7_DAYS:
            self.log(
                'Spidering bookings from the last 7 days',
                level=scrapy.log.INFO)
            form_data['ctl00$MainContent$PAIDBookingSearch$ddlSearchType'] = '3'
        return [
            FormRequest.from_response(
                response, callback=self.parse_inmates, formdata=form_data)]

    def parse_inmates(self, response):
        """ Parse the response to our POST to get the inmates page."""
        hxs = HtmlXPathSelector(response)
        inmate_urls = hxs.select(
            '//a[contains(@href, "BookingDetail.aspx")]/@href').extract()
        return [
            Request(self.absolute_url(response, inmate_url),
                    callback=self.parse_inmate)
            for inmate_url in inmate_urls]

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
            try:
                inmate_item[key.lower()] = value
            except KeyError:
                self.log(
                    'got unexpected key %s at %s' % (key, response.url),
                    level=scrapy.log.ERROR)
        try:
            (case_table,) = hxs.select(
                '//table[@id="ctl00_MainContent_CaseDataList"]')
        except ValueError:
            # recent bookings are not always complete
            # this might be better handled by the pipeline validator
            self.log('incomplete page %s, try again later' % response.url,
                     level=scrapy.log.WARNING)
            # XXX raising the Twisted TimeoutError should make the retryer
            #     retry it, but isn't?  Otherwise, return a Request, but
            #     dups aren't being retried?  Workaround, just scrape more.
            #raise UserTimeoutError
            #return Request(
            #   response.url,
            #    meta={'attempts':response.meta.get('attempts', 0) + 1},
            #    callback=self.parse_inmate)
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
