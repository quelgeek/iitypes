import pyngres as py
import sys
import ctypes
import struct
import decimal
import math
import datetime as dt
import uuid as uu
import ipaddress as ip
import codecs
from multipledispatch import dispatch


package_name = __name__


class NULL():
    pass


class NOTNULL():
    pass


class WITHNULL():
    pass


##  OpenAPI envHandle 
_envHandle = None


def publish_envHandle(in_envHandle=None):
    '''make the OpenAPI envHandle globally available'''

    ##  if the caller has the in_envHandle for some reason they can 
    ##  supply it as an argument, otherwise we will attempt to get 
    ##  the handle using the latest OpenAPI version
    
    global _envHandle

    ##  silently ignore a change to _envHandle when it is already set
    if _envHandle:
        return
    
    if not in_envHandle:
        ##  initialize the OpenAPI to get the in_envHandle;
        ##  there is no way to know which level the local OpenAPI DLL
        ##  supports, so start with the defined latest level (IIAPI_VERSION)
        ##  and fall back a level at a time until we succeed
        inp = py.IIAPI_INITPARM()
        for in_version in range(py.IIAPI_VERSION, 0, -1):
            inp.in_version = in_version
            py.IIapi_initialize( inp )
            if inp.in_status == py.IIAPI_ST_SUCCESS:
                in_envHandle = inp.in_envHandle
                break

    if not in_envHandle:
        raise RuntimeError("can't initialize OpenAPI")

    _envHandle = in_envHandle


def get_envHandle():
    '''return the current envHandle'''

    global _envHandle
    return _envHandle


def Buffer_Factory(fields):
    class Factory(ctypes.Structure):
        _fields_ = fields
    return Factory


def format(src, dst):
    '''convert Ingres src value using IIapi_formatData()'''

    global _envHandle
    if not _envHandle:
        raise RuntimeError('_envHandle not set; call publish_envHandle()')

    fdp = py.IIAPI_FORMATPARM()
    fdp.fd_envHandle = _envHandle

    fdp.fd_srcDesc = src.descriptor
    fdp.fd_srcDesc.ds_columnType = py.IIAPI_COL_QPARM
    fdp.fd_srcValue = src.datavalue

    fdp.fd_dstDesc = dst.descriptor
    fdp.fd_dstDesc.ds_columnType = py.IIAPI_COL_QPARM
    fdp.fd_dstValue = dst.datavalue

    py.IIapi_formatData(fdp)    
    if fdp.fd_status >= py.IIAPI_ST_ERROR:
        raise ValueError('type conversion failed')


def CURRENT_DATE():
    '''return ANSI formatted date (taken from the machine executing this)'''

    current_date = dt.date.today().strftime('%Y-%m-%d')
    return current_date


def CURRENT_TIME():
    '''return ANSI formatted time (taken from the machine executing this)'''

    ##  timezone-aware
    now = dt.datetime.now().astimezone()
    current_time = now.strftime('%H:%m:%S.%f%:z')
    return current_time


def CURRENT_TIMESTAMP():
    '''return ANSI formatted timestamp (taken from the machine executing this)'''

    ##  timezone-aware
    current_date = CURRENT_DATE()
    current_time = CURRENT_TIME()
    current_timestamp = current_date + ' ' + current_time
    return current_timestamp


def LOCAL_TIME():
    '''return ANSI formatted time (taken from the machine executing this)'''

    ##  timezone-naive
    now = dt.datetime.now()
    local_time = now.strftime('%H:%m:%S.%f')
    return local_time


def LOCAL_TIMESTAMP():
    '''return ANSI formatted timestamp (taken from the machine executing this)'''

    ##  timezone-naive
    current_date = CURRENT_DATE()
    local_time = LOCAL_TIME()
    local_timestamp = current_date + ' ' + local_time
    return local_timestamp


def TIMESTAMP_UNIX():
    '''return Unix ticks (taken from the machine executing this)'''

    ticks = int(dt.datetime.now(dt.UTC).timestamp())
    return ticks


##  -----------------------------  IIAPI_TYPE  ---------------------------------


class IIAPI_TYPE():
    '''base class for Ingres data containers'''

    descriptor = None
    datavalue = None
    _null_semantics = NOTNULL
    _ds_dataType = None         ##  datatype code, overridden by subclass
    _ds_length = None           ##  declared size, overridden by subclass
    _buffer = None              ##  actual data buffer


    def __init__(self,*args,**kwargs):

        ##  NB calling IIapi_close() releases/invalidates descriptors
        ##  that were allocated by the OpenAPI. If the caller has a
        ##  descriptor allocated by the OpenAPI the caller needs to 
        ##  clone it and pass the clone

        ##  instantiating an Ingres data object using a descriptor 
        ##  implies it will be used as a data buffer for a SELECT 
        ##  statement and hence no initial value needs to be supplied

        ##  pick up any keyword arguments
        try:
            descriptor = kwargs['descriptor']
        except KeyError:
            descriptor = None
        try:
            null_semantics = kwargs['nullable']
            if null_semantics not in {NOTNULL,WITHNULL}:
                raise ValueError(
                    'must be NOTNULL or WITHNULL')
        except KeyError:
            null_semantics = NOTNULL
        try:
            name = kwargs['name'].encode()
        except KeyError:
            name = None

        ##  remember null semantics
        self._null_semantics = null_semantics

        ##  disallow positional arguments when descriptor= is used
        argc = len(args)
        positionals = (argc > 0)
        if descriptor and positionals:
            raise RuntimeError('positional argument(s) with descriptor=')

        ##  when there is no descriptor an initial value is mandatory
        if not descriptor and not positionals:
            raise RuntimeError('no initial value')

        ##  if no descriptor was supplied then construct one
        if not descriptor:
            descriptor = py.IIAPI_DESCRIPTOR()
            descriptor.ds_dataType = self._ds_dataType
            if null_semantics is NOTNULL:
                descriptor.ds_nullable = False
            else:
                descriptor.ds_nullable = True
            descriptor.ds_length = self._get_ds_length(*args)
            descriptor.ds_precision = self._get_ds_precision(*args)
            descriptor.ds_scale = self._get_ds_scale (*args)
            descriptor.ds_columnType = 0
            descriptor.ds_columnName = name

        ##  expose the descriptor 
        self.descriptor = descriptor

        ##  set the SQL type declaration
        self.SQL_declaration = self._SQL_declaration()

        ##  check size is within limits
        self._validate_size()

        ##  allocate any required conversion buffers
        self._allocate_conversion_buffers()

        ##  allocate the data buffer and construct the IIAPI_DATAVALUE()
        datavalue = py.IIAPI_DATAVALUE()      
        self._buffer = self._allocate_buffer()
        datavalue.dv_length = self._get_dv_length()
        datavalue.dv_value = ctypes.addressof(self._buffer)

        ##  expose the datavalue
        self.datavalue = datavalue
        
        if positionals:
            self._validate_positionals(*args)
            ##  an initial value was supplied
            value = self._get_initial_value(*args)
            self._set(value)

   
    def _allocate_conversion_buffers(self):
        '''create buffers for use with IIapi_formatdata()'''
        pass


    def _validate_size(self):
        '''ensure size is within limits'''

        ##  overridden by IIAPI_TYPE_WITH_LIMITED_SIZE
        pass
        

    def _validate_positionals(self,*args):
        if len(args) > self._expected_positionals:
            raise RuntimeError('too many arguments')
    
        
    def _get_initial_value(self,*args):
        try:
            value = args[0]
        except IndexError:
            raise RuntimeError('no initial value')
        return value


    def _get_ds_length(self,*args):
        raise NotImplementedError


    def _get_dv_length(self):
        dv_length = ctypes.sizeof(self._buffer)
        return dv_length

    
    def _get_ds_precision(self,*args):
        return 0


    def _get_ds_scale(self,*args):
        return 0


    def _SQL_declaration(self):
        '''return the human-readable SQL type declaration'''
        ##  e.g. 'VARCHAR(100)'
        raise NotImplementedError


    def _allocate_buffer(self):
        '''allocate a sufficiently big data buffer'''
        raise NotImplementedError


    def _clear_buffer(self):
        address = self.datavalue.dv_value
        length = ctypes.sizeof(self._buffer)
        ctypes.memset(address, 0x00, length)


    def _set_null(self):
        if self._null_semantics is NOTNULL:
            raise ValueError('not nullable')
        self.datavalue.dv_null = True
        self.datavalue.dv_value = None


    def _set_value(self,v):
        self.datavalue.dv_null = False
        self.datavalue.dv_value = ctypes.addressof(self._buffer)
        self._value_setter(v)


    def _value_setter(self,v):
        raise NotImplementedError


    def _get_python_value(self):
        raise NotImplementedError


    def formatted(self):
        raise NotImplementedError


    @property
    def name(self):
        '''return the column name (if any)'''

        name = self.descriptor.ds_columnName
        if name:
            name = name.decode()
        else:
            name = ''
        return name


    @property
    def address(self):
        '''return buffer address'''

        return ctypes.addressof(self._buffer)


    @property
    def value(self):
        '''return Ingres data as Python value'''
    
        if self.datavalue.dv_null:
            v = None
        else:
            v = self._get_python_value()
        return v


    def _set(self,v):
        if v is NULL or v is None: 
            self._set_null()
        else:
            self._set_value(v)


    @value.setter
    def value(self,v):
        '''initialize the Ingres data type instance'''
    
        self._set(v)


    @property
    def name(self):
        '''return the name of the Ingres value'''
        try:
            name = self.descriptor.ds_columnName.decode()
        except AttributeError:
            name = None
        return name


    def __str__(self): 
        '''return a human-readable representation of the *Python* value'''

        ##  note: use self.formatted() to get a human-readable 
        ##  representation of the *Ingres* value

        v = self.value
        s = str(v)
        return s


    def __repr__(self):
        raise NotImplementedError


    def _reprfy_value(self):
        raise NotImplementedError


    def _reprfy_nullability(self):
        '''return ",nullable=ingtypes.WITHNULL" if instance is nullable'''

        if self._null_semantics == WITHNULL:
            modifier = f',nullable={package_name}.WITHNULL'
        else:
            modifier = ''
        return modifier 


    def _peek(self):
        '''return a hex dump of the Ingres value buffer'''
        
        if not self.datavalue.dv_null:
            r = bytes(self._buffer).hex()
        else:
            r = bytes(b'').hex()
        return r


    def _poke(self,s):
        '''poke bytes into the buffer'''

        ##  intended only for testing/debugging 
        ##  e.g. i._poke('0x050062797465730000000000') or
        ##  i._poke('E7070803E1ED0000D08058293C00')

        ##  the burden of constructing a valid bytes argument is 
        ##  entirely on the user. If it is a complex object then consider
        ##  using the struct class to build it

        if type(s) is str:
            ##  clip off any leading '0x'
            if s.lower().startswith('0x'):
                s = s[2:]
            ##  convert to bytes
            b = bytes.fromhex(s)
        elif type(s) is bytes:
            b = s
        else:
            raise ValueError('must be bytes or str')

        ##  poke; overrun is prevented but underrun is not
        self._clear_buffer()
        length = ctypes.sizeof(self._buffer)
        dv_value = self.datavalue.dv_value
        ctypes.memmove(dv_value, b, length)


##  ------------------  IIAPI_TYPE_WITH_INTRINSIC_SIZE  ------------------------


