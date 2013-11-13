import common

from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request, FormRequest
from scrapy.conf import settings
import scrapy.log
import scrapy.item

import socket
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
        """ Log, and send mail on error log. """
        # XXX this doesn't cover pipeline logs or any other logging outside
        #     of these objects.  We really want either scrapy.log.err() or
        #     twisted.python.log.err() to be listening.
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
        "http://www.mcso.us/PAID"
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
        if url.startswith('/'):
            path = url
        else:
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
            form_data['SearchType'] = '3'
        else:
            raise NotImplementedError # could implement other options
        return [
            FormRequest.from_response(
                response, callback=self.parse_inmates, formdata=form_data)]

    def parse_inmates(self, response):
        """ Parse the response to our POST to get the inmates page."""
        hxs = HtmlXPathSelector(response)
        inmate_urls = hxs.select(
            '//a[contains(@href, "/PAID/Home/Booking")]/@href').extract()
        return [
            Request(self.absolute_url(response, inmate_url),
                    callback=self.parse_inmate)
            for inmate_url in inmate_urls]

    def parse_inmate(self, response):
        """ Parse the response to our GET of an inmate page. """
        # XXX q&d throttling, there should be a smarter way
        import time; time.sleep(1)

        inmate_item = InmateItem()
        inmate_item['url'] = response.url
        hxs = HtmlXPathSelector(response)

        # XXX mugshot is loaded with javascript, so just get the known URL
        # this is the low-res version, high-res needs auth
        mugshot_url = response.url.replace('Booking', 'MugshotImage')
        inmate_item['mugshot_url'] = mugshot_url
        inmate_item['mugshot'] = self.download_image(mugshot_url)

        def booking_key(key):
            """ Return the item key corresponding to the given text label """
            key = key.lower().replace('person_', '')
            return {
                'fullname':'name',
                'bookingdatetime':'bookingdate',
                'haircolor':'hair',
                'eyecolor':'eyes',
                'assignedfacility':'assignedfac',
                'projectedreleasedatetime':'projreldate',
                'releasedatetime':'releasedate'
                }.get(key, key)

        for field in hxs.select(
            '//*[@class="booking-information"]').select('dt'):
            key = booking_key(field.select('label/@for')[0].extract())
            value = field.select('following-sibling::dd[1]/text()')[0].extract()
            try:
                inmate_item[key] = value
            except KeyError:
                self.log(
                    'got unexpected key %s at %s' % (key, response.url),
                    level=scrapy.log.ERROR)

        try:
            (case_table,) = hxs.select('//div[@id="charge-info"]')
        except ValueError:
            # recent bookings are not always complete
            # this might be better handled by the pipeline validator
            # XXX should we fail the item so the stats reflect it?
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
        inmate_item['cases'] = []
        def header_extract(case_elt, name):
            """ Return a value from a court case header. """
            case_elt = case_elt.select(
                './descendant::*[@class="%s"]' % name)[0]
            return case_elt.select('./b/text()')[0].extract()
        def body_extract(body_elt):
            """ Return a value from a court case body. """
            def value_extract(elt, name):
                return elt.select(
                    './descendant::*[@class="%s"]/text()' % name)[0].extract()
            for charge in body_elt.select('ol/li'):
                charge_item = ChargeItem()
                charge_item['charge'] = value_extract(
                    charge, 'charge-description-display')
                charge_item['bail'] = value_extract(charge, 'charge-bail-value')
                charge_item['status'] = value_extract(
                    charge, 'charge-status-value')
                yield charge_item
        for case_header in case_table.select('./descendant::h3'):
            case_item = CaseItem()
            case_item['court_case_number'] = header_extract(
                case_header, 'court-case-number')
            case_item['da_case_number'] = header_extract(
                case_header, 'da-case-number')
            case_item['citation_number'] = header_extract(
                case_header, 'citation-number')
            case_body = case_header.select('following-sibling::*')[0]
            case_item['charges'] = [
                charge for charge in body_extract(case_body)]
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
