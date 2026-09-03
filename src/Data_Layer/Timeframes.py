timeframes = {'M1': [1440,1,'M1_db.db'],
               'M5': [288,5,'M5_db.db'],
               'M15': [96,15,'M15_db.db'],
               'M30': [48,30,'M30_db.db'],
              'H1': [24,16385,'H1_db.db'],
            }

class Timeframe:
    def __init__(self, timeframe):
        self.bars = timeframes[timeframe][0]
        self.id = timeframes[timeframe][1]
        self.db_name = timeframes[timeframe][2]
        self.frame = timeframe

    def bars(self):
        return self.bars

    def id(self):
        return self.id

    def db_name(self):
        return self.db_name

    def frame(self):
        return self.frame
