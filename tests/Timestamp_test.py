import pytest
import pyngres as py
import iitypes.standard as ii
import datetime
import ctypes

##  NOTE: some of these tests require IANA timezone names and will throw
##  "RuntimeError: bad timezone name" when run using versions of the OpenAPI
##  that pre-date IANA support. Use Ingres 11.x or later for testing

ii.publish_envHandle()

##  NB default precision of TIMESTAMPs is 6

def set_timezone(t):
    '''set the timezone in the OpenAPI environment'''
    envHandle = ii.get_envHandle()
    timezone_name = t.encode()
    sep = py.IIAPI_SETENVPRMPARM()
    sep.se_envHandle = envHandle
    sep.se_paramID = py.IIAPI_EP_TIMEZONE
    timezone = ctypes.c_buffer(timezone_name)
    sep.se_paramValue = ctypes.addressof(timezone)
    py.IIapi_setEnvParam(sep)
    if sep.se_status != py.IIAPI_ST_SUCCESS:
        raise RuntimeError('bad timezone name')

def test_of_str_value_instantiation_default_precision():
    i = ii.Timestamp('2024-06-21 06:54:32.123')
    assert i.formatted() == '2024-06-21 06:54:32.123000'

def test_of_repr():
    i = ii.Timestamp('2024-06-21 06:54:32.123')
    assert repr(i) == 'iitypes.types.IIAPI_TSWO_TYPE("2024-06-21 06:54:32.123000",6)'

def test_of_str_value_instantiation_0_precision():
    i = ii.Timestamp('2024-06-21 06:54:32.123',0)
    assert i.formatted() == '2024-06-21 06:54:32'

def test_of_str_value_instantiation_intermediate_precision():
    i = ii.Timestamp('2024-06-21 06:54:32.123',2)
    assert i.formatted() == '2024-06-21 06:54:32.12'

def test_of_LOCAL_TIMESTAMP_instantiation():
    i = ii.Timestamp(ii.LOCAL_TIMESTAMP)
    assert type(i.value) is datetime.datetime

def test_of_NOW_instantiation():
    i = ii.Timestamp('now')
    assert type(i.value) is datetime.datetime

def test_of_Ingres_format_value_instantiation():
    i = ii.Timestamp('21-jun-2024 06:54:32.123')
    assert i.value == datetime.datetime(2024, 6, 21, 6, 54, 32, 123000)

def test_of_time_value_instantiation():
    interval = datetime.datetime.fromisoformat('2024-06-21 06:54:32.123')
    i = ii.Timestamp(interval,3)
    assert i.formatted() == '2024-06-21 06:54:32.123'

def test_of_disallowed_time_value_with_tzinfo():
    interval = datetime.datetime.fromisoformat('2024-06-21 06:54:32.123+01:00')
    with pytest.raises(ValueError) as e:
        i = ii.Timestamp(interval,3)
    assert str(e.value) == 'tzinfo not allowed'

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Timestamp()
    assert str(e.value) == 'no initial value'

def test_of_str_value_assignment():
    i = ii.Timestamp('2024-06-21 06:54:32.123')
    i.value = '2024-06-21 23:30:01.542'
    assert i.value == datetime.datetime(2024, 6, 21, 23, 30, 1, 542000)

def test_of_time_value_assignment():
    i = ii.Timestamp('2024-06-21 06:54:32.123')
    i.value = datetime.datetime(2024, 6, 21, 23, 30, 1, 542000)
    assert i.formatted() == '2024-06-21 23:30:01.542000'

def test_of_timezone_invariance():
    set_timezone('NA-MOUNTAIN')
    i = ii.Timestamp('2024-06-21 06:54:32.123')
    set_timezone('UNITED-KINGDOM')
    assert i.formatted() == '2024-06-21 06:54:32.123000'

def test_of_permitted_NULL_assignment():
    i = ii.Timestamp('2024-06-21 06:54:32.123',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_NULL_assignment_flagged_null():
    i = ii.Timestamp('2024-06-21 06:54:32.123',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.datavalue.dv_null == True

def test_of_disallowed_NULL_assignment():
    with pytest.raises(ValueError) as e:
        i = ii.Timestamp('2024-06-21 06:54:32.123',nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.Timestamp(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.Timestamp(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.Timestamp(3.14)
    assert str(e.value) == 'must be LOCAL_TIMESTAMP, or a str or datetime.datetime'

def test_of_isoformat_checking():
    with pytest.raises(ValueError) as e:
        i = ii.Timestamp('monkey business')
    assert str(e.value) == 'type conversion failed'

def test_of_extra_positional():
    with pytest.raises(RuntimeError) as e:
        i = ii.Timestamp('2024-06-21 06:54:32.123',0,'7 months')
    assert str(e.value) == 'too many arguments'

def test_of_poke():
    i = ii.Timestamp('2024-06-21 06:54:32.123',1)
    i._poke('e8070615794a010080434e203c000000')
    assert i.formatted() == '2024-06-21 23:30:01.5'

def test_of_user_assigned_name():
    i = ii.Timestamp('2024-06-21 06:54:32.123',name='solstice')
    assert i.descriptor.ds_columnName == b'solstice'

def test_of_readable_type_name():
    i = ii.Timestamp('2024-06-21 06:54:32.123',7)
    type_name = i.SQL_declaration
    assert type_name == 'TIMESTAMP(7)'

def test_of_python_value_type():
    i = ii.Timestamp('2024-06-21 06:54:32.123')
    python_type = type(i.value)
    assert python_type is datetime.datetime    