class IIAPI_TYPE_WITH_INTRINSIC_SIZE(IIAPI_TYPE):
    ##  ANSIdate
    ##  Boolean
    ##  Ingresdate
    ##  Interval_YM
    ##  IPv4
    ##  IPv6
    ##  Money
    ##  Object_Key
    ##  Table_Key
    ##  UUID


    ##  these types take a single positional argument (value)
    _expected_positionals = 1


    def __repr__(self):
        classname = type(self).__qualname__
        value = self._reprfy_value()
        modifier = self._reprfy_nullability()
        r = f'{package_name}.{classname}({value}{modifier})'
        return r


    def _get_ds_length(self,*args):
        ##  the subclass will have overridden self._ds_length so just use it
        return self._ds_length


class IIAPI_DATE_TYPE(IIAPI_TYPE_WITH_INTRINSIC_SIZE):
    '''Ingres ANSIDATE'''

    
    _ds_dataType = py.IIAPI_DATE_TYPE
    _ds_length = py.IIAPI_DATE_LEN


    def _SQL_declaration(self):
        return 'ANSIDATE'


    def _allocate_conversion_buffers(self):
        '''preallocate conversion buffers'''
        self._conv_target = Char('',10)


    class ANSIdate(ctypes.Structure):
        ##  (see typedef struct _AD_ADATE in 
        ##  ..\main\src\common\hdr\hdr\adudate.h)
        _fields_ = [
            ('year',ctypes.c_short),
            ('month',ctypes.c_ubyte),
            ('day',ctypes.c_ubyte) ]


    def _allocate_buffer(self):
    
        class BUFFER(ctypes.Union):
            _fields_ = [
                ('fields',self.ANSIdate),
                ('value',ctypes.c_ubyte * py.IIAPI_DATE_LEN) ]


        buffer = BUFFER()
        return buffer


    def _reprfy_value(self):
        if self.datavalue.dv_null:
            ansi_date = f'{package_name}.NULL'
        else:
            ansi_date = self.formatted()
        return f"'{ansi_date}'"


    def formatted(self):
        '''return natively formatted ANSIdate'''

        ##  require up to 10 character for Ingresdate
        format(self, self._conv_target)
        d = self._conv_target.value.strip()
        return d        


    def _get_python_value(self):
        '''return Ingres ANSIDATE as a Python datetime.date'''

        year = self._buffer.fields.year
        month = self._buffer.fields.month
        day = self._buffer.fields.day
        v = dt.date(year, month, day)
        return v

    
    def _value_setter(self,v):
        '''initialize the Ingres ANSIDATE instance'''

        if v is CURRENT_DATE:
            v = CURRENT_DATE()

        if type(v) not in {dt.date, str}:
            raise TypeError('must be CURRENT_DATE, a str, or a datetime.date')

        if type(v) is str:
            if v.lower() == 'today':
                v = CURRENT_DATE()
            v = dt.date.fromisoformat(v)            

        self._buffer.fields.year = v.year
        self._buffer.fields.month = v.month
        self._buffer.fields.day = v.day


class IIAPI_BOOL_TYPE(IIAPI_TYPE_WITH_INTRINSIC_SIZE):
    '''Ingres BOOLEAN'''

    
    _ds_dataType = py.IIAPI_BOOL_TYPE
    _ds_length = py.IIAPI_BOOL_LEN


    def _SQL_declaration(self):
        return 'BOOLEAN'


    def _allocate_buffer(self):
        _fields_ = [('value', ctypes.c_bool)]
        BOOL_BUFFER = Buffer_Factory(_fields_)
        buffer = BOOL_BUFFER()
        return buffer        


    def _reprfy_value(self):
        if self.datavalue.dv_null:
            r = f'{package_name}.NULL'
        else:
            truth = self._buffer.value
            r = f'{truth}'
        return r
        

    def formatted(self):
        '''return natively formatted Boolean'''

        if self.datavalue.dv_null:
            d = None
        elif self._buffer.value != 0:
            d = 'TRUE'
        elif self._buffer.value == 0:
            d = 'FALSE'
        return d


    def _get_python_value(self):
        '''return Ingres BOOLEAN as a Python bool'''

        v = (True if self._buffer.value else False)
        return v
        

    def _value_setter(self,v):
        '''initialize the Ingres BOOLEAN instance'''

        if v not in {True,False,1,0}:
            raise ValueError('must be True or False')
            
        value = 1 if v else 0
        self._buffer.value = value


class IIAPI_DTE_TYPE(IIAPI_TYPE_WITH_INTRINSIC_SIZE):
    '''Ingres INGRESDATE'''

    ##  INGRESDATE is a disgusting mess. It is unforgivable. I hate it.
    ##  Looking at the implementation details I suspect it was intended to
    ##  be even worse than it is. We can be thankful the culprit died, was 
    ##  fired, or came to their senses before unleashing its full horror.
    ##  And interval() is beyond broken. I despair. I also have a dread
    ##  that I will have to implement arithmetic on INGRESDATE because
    ##  it isn't fully compatible with the Python datetime package; Python 
    ##  could update times in ways that are not expected

    _ds_dataType = py.IIAPI_DTE_TYPE
    _ds_length = py.IIAPI_DTE_LEN

    
    def _SQL_declaration(self):
        return 'INGRESDATE'

    def _now():
        now = dt.datetime.now().strftime('%d-%b-%Y %H:%M:%S')
        return now


    def _today():
        today = dt.date.today().strftime('%d-%b-%Y')
        return today


    def _allocate_conversion_buffers(self):
        '''preallocate conversion buffers'''

        self._conv_source = Char('',35)
        self._conv_target = Char('',35)


    AD_DN_NULL = 0x00
    AD_DN_ABSOLUTE = 0x01 
    AD_DN_DURATION = AD_DN_LENGTH = 0x02 
    AD_DN_YEARSPEC = 0x04 
    AD_DN_MONTHSPEC = 0x08 
    AD_DN_DAYSPEC = 0x10 
    AD_DN_TIMESPEC = 0x20 
    AD_DN_AFTER_EPOCH = 0x40 
    AD_DN_BEFORE_EPOCH = 0x80


    class IngresDate(ctypes.Structure):
        ##  the first byte of an INGRESDATE is a discriminator from which
        ##  it is possible to determine that the value is a date, a date+time, 
        ##  or a duration.  See typedef struct _AD_DATENTRNL in
        ##  ..\main\src\common\hdr\hdr\adudate.h

        ##  the internal representation of an INGRESDATE is:
        ##  char    dn_status   # discriminator
        ##  i1      dn_highday  # high order bits of day
        ##  i2      dn_year     # year number or number of years
        ##  i2      dn_month    # month number or number of months
        ##  u_i2    dn_lowday   # day number or number of days
        ##  i4      dn_time     # time in milliseconds from 00:00
        
        _fields_ = [
            ('discriminator',ctypes.c_ubyte),
            ('highday',ctypes.c_ubyte),
            ('year',ctypes.c_short),
            ('month',ctypes.c_short),
            ('lowday',ctypes.c_ushort),
            ('time',ctypes.c_long) ]


    def _allocate_buffer(self):

        class BUFFER(ctypes.Union):
            _fields_ = [
                ('fields',self.IngresDate),
                ('value',ctypes.c_ubyte * py.IIAPI_DTE_LEN) ]

        buffer = BUFFER()
        return buffer


    def _reprfy_value(self):
        ingres_date = self.formatted()
        return f"'{ingres_date}'"


    def formatted(self):
        '''return natively formatted Ingresdate'''

        ##  require up to 25 character for Ingresdate
        format(self, self._conv_target)
        d = self._conv_target.value.strip()
        return d


    def _get_python_value(self):
        '''return Ingres INGRESDATE a Python type'''

        ##  empty ingresdates are returned as None
        ##  absolute ingresdates are returned as datetime.date
        ##  ingresdates with time returned as timezone-aware datetime.datetime
        ##  intervals are returned as datetime.timedelta

        is_empty = False
        is_date = False
        is_datetime = False
        is_duration = False

        discriminator = self._buffer.fields.discriminator
        highday = self._buffer.fields.highday
        year = self._buffer.fields.year
        month = self._buffer.fields.month
        lowday = self._buffer.fields.lowday
        time = self._buffer.fields.time

        if discriminator == self.AD_DN_NULL:
            is_empty = True
        elif discriminator & self.AD_DN_ABSOLUTE:
            if discriminator & self.AD_DN_TIMESPEC:
                is_datetime = True
            else:
                is_date = True
        elif discriminator & self.AD_DN_DURATION:
            is_duration = True
        else:
            raise RuntimeError(f'unhandled INGRESDATE {discriminator=}')

        assert is_date or is_datetime or is_duration or is_empty

        if is_empty:
            v = None
            return v

        if is_date:
            day = highday << 16 | lowday
            v = dt.date(year, month, day)
        elif is_datetime or is_duration:
            day = highday << 16 | lowday
            secs = int(time / 1000)
            hours = int(secs/3600) 
            secs = secs - hours * 3600
            mins = int(secs/60)
            secs = secs - mins * 60
            
            if is_datetime:
                ##  INGRESDATE with a time is stored as UTC
                v = dt.datetime(year, month, day, 
                    hour=hours, minute=mins, second=secs,
                    tzinfo=dt.timezone.utc)
            elif is_duration:
                ##  Unfortunately datetime.timedelta doesn't handle years, and 
                ##  converting years to days isn't very precise because
                ##  you can't know how many of the years are leap-years. 
                ##  Months are all over the place. I use the rule-of-thumb:
                ##  1 year = 365.2425 days and 1 month = 30.4369 days

                ##  NOTE: for intervals involving years or months there is 
                ##  almost no chance the timedelta number of days will come
                ##  out exactly the same as the Ingres calculation of days
                ##  :-(
                yeardays = round(year * 365.2425)
                monthdays = round(month * 30.4369)
                days = yeardays + monthdays + day
                v = dt.timedelta(days=days, 
                    hours=hours, minutes=mins, seconds=secs)
        return v


    def _value_setter(self,v):
        global _envHandle

        if v == None or v == '':
            ##  an empty value is a valid Ingresdate of all 0s
            self._clear_buffer()
        elif type(v) is str:
            if v.lower == 'today':
                v = self._today()
            elif v.lower == 'now':
                v = self._now()
            ##  use IIapi_formatData() to do str to Ingresdate conversion
            self._conv_source.value = v
            format(self._conv_source, self)
        elif type(v) is dt.date:
            discriminator = (self.AD_DN_ABSOLUTE | 
                self.AD_DN_DAYSPEC | self.AD_DN_MONTHSPEC | self.AD_DN_YEARSPEC)
            highday = 0
            year = v.year
            month = v.month
            lowday = v.day
            msecs = 0
            self._buffer.fields.discriminator = discriminator
            self._buffer.fields.highday = highday
            self._buffer.fields.year = year
            self._buffer.fields.month = month
            self._buffer.fields.lowday = lowday
            self._buffer.fields.time = msecs
        elif type(v) is dt.datetime:
            discriminator = (self.AD_DN_ABSOLUTE | 
                self.AD_DN_DAYSPEC | self.AD_DN_MONTHSPEC |
                self.AD_DN_YEARSPEC | self.AD_DN_TIMESPEC)
            highday = 0
            year = v.year
            month = v.month
            lowday = v.day
            msecs = int(v.microsecond / 1000 +  
                (v.second + v.minute * 60 + v.hour * 60 * 60) * 1000)
        elif type(v) is dt.timedelta:
            discriminator = self.AD_DN_DURATION

            ##  timedelta exposes only days, seconds, and microseconds
            ##  Ingres intervals are a pig's dinner  :-(
            year = 0
            month = 0
            days = v.days
            secs = v.seconds
            microsecs = v.microseconds
            msecs = int(microsecs / 1000 + secs * 1000) 

            ##  Ingresdate intervals are limited to +/-9,999 years, regardless
            ##  which units are used to express the interval:
            ##  YEARS -9999 to +9999
            ##  MONTHS -119988 to +119988
            ##  DAYS -3652047 to +3652047

            if days > 3652047 or days == 3652047 and (secs > 0 or msecs > 0):
                raise OverflowError('cannot exceed 3652047 days') 
            if days < -3652047 or days == -3652047 and (secs < 0 or msecs < 0):
                raise OverflowError('cannot exceed -3652047 days') 

            if days:
                discriminator |= self.AD_DN_DAYSPEC
            lowday = days & 0xFFFF 
            highday = days >> 16 & 0xFF
            ##  massage highday into the form struct.pack_into expects when
            ##  highday is negative
            highday = highday.to_bytes(1, sys.byteorder)
            highday = int.from_bytes(highday, sys.byteorder, signed=True)

            if secs or msecs:
                discriminator |= self.AD_DN_TIMESPEC

            struct.pack_into(self.format, self.buffer, 0,  # <-- FIX ME
                discriminator, highday, year, month, lowday, msecs)
        else:
            v_type = type(v)
            raise TypeError('{v} is not a datetime type')


