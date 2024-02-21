import re
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

def parse_time(string: str, time_ref: datetime.datetime = datetime.datetime.now(datetime.timezone.utc).astimezone()):
    '''
    Parses a string containing a date/time/timedelta.

    Returns
        :class:`datetime`: time relative to the reference time.
        :class:`string`: remaining string.
    '''
    time_dict = {'month': None, 'day': None, 'year': None, 'hour': None, 'minute': None, 'period': None, 'weekday': None}

    # match timedelta
    if match := match_timedelta(string):
        return time_ref + match[0], match[1].replace('\n', ' ').strip()
    
    # match date/time/weekday
    while (match := match_time(string)) or (match := match_date(string)) or (match := match_weekday(string)):
        time_dict.update(match[0])
        string = match[1]

    # if date/time/weekday was matched
    if not all(value == None for value in time_dict.values()):
        if time_dict['weekday'] == 'tmr':
            time_dict['weekday'] = time_ref.weekday() + 1
        date = interpret_time(**time_dict, time_ref=time_ref)
        
    else:
        raise ValueError("Invalid string format.")
    
    return date, string.replace('\n', ' ').strip()

def parse(string: str):
    units = {
        'am': 'am',
        'a':  'am',
        'pm': 'pm',
        'p':  'pm',

        'jan': 1,
        'feb': 2,
        'mar': 3,
        'apr': 4,
        'may': 5,
        'jun': 6,
        'jul': 7,
        'aug': 8,
        'sep': 9,
        'oct': 10,
        'nov': 11,
        'dec': 12,

        'mon': 0,
        'tue': 1,
        'wed': 2,
        'thu': 3,
        'fri': 4,
        'sat': 5,
        'sun': 6,

        'tmr': 'tmr',
        'tom': 'tmr'
    }

    if string == None:
        return string
    elif string.isdigit():
        return int(string)
    else:
        return units[string[:3].lower()]

def match_timedelta(string: str):
    '''
    If timedelta is found at beginning of string:
        return tuple( `timedelta`, `remaining string` )
    Else:
        return `None`
    '''
    timedelta_pattern = r"\s*(?:in\s?)?(\d+\.?\d?)(y|mo|w|d|h|m|s)\s*"

    if re.match(timedelta_pattern, string, flags=re.I):
        delta = timedelta()
        while match := re.match(timedelta_pattern, string, flags=re.I):
            delta += to_timedelta(*match.groups())
            string = string[match.end():]

        return delta, string.replace('\n', ' ').strip()

    else:
        return None


def match_time(string: str):
    '''
    If time is found at beginning of string:
        return tuple( `time_dict`, `remaining string` )
    Else:
        return `None`
    '''
    time_pattern = r"\s*(?:at\s?)?(1[0-2]|[0-9])(?::([0-5][0-9]))?\s?(am|a|pm|p)?\s*"

    if (match := re.match(time_pattern, string, flags=re.I)):
        matched = [parse(m) for m in match.groups()]

        # correct hour
        if matched[0] == 12:
            matched[0] = 0

        time_dict = {i: j for i, j in zip(['hour', 'minute', 'period'], matched)}
        string = string[match.end():]

        return time_dict, string
    
    else:
        return None
    
def match_date(string: str):
    '''
    If date is found at beginning of string:
        return tuple( `time_dict`, `remaining string` )
    Else:
        return `None`
    '''
    date_pattern = r"\s*(?:on\s?)?(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s?(3[0-1]|[0-2]?[0-9])(?:[,\s]*(\d{4}))?\s*"

    if (match := re.match(date_pattern, string, flags=re.I)):
        matched = [parse(m) for m in match.groups()]

        time_dict = {i: j for i, j in zip(['month', 'day', 'year'], matched)}
        string = string[match.end():]

        return time_dict, string
    
    else:
        return None
    
def match_weekday(string: str):
    '''
    If weekday is found at beginning of string:
        return tuple( `time_dict`, `remaining string` )
    Else:
        return `None`
    '''
    weekday_pattern = r"\s*(?:on\s?)?(mon|tue|wed|thu|fri|sat|sun|tmr|tom)[a-z]*\s*"

    if (match := re.match(weekday_pattern, string, flags=re.I)):
        time_dict = {'weekday': parse(match.groups()[0])}
        string = string[match.end():]

        return time_dict, string
    
    else:
        return None
    
def to_timedelta(amount, unit):
    '''
    Returns a :class:`timedelta` | :class:`relativedelta` object.

    Valid units: [ y | mo | w | d | h | m | s]
    '''

    units = {
    's':  'seconds',
    'm':  'minutes',
    'h':  'hours',
    'd':  'days',
    'w':  'weeks',
    'mo': 'months',
    'y':  'years',
    }

    if (unit := units.get(unit.lower())) and (amount := to_float(amount)):
        if unit == 'months':
            return relativedelta(months=+int(amount), days=+int(30*(amount%1)))
        elif unit == 'years':
            return relativedelta(years=+int(amount), days=+int(365*(amount%1)))
        else:
            return timedelta(**dict({unit: amount}))

    else:
        raise ValueError("Invalid unit.")
    
def interpret_time(month: int = None, day: int = None, year: int = None, 
                   hour: int = None, minute: int = None, period: str = None,
                   weekday: int = None, 
                   time_ref: datetime.datetime = datetime.datetime.now(datetime.timezone.utc).astimezone()):
    '''
    Returns the earliest possible date with the given time information.
    
    Date is determined with respect to the refernce time (default: `datetime.datetime.now()`).

    If hour/minute/period is not given, default is 12:00 AM.

    Returns
        :class:`datetime.datetime`: time relative to the reference time.
    '''
    
    loc = locals()
    time_dict = {i: loc[i] for i in ('year', 'month', 'day', 'hour', 'minute')}

    date = midnight(time_ref).replace(**{i: time_dict[i] for i in time_dict if time_dict[i] != None}) + relativedelta(weekday=weekday)

    # apply corrections
    if period == 'am' and date.hour in range(12, 24):
        date -= timedelta(hours=12)
    elif period == 'pm' and date.hour in range(0, 12):
        date += timedelta(hours=12)

    if date <= time_ref:
        if period == None and date + timedelta(hours=12) > time_ref:
            date += timedelta(hours=12)
        elif day == None and date + timedelta(days=1) > time_ref:
            date += timedelta(days=1)
        elif month == None and date + relativedelta(months=+1) > time_ref:
            date += relativedelta(months=+1)
        elif year == None:
            date += relativedelta(years=1)

    return date

def to_float(string):
    '''
    If string is float:
        return `float`
    Else:
        return `None`
    '''
    try:
        return float(string)
    except:
        return None
    
def midnight(time_ref: datetime.datetime = datetime.datetime.now(datetime.timezone.utc).astimezone()):
    '''
    Returns a :class:`datetime.datetime` object with the given time at midnight.
    '''
    return datetime.datetime.combine(time_ref.date(), datetime.time(tzinfo=time_ref.tzinfo))

def time_diff(t1: datetime.time, t2: datetime.time):
    '''
    Returns `t1` - `t2` as a :class:`timedelta`.
    '''
    return datetime.datetime.combine(datetime.date(1,1,1), t1) - datetime.datetime.combine(datetime.date(1,1,1), t2)
    