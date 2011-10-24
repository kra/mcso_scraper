from scrapy.conf import settings
import json


class McsoPipeline(object):

    def __init__(self):
        self.dir = settings['EXPORT_DIR'] or '.'
        self.encoder = json.JSONEncoder()

    def process_item(self, item, spider):
        filename = '_'.join(
            (item['swisid'],
             item['bookingdate'].replace('/', '_').replace(' ', '_')))
        filename = '/'.join((self.dir, filename))
        item_file = open(filename, 'w')
        item_file.write(self.encoder.encode(dict(item.items())) + '\n')
        item_file.close
        return item