class IIAPI_INTYM_TYPE(IIAPI_TYPE_WITH_INTRINSIC_SIZE):
    '''Ingres INTERVAL YEAR TO MONTH'''


    _ds_dataType = py.IIAPI_INTYM_TYPE
    _ds_length = py.IIAPI_INTYM_LEN


    def _allocate_conversion_buffers(self):
        '''preallocate conversion buffers'''

        self._conv_source = Char('',64)
        self._conv_target = Char('',64)


    def _SQL_declaration(self):
        return 'INTERVAL YEAR TO MONTH'


    def _allocate_buffer(self):
        ##  internal representation of INTERVAL YEAR TO MONTH is:
        ##  i2  dn_years    # years component (-9999 to 9999) 
        ##  i1  dn_months   # months component (-11 to 11)  
        _fields_ = [
            ('years',ctypes.c_short),
            ('months',ctypes.c_byte) ]
        INTERVAL_YM_BUFFER = Buffer_Factory(_fields_)
        buffer = INTERVAL_YM_BUFFER()
        return buffer


    def _reprfy_value(self):
        interval = self.formatted()
        return f"'{interval}'"
        return r


    def formatted(self):
        '''return natively formatted value'''

        ##  require up to 64 characters
        format(self, self._conv_target)
        d = self._conv_target.value.strip()
        return d


    def _get_python_value(self):
        '''return Ingres INTERVAL_YM as Python tuple'''

        ##  Python datetime.timedelta is not a good analogue for INTERVAL_YM;
        ##  if the user wants a timedelta let them do the work and decide if
        ##  what they did is any good...
        return (self._buffer.years, self._buffer.months)


    def _value_setter(self,v):
        '''initialize the Ingres INTERVAL_YM instance'''

        if type(v) is str:
            self._conv_source.value = v
            format(self._conv_source,self)
        elif type(v) is Ingresdate:
            ##  note the Ingresdate must be expressed in terms of months; 
            ##  days are not automatically converted to months first; Ingres
            ##  itself behaves the same (IMO wrong) way
            self._conv_source = v
            format(self._conv_source,self)            
        else:
            if type(v) is tuple:
                years = v[0]
                months = v[1]
            elif type(v) is dt.timedelta:
                ##  Python datetime.timedelta is not a good analogue for
                ##  INTERVAL_YM so just do what we can to estimate years and
                ##  months; if there are 365.2425 days per year and 12 months
                ##  per year, there are 30.436878 days per month

                ##  modulo on negative numbers doesn't give us the required 
                ##  form of output, so note the sign and use the absolute 
                ##  value

                sign = -1 if v.days < 0 else 1
                days = abs(v.days)
                months = int(days / 30.436878)
                years = int(months / 12)
                months = months % 12
                years = sign * years
                months = sign * months
            else:
                raise TypeError('must be tuple, str, Ingresdate, or datetime.timedelta')

            if not (0 <= abs(years) <= 9999):
                raise OverflowError('years not in -9999 to 9999')
                if not (0 <= abs(month) <= 11):
                    raise OverflowError('month not in -11 to 11')
            self._buffer.years = years
            self._buffer.months = months


class IIAPI_IPV4_TYPE(IIAPI_TYPE_WITH_INTRINSIC_SIZE):
    '''Ingres IPV4'''


    _ds_dataType = py.IIAPI_IPV4_TYPE
    _ds_length = py.IIAPI_IPV4_LEN


    def _SQL_declaration(self):
        return 'IPV4'


    def _allocate_conversion_buffers(self):
        '''preallocate conversion buffers'''

        self._conv_target = Char('',15)


    def _allocate_buffer(self):
        _fields_ = [('value', ctypes.c_ubyte * py.IIAPI_IPV4_LEN)]
        IPV4_BUFFER = Buffer_Factory(_fields_)
        buffer = IPV4_BUFFER()
        return buffer        


    def _reprfy_value(self):
        address = self.formatted()
        return f"'{address}'"


    def formatted(self):
        format(self,self._conv_target)
        s = self._conv_target.value.strip()
        return s


    def _get_python_value(self):
        '''return IPV4 as Python ipaddress.IPv4Address'''

        b = bytes(self._buffer)
        v = ip.IPv4Address(b)
        return v
        

    def _value_setter(self,v):
        '''initialize the Ingres IPV4 instance'''

        try:
            v = ip.ip_address(v)
        except:
            raise ValueError('could not convert to IPV4')

        value = v.packed
        ctypes.memmove(self.datavalue.dv_value, value, py.IIAPI_IPV4_LEN)


class IIAPI_IPV6_TYPE(IIAPI_TYPE_WITH_INTRINSIC_SIZE):
    '''Ingres IPV6'''


    _ds_dataType = py.IIAPI_IPV6_TYPE
    _ds_length = py.IIAPI_IPV6_LEN


    def _SQL_declaration(self):
        return 'IPV6'


    def _allocate_conversion_buffers(self):
        '''preallocate conversion buffers'''

        self._conv_target = Char('',40)


    def _allocate_buffer(self):
        _fields_ = [('value', ctypes.c_ubyte * py.IIAPI_IPV6_LEN)]
        IPV6_BUFFER = Buffer_Factory(_fields_)
        buffer = IPV6_BUFFER()
        return buffer        


    def _reprfy_value(self):
        address = self.formatted()
        return f"'{address}'"


    def formatted(self):
        format(self,self._conv_target)
        s = self._conv_target.value.strip()
        return s


    def _get_python_value(self):
        '''return IPV6 as Python ipaddress.IPv6Address'''

        b = bytes(self._buffer)
        v = ip.IPv6Address(b)
        return v
        

    def _value_setter(self,v):
        '''initialize the Ingres IPV4 instance'''

        try:
            v = ip.ip_address(v)
        except:
            raise ValueError('could not convert to IPV6')

        value = v.packed
        ctypes.memmove(self.datavalue.dv_value, value, py.IIAPI_IPV6_LEN)


class IIAPI_MNY_TYPE(IIAPI_TYPE_WITH_INTRINSIC_SIZE):
    '''ingres MONEY'''

    ##  MONEY is difficult; I like that they tried but it's not done 
    ##  well enough to be useful and a pain to work with here.
    ##  Stores values as float8 "cents"; it attempts to handle currencies
    ##  with 0, 1, and 2 digits after the separator. The separator can be 
    ##  a decimal or a comma.  Needs to be displayed with a currency
    ##  symbol preceding or following the numeric value. Refer to 
    ##  II_MONEY_FORMAT, II_MONEY_PREC, and II_DECIMAL


    _ds_dataType = py.IIAPI_MNY_TYPE
    _ds_length = py.IIAPI_MNY_LEN


    def _SQL_declaration(self):
        return 'MONEY'


    def _allocate_conversion_buffers(self):
        '''preallocate conversion buffers'''

        self._conv_source = Char('',25)
        self._conv_target = Char('',25)


    def _allocate_buffer(self):
        _fields_ = [('value', ctypes.c_double)]
        MONEY_BUFFER = Buffer_Factory(_fields_)
        buffer = MONEY_BUFFER()
        return buffer


    def _reprfy_value(self):
        amount = self.formatted()
        return f"'{amount}'"


    def formatted(self):
        '''return natively formatted MONEY'''

        ##  require up to 25 character for MONEY
        target = Char('',25)
        format(self, self._conv_target)
        d = self._conv_target.value.strip()
        return d


    def _get_python_value(self):
        '''return Ingres MONEY as a Python float'''

        ##  MONEY is stored as cents so we need to scale it.
        ##  float is not ideal but it is what C users expect
        value = self._buffer.value
        v = float(value) / 100.
        return v


    def _value_setter(self,v):
        '''initialize the Ingres MONEY instance'''

        ##  if v is a str it can include an optional currency symbol;
        ##  use py.IIapi_formatData() by calling format()
        if type(v) == str:
            self._conv_source.value = v
            format(self._conv_source,self)
            return
        ##  otherwise make v a float()
        try:
            v = float(v)
        except:
            raise ValueError('must be float, decimal.Decimal, or str')

        ##  convert to cents
        value = v * 100.

        self._buffer.value = value


class IIAPI_LOGKEY_TYPE(IIAPI_TYPE_WITH_INTRINSIC_SIZE):
    '''Ingres OBJECT_KEY'''


    _ds_dataType = py.IIAPI_LOGKEY_TYPE
    _ds_length = py.IIAPI_LOGKEY_LEN

    ##  example: 010000000000000054010000B4E10A66


    def _SQL_declaration(self):
        return 'LOGICAL_KEY'


    def _allocate_buffer(self):
        _fields_ = [('value', ctypes.c_ubyte * py.IIAPI_LOGKEY_LEN)]
        LOGKEY_BUFFER = Buffer_Factory(_fields_)
        buffer = LOGKEY_BUFFER()
        return buffer        


    def _reprfy_value(self):
        key = self._peek()
        return f"'{key}'"


    def _get_python_value(self):
        '''return OBJECT_KEY as python bytes'''

        v = bytes(self._buffer)
        return v
        

    def _value_setter(self,v):
        '''initialize the OBJECT_KEY from bytes, bytearray, or str'''

        if type(v) is bytes:
            value = v
        elif type(v) is bytearray:
            value = bytes(v)
        elif type(v) is str:
            value = bytes.fromhex(v)
        else:
            raise TypeError('not bytes, bytearray, or str')
        
        vlen = len(value)
        if vlen != py.IIAPI_LOGKEY_LEN:
            raise ValueError(
                f'OBJECT_KEY value must be {py.IIAPI_LOGKEY_LEN} bytes')

        ctypes.memmove(self.datavalue.dv_value, value, py.IIAPI_LOGKEY_LEN)


