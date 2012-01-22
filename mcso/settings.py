BOT_NAME = 'mcso'
BOT_VERSION = '1.0'

LOG_LEVEL = 'INFO'
SPIDER_MODULES = ['mcso.spiders']
NEWSPIDER_MODULE = 'mcso.spiders'
DEFAULT_ITEM_CLASS = 'mcso.items.McsoItem'
ITEM_PIPELINES = ['mcso.pipelines.McsoPipeline']
# asp will forbid form submission unless we spoof a human user-agent
USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_5_8) AppleWebKit/535.1 (KHTML, like Gecko) Chrome/13.0.782.220 Safari/535.1'
DATA_DIRNAME = '../data'
SQLITE_FILENAME = '/'.join([DATA_DIRNAME, 'db'])
MUGSHOT_DIRNAME = '/'.join([DATA_DIRNAME, 'mugshots'])
