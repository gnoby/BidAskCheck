import logging
from logging.handlers import RotatingFileHandler

class Quote:
    name: str
    isin: str
    market: str
    bid: float
    ask: float
    quality: str
    def tostring(self):
        result = self.market
        #result += "Q: " +self.quality
        if hasattr(self, 'bid'):
            result +=": Bid: " +str(self.bid)
        if hasattr(self, 'ask'):
            result +=" / Ask:" +str(self.ask)

        return result

def setuplog(config):
    logger = logging.getLogger('pv_charge_logger')
    logger.setLevel(logging.INFO)

    fileHandler = RotatingFileHandler(config.get('bidaskchecker', 'LOG_FILE_NAME'), mode='a', encoding='utf-8',
                                          maxBytes=config.getint('bidaskchecker', 'LOG_FILE_MAX_BYTES'), backupCount=5)

    fileHandler.setLevel(logging.INFO)

    sysHandler = logging.StreamHandler()
    sysHandler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s')

    fileHandler.setFormatter(formatter)
    sysHandler.setFormatter(formatter)

    logger.addHandler(fileHandler)
    logger.addHandler(sysHandler)
    return logger


def formatnumber(number):
    number = round(number, 2)
    return str(number).rjust(8)


def formatmarket(market):
    return market.ljust(10)