class IIAPI_TABKEY_TYPE(IIAPI_TYPE_WITH_INTRINSIC_SIZE):
    '''Ingres TABLE_KEY'''


    _ds_dataType = py.IIAPI_TABKEY_TYPE
    _ds_length = py.IIAPI_TABKEY_LEN

    ##  example: 54010000B4E10A66


    def _SQL_declaration(self):
        return 'TABLE_KEY'


    def _allocate_buffer(self):
        _fields_ = [('value', ctypes.c_ubyte * py.IIAPI_TABKEY_LEN)]
        TABKEY_BUFFER = Buffer_Factory(_fields_)
        buffer = TABKEY_BUFFER()
        return buffer        


    def _reprfy_value(self):
        key = self._peek()
        return f"'{key}'"


    def _get_python_value(self):
        '''return TABLE_KEY as python bytes'''

        v = bytes(self._buffer)
        return v
        

    def _value_setter(self,v):
        '''initialize the TABLE_KEY from bytes, bytearray, or str'''

        if type(v) is bytes:
            value = v
        elif type(v) is bytearray:
            value = bytes(v)
        elif type(v) is str:
            value = bytes.fromhex(v)
        else:
            raise TypeError('not bytes, bytearray, or str')
        
        vlen = len(value)
        if vlen != py.IIAPI_TABKEY_LEN:
            raise ValueError(
                f'TABLE_KEY value must be {py.IIAPI_TABKEY_LEN} bytes')

        ctypes.memmove(self.datavalue.dv_value, value, py.IIAPI_TABKEY_LEN)


class IIAPI_UUID_TYPE(IIAPI_TYPE_WITH_INTRINSIC_SIZE):
    '''Ingres UUID'''

    ##  https://www.ietf.org/rfc/rfc4122.txt

    ##  Ingres UUIDs are a bit of a mess. On *nix, Ingres generates 
    ##  Type-1 UUIDs--or something that looks sorta like a Type-1 UUID.
    ##  On Windows, Ingres generates what looks like a totally
    ##  random bit pattern. That seems to be an endian thing. Once you account
    ##  for it you see that on Windows Ingres probably generates Type-4 UUIDs.
    ##  We'll just render them so they look like how Ingres renders them,
    ##  even though what Ingres does is probably wrong on Windows.
    ##  Also we'll gloss over the fact Ingres should generate the same 
    ##  kind of UUIDs regardless of the host OS! (Refer to the
    ##  II_UUID_MAC environment variable)


    _ds_dataType = py.IIAPI_UUID_TYPE
    _ds_length = py.IIAPI_UUID_LEN


    def _SQL_declaration(self):
        return 'UUID'


    def _allocate_buffer(self):
        _fields_ = [('value', ctypes.c_ubyte * py.IIAPI_UUID_LEN)]
        UUID_BUFFER = Buffer_Factory(_fields_)
        buffer = UUID_BUFFER()
        return buffer        


    def _reprfy_value(self):
        uuid = str(self.value)
        return f"'{uuid}'"


    def _get_python_value(self):
        '''return UUID as python uuid.UUID'''

        b = bytes(self._buffer)
        v = uu.UUID(bytes=b)
        return v
        

    def _value_setter(self,v):
        '''initialize the UUID from uuid.UUID, bytes, bytearray, or str'''

        if type(v) is uu.UUID:
            value = v.bytes
        elif type(v) is bytearray:
            value = bytes(v)
        elif type(v) is bytes:
            value = v
        elif type(v) is str:
            ##  let any exception escape
            uuid = uu.UUID(v)
            value = uuid.bytes
        else:
            raise TypeError('not uuid.UUID, bytes, bytearray, or str')
        
        vlen = len(value)
        if vlen != py.IIAPI_UUID_LEN:
            raise ValueError(f'UUID value must be {_ds_length} bytes')

        ctypes.memmove(self.datavalue.dv_value, value, py.IIAPI_UUID_LEN)


##  -------------------  IIAPI_TYPE_WITH_LIMITED_SIZE  -------------------------


class IIAPI_TYPE_WITH_LIMITED_SIZE(IIAPI_TYPE):
    ##  BYTE
    ##  C
    ##  CHAR
    ##  NCHAR
    ##  NVARCHAR
    ##  TEXT
    ##  VARBYTE
    ##  VARCHAR

    ##  these types can take two positional arguments (value and size), though
    ##  size can optionally be omitted and inferred from value
    _expected_positionals = 2


    def __repr__(self):
        classname = type(self).__qualname__
        value = self._reprfy_value()
        size = self.descriptor.ds_length
        modifier = self._reprfy_nullability()
        r = f'{package_name}.{classname}({value},{size}{modifier})'
        return r


    ##  value can be up to 32,000 bytes; overridden by NCHAR and NVARCHAR
    MAX_SIZE = 32000 


    def _validate_size(self):
        '''ensure size is within limits'''
        if not ( 0 < self.descriptor.ds_length <= self.MAX_SIZE ):
            raise OverflowError(f'size exceeds {self.MAX_SIZE}')


    def _to_bytes(self,value):
        '''get value as python bytes'''

        if type(value) is bytes:
            pass
        elif type(value) is bytearray:
            value = bytes(value)
        elif type(value) is str:
            value = value.encode()
        else:
            raise TypeError('not bytes, bytearray, or str')
        return value


    def _get_ds_length(self,*args):
        '''get length or implied length to use as ds_length'''

        try:
            length = args[1]
        except IndexError:
            value = self._get_initial_value(*args)
            if type(value) not in {bytes,bytearray,str}:
                raise TypeError('not bytes, bytearray, or str')
            length = len(value)
        return length


    def _value_setter(self,value):
        value = self._to_bytes(value)
        self._clear_buffer()
        try:
            self._buffer.value = value
        except ValueError as ve:
            type_name = self.SQL_declaration
            raise OverflowError(f'{type_name} capacity exceeded')


class IIAPI_BYTE_TYPE(IIAPI_TYPE_WITH_LIMITED_SIZE):
    '''Ingres BYTE(n)'''


    _ds_dataType = py.IIAPI_BYTE_TYPE


    def _SQL_declaration(self):
        size = self.descriptor.ds_length
        declaration = f'BYTE({size})'
        return declaration


    def _allocate_buffer(self):
        ds_length = self.descriptor.ds_length
        _fields_ =  [('value', ctypes.c_char * ds_length)]
        BYTE_BUFFER = Buffer_Factory(_fields_)
        buffer = BYTE_BUFFER()
        return buffer


    def _reprfy_value(self):
        value,_ = codecs.escape_decode(self.value)
        return value


    def _get_python_value(self):
        '''return Ingres BYTE as a Python bytes'''

        v = bytes(self._buffer)
        return v


class IIAPI_CHA_TYPE(IIAPI_TYPE_WITH_LIMITED_SIZE):
    '''Ingres CHAR(n)'''

    _ds_dataType = py.IIAPI_CHA_TYPE


    def _SQL_declaration(self):
        size = self.descriptor.ds_length
        declaration = f'CHAR({size})'
        return declaration


    def _clear_buffer(self):
        '''flood the buffer with ASCII blanks (0x20)'''

        address = self.datavalue.dv_value
        length = self.descriptor.ds_length
        ctypes.memset(address, 0x20, length)


    def _allocate_buffer(self):
        ds_length = self.descriptor.ds_length
        _fields_ =  [('value', ctypes.c_char * ds_length)]
        CHA_BUFFER = Buffer_Factory(_fields_)
        buffer = CHA_BUFFER()
        return buffer


    def _value_setter(self,value):
        value = self._to_bytes(value)
        ##  pad the value to its declared length with ASCII blanks if necessary
        if len(value) < self.descriptor.ds_length:
            value = value + (self.descriptor.ds_length * b' ')
            value = value[:self.descriptor.ds_length]
        try:
            self._buffer.value = value
        except ValueError as ve:
            type_name = self.SQL_declaration
            raise OverflowError(f'{type_name} capacity exceeded')


    def _reprfy_value(self):
        value,_ = codecs.escape_decode(self.value)
        return value


    def _get_python_value(self):
        '''return Ingres CHAR(n) as a Python str'''

        v = bytes(self._buffer)
        s = v.decode()
        return s


class IIAPI_CHR_TYPE(IIAPI_CHA_TYPE):
    '''Ingres Cn'''
    ##  until we find out it's a mistake we will treat the deprecated
    ##  Ingres C(n) type as a CHAR(n). Not even Ingres treats C(n) in
    ##  the documented manner; it should not allow control characters
    ##  but it does

    _ds_dataType = py.IIAPI_CHR_TYPE


    def _SQL_declaration(self):
        size = self.descriptor.ds_length
        declaration = f'C{size}'
        return declaration


class IIAPI_UNICODE_TYPE_WITH_LIMITED_SIZE(IIAPI_TYPE_WITH_LIMITED_SIZE):
    '''abstract parent for NCHAR() and NVARCHAR()'''

    ##  All this NCHAR/NVARCHAR code is more elaborate than you'd expect
    ##  because the Mac/Darwin version of ctypes uses 4 bytes for c_wchar.
    ##  Consequently we have to do everything in terms of single bytes (so the 
    ##  same Python code will work everywhere).

    ##  Ingres uses UCS-2 and Python uses UTF-16. UCS-2 is a fixed-width 
    ##  encoding but UTF-16 is fixed width only within a single value. That
    ##  is, a UTF-16 string can be single-byte UTF-16 or double-byte UTF-16.
    ##  That said, we are going to treat UCS-2 as UTF-16 (--until we find out
    ##  we can't!)

    ##  https://tenthousandmeters.com/blog/\
    ##  python-behind-the-scenes-9-how-python-strings-work/


    def _get_ds_length(self,*args):
        '''get length or implied length to use as ds_length'''

        try:
            length = args[1]
            length = length * 2 ##  UCS-2 characters are 2 bytes each
        except IndexError:
            value = self._get_initial_value(*args)
            if type(value) not in {bytes,bytearray,str}:
                raise TypeError('not bytes, bytearray, or str')
            if type(value) is str:
                ##  need 2 bytes to UCS-2 encode each character
                length = len(value) * 2
            else:
                length = len(value)
        return length


    def _encode(self,value):
        if type(value) is bytes:
            pass
        elif type(value) is bytearray:
            value = bytes(value)
        elif type(value) is str:
            value = value.encode('utf-16le')
        else:
            raise TypeError('not bytes, bytearray, or str')
        return value


    def _decode(self,value):
        s = value.decode('utf-16le')
        return s


class IIAPI_NCHA_TYPE(IIAPI_UNICODE_TYPE_WITH_LIMITED_SIZE):
    '''Ingres NCHAR(n)'''        

    _ds_dataType = py.IIAPI_NCHA_TYPE

    ##  Unicode types are limited to half the usual number of characters
    MAX_SIZE = 16000 


    def _SQL_declaration(self):
        size = self.descriptor.ds_length // 2   ##  UCS-2 characters are 2 bytes
        declaration = f'NCHAR({size})'
        return declaration


    def _clear_buffer(self):
        '''flood the buffer with UTF-16 blanks (0x0020)'''

        size = self.descriptor.ds_length // 2   ##  UCS-2 characters are 2 bytes
        address = self.datavalue.dv_value
        spaces = ' ' * size
        filler = bytes(spaces.encode('utf-16le'))
        ctypes.memmove(address, filler, len(filler))


    def _allocate_buffer(self):
        ds_length = self.descriptor.ds_length
        _fields_ =  [('value', ctypes.c_char * ds_length)]
        BYTE_BUFFER = Buffer_Factory(_fields_)
        buffer = BYTE_BUFFER()
        return buffer


    def _reprfy_value(self):
        ##  this is not the right way to do this; consider this a place-holder
        value = self._get_python_value().strip().replace("'","\\'")
        return f"'{value}'"


    def __repr__(self):
        classname = type(self).__qualname__
        value = self._reprfy_value()
        size = self.descriptor.ds_length // 2   ##  UCS-2 characters are 2 bytes
        modifier = self._reprfy_nullability()
        r = f'{package_name}.{classname}({value},{size}{modifier})'
        return r


    def _get_python_value(self):
        '''return Ingres NCHAR(n) as a Python str'''

        v = bytes(self._buffer)
        s = self._decode(v)
        return s


    def _value_setter(self,value):
        value = self._encode(value)
        dv_length = len(value)
        if dv_length > self.descriptor.ds_length:
            type_name = self.SQL_declaration
            raise OverflowError(f'{type_name} capacity exceeded')        
        self._clear_buffer()
        ctypes.memmove(self.datavalue.dv_value, value, dv_length)


