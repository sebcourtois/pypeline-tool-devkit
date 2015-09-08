

from datetime import datetime, timedelta
from pytd.util.external import ntplib

import time, calendar

cli = ntplib.NTPClient()
res = cli.request("pool.ntp.org", version=3)

utcDelta = timedelta(seconds=int(res.offset))
utcNow = datetime.utcnow()
print "SYS utc:", utcNow.isoformat()
print "FIX utc:", (utcNow + utcDelta).isoformat(), utcDelta.total_seconds()

utcTime = datetime.utcfromtimestamp(int(res.tx_time))
print 'NTP utc:', utcTime.isoformat()

locTime = datetime.fromtimestamp(int(res.tx_time))
print 'NTP loc:', locTime.isoformat()

print "loc to utc:", datetime.utcfromtimestamp(time.mktime(locTime.timetuple())).isoformat()
print "utc to utc:", datetime.utcfromtimestamp(calendar.timegm(utcTime.timetuple())).isoformat()