class IIAPI_NVCH_TYPE(IIAPI_UNICODE_TYPE_WITH_LIMITED_SIZE):
    '''Ingres NVARCHAR(n)'''        


    _ds_dataType = py.IIAPI_NVCH_TYPE


    ##  Unicode types are limited to half the usual number of characters
    MAX_SIZE = 16000 


    def _get_ds_length(self,*args):
        length = super()._get_ds_length(*args)
        ##  add 2 to allow for the internal length indicator
        length = length + 2
        return length


    def _SQL_declaration(self):
        ##  deduct 2 bytes for the length indicator
        size = self.descriptor.ds_length - 2 
        ##  UCS-2 characters are 2 bytes each
        declared_size = size // 2
        declaration = f'NVARCHAR({declared_size})'
        return declaration


    def _allocate_buffer(self):
        ds_length = self.descriptor.ds_length
        _fields_ =  [
            ('length', ctypes.c_short),
            ('value', ctypes.c_char * ds_length ) ]
        NVCH_BUFFER = Buffer_Factory(_fields_)
        buffer = NVCH_BUFFER()
        return buffer


    def _reprfy_value(self):
        ##  this is not the right way to do this; consider this a place-holder
        value = self._get_python_value().strip().replace("'","\\'")
        return f"'{value}'"


    def __repr__(self):
        classname = type(self).__qualname__
        value = self._reprfy_value()
        ##  there is a 2 byte overhead and UCS-2 characters are 2 bytes each
        size = (self.descriptor.ds_length - 2) // 2
        modifier = self._reprfy_nullability()
        r = f'{package_name}.{classname}({value},{size}{modifier})'
        return r


    def _get_python_value(self):
        '''return Ingres NVARCHAR(n) as a Python str'''
    
        size = self._buffer.length
        v = ctypes.string_at(self.datavalue.dv_value + 2, size)
        s = v.decode('utf-16le') 
        return s


    def _value_setter(self,value):
        value = self._encode(value)
        dv_length = len(value)
        ##  2 bytes are reserved for the internal length indicator
        max_length = self.descriptor.ds_length - 2
        if dv_length > max_length:
            type_name = self.SQL_declaration
            raise OverflowError(f'{type_name} capacity exceeded')        
        self._clear_buffer()
        ##  move with offset 2 bytes, past the length indicator
        ctypes.memmove(self.datavalue.dv_value + 2, value, dv_length)
        self._buffer.length = dv_length



class IIAPI_TXT_TYPE(IIAPI_TYPE_WITH_LIMITED_SIZE):
    '''Ingres TEXT(n)'''        

    _ds_dataType = py.IIAPI_TXT_TYPE


    def _SQL_declaration(self):
        size = self.descriptor.ds_length
        declaration = f'TEXT({size})'
        return declaration


    def _allocate_buffer(self):
        ds_length = self.descriptor.ds_length
        _fields_ =  [('value', ctypes.c_char * ds_length)]
        TXT_BUFFER = Buffer_Factory(_fields_)
        buffer = TXT_BUFFER()
        return buffer


    def __repr__(self):
        classname = type(self).__qualname__
        value = self.value
        size = self.descriptor.ds_length
        modifier = self._reprfy_nullability()
        r = f'{package_name}.{classname}("{value}",{size}{modifier})'
        return r


    def _get_python_value(self):
        '''return Ingres TEXT(n) as a Python str'''

        v = bytes(self._buffer)
        ##  strip trailing NULs
        s = v.rstrip(b'\x00')
        s = s.decode()
        return s


    def _value_setter(self,value):
        '''initialize the TEXT() from bytes, bytearray, or str'''
    
        value = self._to_bytes(value)
        ##  convert embedded NULs to ASCII space (0x20)
        value = value.replace(b'\x00',b'\x20')
        self._clear_buffer()
        try:
            self._buffer.value = value
        except ValueError as ve:
            type_name = self.SQL_declaration
            raise OverflowError(f'{type_name} capacity exceeded')


class IIAPI_VBYTE_TYPE(IIAPI_TYPE_WITH_LIMITED_SIZE):
    '''Ingres VARBYTE(n)'''


    _ds_dataType = py.IIAPI_VBYTE_TYPE


    def _get_ds_length(self,*args):
        length = super()._get_ds_length(*args)
        ##  add 2 to allow for the internal length indicator
        length = length + 2
        return length


    def _SQL_declaration(self):
        ds_length = self.descriptor.ds_length
        ##  deduct 2 bytes for the length indicator
        declared_size = ds_length - 2
        declaration = f'VARBYTE({declared_size})'
        return declaration


    def _allocate_buffer(self):
        ds_length = self.descriptor.ds_length
        size = ds_length - 2
        _fields_ =  [
            ('length', ctypes.c_short),
            ('value', ctypes.c_char * size) ]
        VARBYTE_BUFFER = Buffer_Factory(_fields_)
        buffer = VARBYTE_BUFFER()
        return buffer


    def __repr__(self):
        classname = type(self).__qualname__
        value = self._get_python_value()
        size = self.descriptor.ds_length - 2    ##  includes 2 byte overhead
        modifier = self._reprfy_nullability()
        r = f'{package_name}.{classname}({value},{size}{modifier})'
        return r


    def _get_python_value(self):
        '''return Ingres VARBYTE(n) as a Python bytes'''
    
        length = self._buffer.length
        v = bytes(self._buffer.value[:length])
        return v


    def _value_setter(self,value):
        value = self._to_bytes(value)
        dv_length = len(value)
        self._buffer.length = dv_length
        try:
            self._buffer.value = value
        except ValueError as ve:
            type_name = self.SQL_declaration
            raise OverflowError(f'{type_name} capacity exceeded')        


class IIAPI_VCH_TYPE(IIAPI_VBYTE_TYPE):
    '''Ingres VARCHAR(n)'''


    _ds_dataType = py.IIAPI_VCH_TYPE


    def _SQL_declaration(self):
        ds_length = self.descriptor.ds_length
        ##  deduct 2 bytes for the length indicator
        declared_size = ds_length - 2
        declaration = f'VARCHAR({declared_size})'
        return declaration


    def __repr__(self):
        classname = type(self).__qualname__
        value = self._get_python_value()
        size = self.descriptor.ds_length - 2    ##  includes 2 byte overhead
        modifier = self._reprfy_nullability()
        r = f'{package_name}.{classname}("{value}",{size}{modifier})'
        return r


    def _get_python_value(self):
        '''return Ingres VARCHAR(n) as a Python str'''
    
        length = self._buffer.length
        v = bytes(self._buffer.value[:length])
        s = v.decode()
        return s


##  -----------------------  IIAPI_TYPE_WITH_1248  -----------------------------


class IIAPI_TYPE_WITH_1248(IIAPI_TYPE):
    ##  FLOAT4
    ##  FLOAT8
    ##  INTEGER1
    ##  INTEGER2
    ##  INTEGER4
    ##  INTEGER8

    ##  these types REQUIRE two positional arguments (value and size)
    _expected_positionals = 2
    
    def _get_ds_length(self,*args):
        try:
            ds_length = args[1]
        except IndexError:
            raise RuntimeError('no size specified')

        if ds_length not in {1,2,4,8}:
            raise ValueError('invalid size')

        return ds_length
    
 
class IIAPI_FLT_TYPE(IIAPI_TYPE_WITH_1248):
    '''Ingres FLOATn'''

    
    _ds_dataType = py.IIAPI_FLT_TYPE


    def _SQL_declaration(self):
        declarations = {
            4 : 'FLOAT4',
            8 : 'FLOAT' }
        size = self.descriptor.ds_length 
        declaration = declarations[size]
        return declaration


    def _validate_size(self):
        '''ensure size is permissible'''
        ##  NB size here is NOT the range of binary precision (which Ingres 
        ##  does support in syntax, with values in the range 0 to 53...if
        ##  you're interested)
        if self.descriptor.ds_length not in {4,8}:
            raise ValueError(f'size not 4 or 8')


    def _allocate_buffer(self):
        if self.descriptor.ds_length == 4:
            _fields_ = [('value', ctypes.c_float)]
        else:
            _fields_ = [('value', ctypes.c_double)]
        FLT_BUFFER = Buffer_Factory(_fields_)
        buffer = FLT_BUFFER()
        return buffer        


    def __repr__(self):
        classname = type(self).__qualname__
        v = self.value
        size = self.descriptor.ds_length
        if size == 4:
            value = f'{v:.8g}'
        else:
            value = f'{v:.15g}'
        modifier = self._reprfy_nullability()
        r = f'{package_name}.{classname}({value},{size}{modifier})'
        return r

    
    def _get_python_value(self):
        '''return Ingres FLOAT as a Python float'''

        v = self._buffer.value
        return v


    def _value_setter(self,v):
        '''initialize the Ingres FLOAT instance'''

        if type(v) is int:
            v = float(v)
        if type(v) is not float:
            raise TypeError('not float or int')

        self._buffer.value = v


class IIAPI_INT_TYPE(IIAPI_TYPE_WITH_1248):
    '''Ingres INTEGERn'''

    
    _ds_dataType = py.IIAPI_INT_TYPE


    def _SQL_declaration(self):
        declarations = {
            1 : 'TINYINT',
            2 : 'SMALLINT',
            4 : 'INTEGER',
            8 : 'BIGINT' }
        size = self.descriptor.ds_length 
        declaration = declarations[size]
        return declaration


    def _validate_size(self):
        '''ensure size is permissible'''
        size = self.descriptor.ds_length
        if size not in {1,2,4,8}:
            raise ValueError(f'size not 1, 2, 4, or 8')
        ##  save bounds to facilitate overflow checking    
        self.upper_bound = 2 ** (8 * size - 1) - 1
        self.lower_bound = 2 ** (8 * size - 1) * -1


    def _allocate_buffer(self):
        if self.descriptor.ds_length == 1:
            _fields_ = [('value', ctypes.c_byte)]
        elif self.descriptor.ds_length == 2:
            _fields_ = [('value', ctypes.c_short)]
        elif self.descriptor.ds_length == 4:
            _fields_ = [('value', ctypes.c_int)]
        else:
            _fields_ = [('value', ctypes.c_longlong)]
        FLT_BUFFER = Buffer_Factory(_fields_)
        buffer = FLT_BUFFER()
        return buffer        


    def __repr__(self):
        classname = type(self).__qualname__
        size = self.descriptor.ds_length
        value = self.value
        modifier = self._reprfy_nullability()
        r = f'{package_name}.{classname}({value},{size}{modifier})'
        return r

    
    def _get_python_value(self):
        '''return Ingres INTEGER as a Python int'''

        v = self._buffer.value
        return v


    def _value_setter(self,v):
        '''initialize the Ingres INTEGER instance'''

        if type(v) is not int:
            raise TypeError('not int')
        if not ( self.lower_bound <= v <= self.upper_bound):
            raise OverflowError
        self._buffer.value = v


##  create wrappers and aliases
def Float4(*args,**kwargs):
    try:
        descriptor = kwargs['descriptor']
        return IIAPI_FLT_TYPE(*args,**kwargs)
    except KeyError:
        return IIAPI_FLT_TYPE(*args,4,**kwargs)

def Float8(*args,**kwargs):
    try:
        descriptor = kwargs['descriptor']
        return IIAPI_FLT_TYPE(*args,**kwargs)
    except KeyError:
        return IIAPI_FLT_TYPE(*args,8,**kwargs)

def Integer1(*args,**kwargs):
    try:
        descriptor = kwargs['descriptor']
        return IIAPI_INT_TYPE(*args,**kwargs)
    except KeyError:
        return IIAPI_INT_TYPE(*args,1,**kwargs)

def Integer2(*args,**kwargs):
    try:
        descriptor = kwargs['descriptor']
        return IIAPI_INT_TYPE(*args,**kwargs)
    except KeyError:
        return IIAPI_INT_TYPE(*args,2,**kwargs)

def Integer4(*args,**kwargs):
    try:
        descriptor = kwargs['descriptor']
        return IIAPI_INT_TYPE(*args,**kwargs)
    except KeyError:
        return IIAPI_INT_TYPE(*args,4,**kwargs)

def Integer8(*args,**kwargs):
    try:
        descriptor = kwargs['descriptor']
        return IIAPI_INT_TYPE(*args,**kwargs)
    except KeyError:
        return IIAPI_INT_TYPE(*args,8,**kwargs)


##  ---------------------  IIAPI_TYPE_WITH_RESOLUTION  -------------------------


class IIAPI_TYPE_WITH_RESOLUTION(IIAPI_TYPE_WITH_INTRINSIC_SIZE):
    ##  INTERVAL_DS
    ##  TIME
    ##  TIME_WLTZ
    ##  TIME_WTZ
    ##  TIMESTAMP
    ##  TIMESTAMP_WLTZ
    ##  TIMESTAMP_WTZ

    ##  these types take two positional arguments (value and resolution);
    ##  the default resolution is 0, except for timestamp which is 6, 
    ##  and is stored as descriptor.ds_precision (not ds_scale, as you might
    ##  have expected)

    _expected_positionals = 2


    def _SQL_declaration(self):
        templates = {
            py.IIAPI_INTDS_TYPE: 'INTERVAL DAY TO SECOND({})',
            py.IIAPI_TIME_TYPE: 'TIME({}) WITH LOCAL TIME ZONE',
            py.IIAPI_TMTZ_TYPE: 'TIME({}) WITH TIME ZONE',
            py.IIAPI_TMWO_TYPE: 'TIME({})',
            py.IIAPI_TS_TYPE: 'TIMESTAMP({}) WITH LOCAL TIME ZONE',
            py.IIAPI_TSTZ_TYPE: 'TIMESTAMP({}) WITH TIME ZONE',
            py.IIAPI_TSWO_TYPE: 'TIMESTAMP({})'  }
        ##  ds_precision is used for the resolution
        type = self.descriptor.ds_dataType
        resolution = self.descriptor.ds_precision 
        declaration = templates[type].format(resolution)
        return declaration


    def _get_dv_length(self):
        '''use ds_length for dv_length'''
        ##  the buffer may be padded but the server doesn't want to know
        return self._get_ds_length()


    ##  allocate conversion buffers  <- FIX ME; this well enough to trick 
    ##  you but it's dangerous. Find another way to preallocate the conversion
    ##  buffers
    _conv_source = IIAPI_CHA_TYPE('',64)
    _conv_target = IIAPI_CHA_TYPE('',64)


    ##  because of the way Python datetime works we support only scale of
    ##  0, 3 or 6; higher resolution is lost; intermediate resolution are
    ##  promoted (e.g. TIME(4) is treated as TIME(6))


    _default_precision = 0

    def _get_ds_precision(self,*args):
        try: 
            precision = args[1]
        except IndexError:
            precision = self._default_precision
        return precision


    def _validate_size(self):
        if not ( 0 <= self.descriptor.ds_scale <= 9 ):
            raise OverflowError('resolution not in 0 to 9')


    def formatted(self):
        '''return natively formatted value, respecting resolution'''

        ##  require up to 64 characters
        format(self, self._conv_target)
        d = self._conv_target.value.strip()
        return d


    def __repr__(self):
        classname = type(self).__qualname__
        value = self.formatted()
        resolution = self.descriptor.ds_precision
        modifier = self._reprfy_nullability()
        r = f'{package_name}.{classname}("{value}",{resolution}{modifier})'
        return r


class IIAPI_INTDS_TYPE(IIAPI_TYPE_WITH_RESOLUTION):
    '''ingres INTERVAL DAY TO SECOND'''

    
    _ds_dataType = py.IIAPI_INTDS_TYPE
    _ds_length = py.IIAPI_INTDS_LEN


    def _allocate_buffer(self):
        ##  internal representation of INTERVAL DAY TO SECOND is:
        ##  i4  dn_days         # days component
        ##  i4  dn_seconds      # time component in seconds 
        ##  i4  dn_nseconds     # nanoseconds component 
        _fields_ = [
            ('days',ctypes.c_int),
            ('seconds',ctypes.c_int),
            ('nseconds',ctypes.c_int) ]
        INTERVAL_DS_BUFFER = Buffer_Factory(_fields_)
        buffer = INTERVAL_DS_BUFFER()
        return buffer

 
    def _get_python_value(self):
        '''return Ingres INTERVAL_DS as Python datetime.timedelta'''
        days = self._buffer.days
        seconds = self._buffer.seconds
        nseconds = self._buffer.nseconds
        microseconds = int(nseconds / 1000)
        v = dt.timedelta(days=days, seconds=seconds, microseconds=microseconds)
        return v


    def _value_setter(self,v):
        '''initialize the Ingres INTERVAL_DS instance'''

        if type(v) is dt.timedelta:
            self._buffer.days = v.days
            self._buffer.seconds = v.seconds
            self._buffer.nseconds = v.microseconds * 1000
        elif type(v) is str:
            self._conv_source.value = v
            format(self._conv_source,self)
        elif type(v) is Ingresdate:
            format(v,self)
        else:
            raise TypeError('must be str, Ingresdate, or datetime.timedelta')
            
            
class IIAPI_TIME_TYPE(IIAPI_TYPE_WITH_RESOLUTION):
    '''Ingres TIME WITH LOCAL TIME ZONE'''

    ##  don't be confused; the name of this class is IIAPI_TIME_TYPE but
    ##  it implements the Ingres TIME WITH LOCAL TIME ZONE type. (The 
    ##  IIAPI_TMWO_TYPE class implements the Ingres TIME type; see below)

    
    _ds_dataType = py.IIAPI_TIME_TYPE
    _ds_length = py.IIAPI_TIME_LEN

   
    def _allocate_buffer(self):
        ##  internal representation of TIME is:
        ##  i4  dn_seconds        # seconds since midnight
        ##  i4  dn_nsecond        # nanoseconds since last second
        ##  i1  dn_tzhour        # timezone hour component (-12 to 14)
        ##  i1  dn_tzminute        # timezone minute component (0-59)
        ##  See typedef struct _AD_TIME in ..\main\src\common\hdr\hdr\adudate.h

        ##  Note: dn_tzhour and dn_tzminute blur together. The low-order bit
        ##  of dn_tzhour is actually the high order bit of dn_tzminute. Also, 
        ##  DST is getting in on the act. Also I don't think tzhour is a
        ##  number of hours. One day I might take the time to
        ##  work out exactly what is going on with this... Till then, don't
        ##  take the timezone members too seriously

        _fields_ = [
            ('seconds',ctypes.c_int),
            ('nsecond',ctypes.c_int),
            ('tzhour',ctypes.c_ubyte),
            ('tzminute',ctypes.c_ubyte) ]
        TIME_BUFFER = Buffer_Factory(_fields_)
        buffer = TIME_BUFFER()
        return buffer


    def _get_python_value(self):
        '''return Ingres TIME WITH LOCAL TIMEZONE as python datetime.datetime'''

        ##  let the OpenAPI do the heavy lifting; get the time as an ISO format
        ##  string like '08:28:33.8610', respecting the declared precision,
        ##  then convert the string to a datetime.time
        s = self.formatted()

        ##  datetime.time can handle only TIME(0), TIME(3), and TIME(6); also 
        ##  anything more precise than TIME(6) *WILL* lose resolution
        ##  when returned as a datetime.time
        resolution = self.descriptor.ds_precision
        ##  pad with 0s
        s = s + '00'
        if resolution > 3:
            s = s[:15]
        elif resolution > 0:
            s = s[:12]
        else:
            s = s[:8]
        v = dt.time.fromisoformat(s)
        return v


    def _value_setter(self,v):
        '''initialize the Ingres TIME WITH LOCAL TIME ZONE instance'''

        ##  Because it is not clear how Ingres expects
        ##  dn_tzhour and dn_tzminute to be set to account for DST we rely 
        ##  on the IIapi_formatData() function to convert to the 
        ##  internal Ingres form

        if v is LOCAL_TIME:
            v = LOCAL_TIME()
        elif type(v) is dt.time:
            ##  datetime.time must be naive (no tzinfo)
            if v.tzinfo:
                raise ValueError('tzinfo not allowed')
            v = v.isoformat()
        elif type(v) is not str:
            raise TypeError('must be LOCAL_TIME, or a str or datetime.time')

        if v.lower() == 'now':
            v = LOCAL_TIME()

        self._conv_source.value = v
        format(self._conv_source,self)


class IIAPI_TMWO_TYPE(IIAPI_TIME_TYPE):
    '''Ingres TIME (naive, no timezone)'''

    
    _ds_dataType = py.IIAPI_TMWO_TYPE


    ##  that's all there is to it!

  
class IIAPI_TMTZ_TYPE(IIAPI_TIME_TYPE):
    '''Ingres TIME WITH TIME ZONE'''

    
    _ds_dataType = py.IIAPI_TMTZ_TYPE


    def _value_setter(self,v):
        '''initialize the Ingres TIME WITH LOCAL TIME ZONE instance'''

        ##  unlike the other time types, we do not allow the string 'now'
        ##  nor LOCAL_TIME as a value because they are not timezone-aware

        ##  Because it is not clear how Ingres expects
        ##  dn_tzhour and dn_tzminute to be set to account for DST we rely 
        ##  on the IIapi_formatData() function to convert to the 
        ##  internal Ingres form

        if v is CURRENT_TIME:
            v = CURRENT_TIME()
        elif type(v) is dt.time:
            v = v.isoformat()
        elif type(v) is not str:
            raise TypeError('must be str or datetime.time')

        self._conv_source.value = v
        format(self._conv_source,self)


    def _get_python_value(self):
        '''return Ingres TIME WITH TIME ZONE as python datetime.datetime'''

        ##  datetime.time.fromisoformat() is finnicky; see above

        s = self.formatted()
        ##  make provision for the timezone adjustment
        resolution = self.descriptor.ds_precision
        ##  parse out the timezone adjustment
        adjuster = s[-6]
        if adjuster not in {'+','-'}:
            raise RuntimeError('internal error; non-compliant TIME format')
        hms,adjustment = s.split(adjuster)
        ##  pad the time part then truncate to 0, 3, or 6 decimals
        hms = hms + '00'
        if resolution > 3:
            hms = hms[:15]
        elif resolution > 0:
            hms = hms[:12]
        else:
            hms = hms[:8]
        ##  reassemble the time string
        s = hms + adjuster + adjustment
        v = dt.time.fromisoformat(s)
        return v


class IIAPI_TS_TYPE(IIAPI_TYPE_WITH_RESOLUTION):
    '''Ingres TIMESTAMP WITH LOCAL TIME ZONE'''


    _ds_dataType = py.IIAPI_TS_TYPE
    _ds_length = py.IIAPI_TS_LEN
    _default_precision = 6


    def _allocate_buffer(self):
        ##  i2  dn_year         # year component (1-9999) 
        ##  i1  dn_month        # month component (1-12)
        ##  i1  dn_day            # day component (1-31)
        ##  i4  dn_seconds        # seconds since midnight
        ##  i4  dn_nsecond        # nanoseconds since last second
        ##  i1  dn_tzhour        # timezone hour component (-12 to 14)
        ##  i1  dn_tzminute     # timezone minute component (0-59)
        ##  See typedef struct _AD_TIMESTAMP in 
        ##  ..\main\src\common\hdr\hdr\adudate.h  See also comments
        ##  in IIAPI_TIME_TYPE about timezone members
        _fields_ = [
            ('year',ctypes.c_short),
            ('month',ctypes.c_ubyte),
            ('day',ctypes.c_ubyte),
            ('seconds',ctypes.c_int),
            ('nseconds',ctypes.c_int),
            ('tzhour',ctypes.c_ubyte),
            ('tzminute',ctypes.c_ubyte) ]
        TIMESTAMP_BUFFER = Buffer_Factory(_fields_)
        buffer = TIMESTAMP_BUFFER()
        return buffer


    def _get_python_value(self):
        '''return Ingres TIMESTAMP WITH LOCAL TIMEZONE as python dt.datetime'''

        ##  I haven't worked out how DST is encoded so 
        ##  let the OpenAPI do the heavy lifting; get the stamp as an ISO format
        ##  string like '2024-06-11 10:59:10.173570327', respecting the
        ##  declared scale, then convert the string to a datetime.datetime
        s = self.formatted()

        ##  datetime.datetime can handle only TIMESTAMP(0), TIMESTAMP(3), and
        ##  TIMESTAMP(6); also anything more precise than TIMESTAMP(6) *WILL*
        ##  lose resolution when returned as a datetime.datetime
        resolution = self.descriptor.ds_precision
        ##  pad with 0s
        s = s + '00'
        if resolution > 3:
            s = s[:26]
        elif resolution > 0:
            s = s[:23]
        else:
            s = s[:19]
        v = dt.datetime.fromisoformat(s)
        return v


    def _value_setter(self,v):
        '''initialize the Ingres TIMESTAMP WITH LOCAL TIME ZONE instance'''

        ##  Because it is not clear how Ingres expects
        ##  dn_tzhour and dn_tzminute to be set to account for DST we rely 
        ##  on the IIapi_formatData() function to convert to the 
        ##  internal Ingres form

        if v is LOCAL_TIMESTAMP:
            v = LOCAL_TIMESTAMP()
        elif type(v) is dt.datetime:
            ##  datetime.time must be naive (no tzinfo)
            if v.tzinfo:
                raise ValueError('tzinfo not allowed')
            v = v.isoformat()
        elif type(v) is not str:
            raise TypeError('must be LOCAL_TIMESTAMP, or a str or datetime.datetime')

        if v.lower() == 'now':
            v = LOCAL_TIMESTAMP()

        self._conv_source.value = v
        format(self._conv_source,self)


class IIAPI_TSWO_TYPE(IIAPI_TS_TYPE):
    '''Ingres TIMESTAMP (naive, no timezone)'''

    
    _ds_dataType = py.IIAPI_TSWO_TYPE


    ##  that's all there is to it!

 
class IIAPI_TSTZ_TYPE(IIAPI_TS_TYPE):
    '''Ingres TIMESTAMP WITH TIME ZONE'''

    
    _ds_dataType = py.IIAPI_TSTZ_TYPE


    def _get_python_value(self):
        '''return Ingres TIME WITH TIME ZONE as python datetime.datetime'''

        ##  datetime.datetime.fromisoformat() is finnicky; see above

        s = self.formatted()
        date,time = s.split(' ')
        ##  make provision for the timezone adjustment
        resolution = self.descriptor.ds_precision
        ##  parse out the timezone adjustment
        adjuster = time[-6]
        if adjuster not in {'+','-'}:
            raise RuntimeError('internal error; non-compliant TIMESTAMP format')
        hms,adjustment = time.split(adjuster)
        ##  pad the time part then truncate to 0, 3, or 6 decimals
        hms = hms + '00'
        if resolution > 3:
            hms = hms[:15]
        elif resolution > 0:
            hms = hms[:12]
        else:
            hms = hms[:8]
        ##  reassemble the timestamp string
        time = hms + adjuster + adjustment
        s = date + ' ' + time
        v = dt.datetime.fromisoformat(s)
        return v


    def _value_setter(self,v):
        '''initialize the Ingres TIMESTAMP WITH TIME ZONE instance'''

        ##  we do not allow LOCAL_TIMESTAMP as a value because it 
        ##  not timezone-aware

        ##  Because it is not clear how Ingres expects
        ##  dn_tzhour and dn_tzminute to be set to account for DST we rely 
        ##  on the IIapi_formatData() function to convert to the 
        ##  internal Ingres form

        if v is CURRENT_TIMESTAMP:
            v = CURRENT_TIMESTAMP()
        if type(v) is dt.datetime:
            v = v.isoformat()
        elif type(v) is not str:
            raise TypeError('must be str or datetime.datetime')

        self._conv_source.value = v
        format(self._conv_source,self)


##  ----------------------  IIAPI_TYPE_WITH_SCALE  ----------------------------


class IIAPI_DEC_TYPE(IIAPI_TYPE):
    '''Ingres DECIMAL'''


    ##  this type takes 3 positional arguments (value, precision, and scale)
    _expected_positionals = 3


    _ds_dataType = py.IIAPI_DEC_TYPE


    def _SQL_declaration(self):
        precision = self.descriptor.ds_precision
        scale = self.descriptor.ds_scale
        declaration = f'DECIMAL({precision},{scale})'
        return declaration


    def _allocate_conversion_buffers(self):
        '''preallocate conversion buffers'''

        self._conv_source = Char('',40)
        self._conv_target = Char('',40)


    def _get_ds_length(self,*args):
        '''infer the buffer size from the precision'''

        precision = self._get_ds_precision(*args)
        length = int(precision / 2) + 1
        return length


    def _get_ds_precision(self,*args):
        '''get the declared precision or infer it from the initial value'''

        try:
            precision = args[1]
        except IndexError:
            value = self._get_initial_value(*args)
            if type(value) is decimal.Decimal:
                precision = dec.getcontext().prec
            elif type(value) is float:
                precision = 15
            elif type(value) is int:
                precision = 19
            else:
                raise TypeError('not int, float, or decimal.Decimal')
        return precision


    def _get_ds_scale(self,*args):
        '''get the declared scale or default it to 0'''

        try:
            scale = args[2]
        except IndexError:
            scale = 0
        return scale


    def _validate_size(self):
        '''make sure precision and scale are within limits'''

        precision = self.descriptor.ds_precision
        scale = self.descriptor.ds_scale
        if not ( 0 < precision <= 39 ):
            raise OverflowError('precision cannot exceed 39')
        if not ( 0 <= scale <= precision ):
            raise OverflowError('scale cannot exceed precision')


    def _allocate_buffer(self):
        ds_length = self.descriptor.ds_length
        _fields_ =  [('value', ctypes.c_ubyte * ds_length)]
        DEC_BUFFER = Buffer_Factory(_fields_)
        buffer = DEC_BUFFER()
        return buffer


    def __repr__(self):
        classname = type(self).__qualname__
        value = self.formatted()
        precision = self.descriptor.ds_precision
        scale = self.descriptor.ds_scale
        modifier = self._reprfy_nullability()
        r = f'{package_name}.{classname}({value},{precision},{scale}{modifier})'
        return r


    def _get_python_value(self):
        '''return Ingres DECIMAL as a Python float'''

        ##  Each Ingres DECIMAL has its own scale and precision whereas
        ##  a Python decimal.Decimal has whatever is defined in the Decimal 
        ##  "context". We therefore return DECIMAL as a float to avoid the
        ##  the problem. This is consistent with embedded SQL in C

        s = self.formatted()
        v = float(s)
        return v
        

    def _value_setter(self,v):
        '''initialize Ingres DECIMAL instance'''

        ##  IIapi_formatData() is very rigid about precision and scale
        ##  so we need to go through some antics to make sure the supplied
        ##  value is in the form it demands. There are multiple possible 
        ##  approaches; I have decided to brute force it for now

        if type(v) not in {float, int, decimal.Decimal}:
            raise TypeError('not int, float, or decimal.Decimal')

        s = str(v)
        ##  break out the left- and right-of-decimal parts
        parts = s.split('.')
        lod = parts[0]
        if len(parts) == 2:
            rod = parts[1]
        else:
            rod = ''
        scale = self.descriptor.ds_scale
        ##  constrain the right-of-decimal part to scale
        rod = rod[:scale]
        ##  reassemble the value
        s = lod + '.' + rod
        ##  convert to DECIMAL
        self._conv_source.value = s
        format(self._conv_source,self)


    def formatted(self):
        '''return natively formatted value, respecting precision and scale'''

        format(self, self._conv_target)
        d = self._conv_target.value.strip()
        return d


##  ------------------------  IIAPI_LOCATOR_TYPE  ----------------------------


class IIAPI_LOCATOR_TYPE(IIAPI_TYPE_WITH_INTRINSIC_SIZE):
    '''large object (LOB) locator'''

    ##  LONG VARCHAR
    ##  LONG BYTE
    ##  LONG NVARCHAR

    _ds_length = py.IAPI_LOCATOR_LEN = 4    


    def _SQL_declaration(self):
        templates = {
            py.IIAPI_LCLOC_TYPE: '<LONG VARCHAR locator>',
            py.IIAPI_LBLOC_TYPE: '<LONG BYTE locator>',
            py.IIAPI_LNLOC_TYPE: '<LONG NVARCHAR locator>' }
        declaration = templates[type]
        return declaration



    ##  these types take no positional argument; only ever allocated using
    ##  a descriptor
    _expected_positionals = 0


    def _get_initial_value(self,*args):
        ##  cannot be initialized explicitly
        pass

    
    def _set(self,v):
        ##  cannot be set explicitly
        raise RuntimeError('a locator cannot be assigned a value')


    def _allocate_buffer(self):
        _fields_ = [
            ('locator',ctypes.c_int) ]
        LOCATOR_BUFFER = Buffer_Factory(_fields_)
        buffer = LOCATOR_BUFFER()
        return buffer


    def _get_python_value(self):
        '''return the locator as a Python int'''
        v = self._buffer.locator
        return v


class IIAPI_LCLOC_TYPE(IIAPI_LOCATOR_TYPE):
    '''Ingres LONG VARCHAR locator'''

    _ds_dataType = py.IIAPI_LCLOC_TYPE

    
class IIAPI_LBLOC_TYPE(IIAPI_LOCATOR_TYPE):
    '''Ingres LONG BYTE locator'''

    _ds_dataType = py.IIAPI_LBLOC_TYPE


class IIAPI_LNLOC_TYPE(IIAPI_LOCATOR_TYPE):
    '''Ingres LONG NVARCHAR locator'''

    _ds_dataType = py.IIAPI_LNLOC_TYPE


##  no need for nice aliases for locators
pass


##  --------------------  IIAPI_UNIMPLEMENTED_BLOB_TYPE  -----------------------


##  the following are Ingres BLOb types but we discourage their use in 
##  favour of using LOB locators instead, i.e. set 
##  qyp.qy_flags = py.IIAPI_QF_LOCATORS when calling IIapi_query().
##  Do feel free to override these with your own implementation if
##  you like hard work and ugly code

class IIAPI_LBYTE_TYPE():

    def __init__(self,*args,**kwargs):
        raise NotImplementedError('not supported; use LOB locators')

IIAPI_LNVCH_TYPE = IIAPI_LVCH_TYPE = IIAPI_LBYTE_TYPE


##  ----------------------------  nice aliases   -------------------------------


ANSIdate = IIAPI_DATE_TYPE
Boolean = IIAPI_BOOL_TYPE
Ingresdate = IIAPI_DTE_TYPE
Interval_YM = IIAPI_INTYM_TYPE
IPv4 = IIAPI_IPV4_TYPE
IPv6 = IIAPI_IPV6_TYPE
Money = IIAPI_MNY_TYPE
Object_Key = IIAPI_LOGKEY_TYPE 
Table_Key = IIAPI_TABKEY_TYPE 
UUID = IIAPI_UUID_TYPE
Byte = IIAPI_BYTE_TYPE
C = IIAPI_CHR_TYPE
Char = IIAPI_CHA_TYPE
Nchar = IIAPI_NCHA_TYPE
Nvarchar = IIAPI_NVCH_TYPE
Text = IIAPI_TXT_TYPE
Varbyte = IIAPI_VBYTE_TYPE
Varchar = IIAPI_VCH_TYPE
Real = Float4
Float = Double_Precision = Float8
Tinyint = Integer1 
Smallint = Integer2
Integer = Integer4
Bigint = Integer8
Interval_DS = IIAPI_INTDS_TYPE
Time = Time_WOTZ = IIAPI_TMWO_TYPE
Time_WLTZ = IIAPI_TIME_TYPE
Time_WTZ = IIAPI_TMTZ_TYPE
Timestamp = Timestamp_WOTZ = IIAPI_TSWO_TYPE
Timestamp_WLTZ = IIAPI_TS_TYPE
Timestamp_WTZ = IIAPI_TSTZ_TYPE
Decimal = Numeric = IIAPI_DEC_TYPE


##  ------------------------  allocator_for_type()  ----------------------------


def ____():
    '''bogus allocator to remind me what still needs doing'''
    raise NotImplementedError


def allocator_for_type(descriptor):
    allocator = {
        ##  the key is the Ingres type code and the value is the function used
        ##  to allocate the buffer for the Ingres value; see above
        py.IIAPI_BOOL_TYPE: IIAPI_BOOL_TYPE,
        py.IIAPI_BYTE_TYPE: IIAPI_BYTE_TYPE,
        py.IIAPI_CHA_TYPE: IIAPI_CHA_TYPE,
        py.IIAPI_CHR_TYPE: IIAPI_CHR_TYPE,
        py.IIAPI_DATE_TYPE: IIAPI_DATE_TYPE,
        py.IIAPI_DEC_TYPE: IIAPI_DEC_TYPE,
        py.IIAPI_DTE_TYPE: IIAPI_DTE_TYPE,
        py.IIAPI_FLT_TYPE: IIAPI_FLT_TYPE,
        py.IIAPI_INT_TYPE: IIAPI_INT_TYPE,
        py.IIAPI_INTDS_TYPE: IIAPI_INTDS_TYPE,
        py.IIAPI_INTYM_TYPE: IIAPI_INTYM_TYPE,
        py.IIAPI_IPV4_TYPE: IIAPI_IPV4_TYPE,
        py.IIAPI_IPV6_TYPE: IIAPI_IPV6_TYPE,
        py.IIAPI_LBLOC_TYPE: IIAPI_LBLOC_TYPE,
        py.IIAPI_LBYTE_TYPE: IIAPI_LBYTE_TYPE,      ## deprecated
        py.IIAPI_LCLOC_TYPE: IIAPI_LCLOC_TYPE,
        py.IIAPI_LNLOC_TYPE: IIAPI_LNLOC_TYPE,
        py.IIAPI_LNVCH_TYPE: IIAPI_LNVCH_TYPE,      ## deprecated
        py.IIAPI_LOGKEY_TYPE: IIAPI_LOGKEY_TYPE,
        py.IIAPI_LVCH_TYPE: IIAPI_LVCH_TYPE,        ## deprecated
        py.IIAPI_MNY_TYPE: IIAPI_MNY_TYPE,
        py.IIAPI_NCHA_TYPE: IIAPI_NCHA_TYPE,
        py.IIAPI_NVCH_TYPE: IIAPI_NVCH_TYPE,
        py.IIAPI_TABKEY_TYPE: IIAPI_TABKEY_TYPE,
        py.IIAPI_TIME_TYPE: IIAPI_TIME_TYPE,
        py.IIAPI_TMTZ_TYPE: IIAPI_TMTZ_TYPE,
        py.IIAPI_TMWO_TYPE: IIAPI_TMWO_TYPE,
        py.IIAPI_TS_TYPE: IIAPI_TS_TYPE,
        py.IIAPI_TSTZ_TYPE: IIAPI_TSTZ_TYPE,
        py.IIAPI_TSWO_TYPE: IIAPI_TSWO_TYPE,
        py.IIAPI_TXT_TYPE: IIAPI_TXT_TYPE,
        py.IIAPI_UUID_TYPE: IIAPI_UUID_TYPE,
        py.IIAPI_VBYTE_TYPE: IIAPI_VBYTE_TYPE,
        py.IIAPI_VCH_TYPE: IIAPI_VCH_TYPE,
        ##  -- the following are geospatial types
        py.IIAPI_GEOM_TYPE: ____,       # BLOb
        py.IIAPI_POINT_TYPE: ____,      # BLOb
        py.IIAPI_MPOINT_TYPE: ____,     # BLOb
        py.IIAPI_LINE_TYPE: ____,       # BLOb
        py.IIAPI_MLINE_TYPE: ____,      # BLOb
        py.IIAPI_POLY_TYPE: ____,       # BLOb
        py.IIAPI_MPOLY_TYPE: ____,      # BLOb
        py.IIAPI_NBR_TYPE: ____,        # BLOb
        py.IIAPI_GEOMC_TYPE: ____,      # BLOb
        py.IIAPI_CURVE_TYPE: ____,
        py.IIAPI_SURF_TYPE: ____,
        py.IIAPI_PSURF_TYPE: ____,
        py.IIAPI_GEOMZ_TYPE: ____,
        py.IIAPI_POINTZ_TYPE: ____,
        py.IIAPI_LINEZ_TYPE: ____,
        py.IIAPI_POLYZ_TYPE: ____,
        py.IIAPI_MPOINTZ_TYPE: ____,
        py.IIAPI_MLINEZ_TYPE: ____,
        py.IIAPI_MPOLYZ_TYPE: ____,
        py.IIAPI_GEOMCZ_TYPE: ____,
        py.IIAPI_CURVEZ_TYPE: ____,
        py.IIAPI_SURFZ_TYPE: ____,
        py.IIAPI_PSURFZ_TYPE: ____,
        py.IIAPI_GEOMM_TYPE: ____,
        py.IIAPI_POINTM_TYPE: ____,
        py.IIAPI_LINEM_TYPE: ____,
        py.IIAPI_POLYM_TYPE: ____,
        py.IIAPI_MPOINTM_TYPE: ____,
        py.IIAPI_MLINEM_TYPE: ____,
        py.IIAPI_MPOLYM_TYPE: ____,
        py.IIAPI_GEOMCM_TYPE: ____,
        py.IIAPI_CURVEM_TYPE: ____,
        py.IIAPI_SURFM_TYPE: ____,
        py.IIAPI_PSURFM_TYPE: ____,
        py.IIAPI_GEOMZM_TYPE: ____,
        py.IIAPI_POINTZM_TYPE: ____,
        py.IIAPI_LINEZM_TYPE: ____,
        py.IIAPI_POLYZM_TYPE: ____,
        py.IIAPI_MPOINTZM_TYPE: ____,
        py.IIAPI_MLINEZM_TYPE: ____,
        py.IIAPI_MPOLYZM_TYPE: ____,
        py.IIAPI_GEOMCZM_TYPE: ____,
        py.IIAPI_CURVEZM_TYPE: ____,
        py.IIAPI_SURFZM_TYPE: ____,
        py.IIAPI_PSURFZM_TYPE: ____,
        py.IIAPI_MCURVE_TYPE: ____,
        py.IIAPI_MSURF_TYPE: ____,
        py.IIAPI_MCURVEZ_TYPE: ____,
        py.IIAPI_MSURFZ_TYPE: ____,
        py.IIAPI_MCURVEM_TYPE: ____,
        py.IIAPI_MSURFM_TYPE: ____,
        py.IIAPI_MCURVEZM_TYPE: ____,
        py.IIAPI_MSURFZM_TYPE: ____,
        py.IIAPI_CSTR_TYPE: ____,
        py.IIAPI_CSTRZ_TYPE: ____,
        py.IIAPI_CSTRZM_TYPE: ____,
        py.IIAPI_CCURVE_TYPE: ____,
        py.IIAPI_CCURVEZ_TYPE: ____,
        py.IIAPI_CCURVEM_TYPE: ____,
        py.IIAPI_CCURVEZM_TYPE: ____,
        py.IIAPI_CPOLY_TYPE: ____,
        py.IIAPI_CPOLYZ_TYPE: ____,
        py.IIAPI_CPOLYM_TYPE: ____,
        py.IIAPI_CPOLYZM_TYPE: ____,
        py.IIAPI_TIN_TYPE: ____,
        py.IIAPI_TINZ_TYPE: ____,
        py.IIAPI_TINM_TYPE: ____,
        py.IIAPI_TINZM_TYPE: ____,
        py.IIAPI_TRI_TYPE: ____,
        py.IIAPI_TRIZ_TYPE: ____,
        py.IIAPI_TRIM_TYPE: ____,
        py.IIAPI_TRIZM_TYPE: ____,
        py.IIAPI_BOX_TYPE: ____,
        py.IIAPI_BOXZ_TYPE: ____ }

    return allocator[descriptor.ds_dataType]


## --------------------------- SQL Constants ---------------------------------

# these *probably* belong in the ingres module, not iitypes...
#USER
#CURRENT_USER
#SYSTEM_USER
#INITIAL_USER
#SESSION_USER
#SYSDATE

#if value is CURRENT_DATE:
#    return = CURRENT_DATE()
