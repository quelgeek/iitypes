import ctypes
import pytest
import pyngres as py
import iitypes.standard as ii
import datetime

ii.publish_envHandle()

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

##  potentially DST-dependent; some tests might wrongly fail; I might fix them

def test_of_str_value_instantiation_default_precision():
    set_timezone('GMT')
    i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123')
    ##  default resolution is microseconds
    assert i.formatted() == '2024-06-21 06:54:32.123000+00:00'

def test_of_repr():
    set_timezone('GMT')
    i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123')
    ##  default resolution is microseconds
    assert repr(i) == 'iitypes.types.IIAPI_TSTZ_TYPE("2024-06-21 06:54:32.123000+00:00",6)'

def test_of_str_value_instantiation_0_precision():
    set_timezone('NA-MOUNTAIN')
    i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123',0)
    assert i.formatted() == '2024-06-21 06:54:32-06:00'

def test_of_str_value_instantiation_intermediate_precision():
    set_timezone('MEXICO-BAJANORTE')
    i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123',2)
    assert i.formatted() == '2024-06-21 06:54:32.12-07:00'

def test_of_time_value_instantiation():
    set_timezone('UNITED-KINGDOM')
    time_of_day = datetime.datetime.fromisoformat('2024-06-21 06:54:32.123+04:00')
    i = ii.Timestamp_WTZ(time_of_day,3)
    assert i.formatted() == '2024-06-21 06:54:32.123+04:00'

def test_of_bare_instantiation():
    set_timezone('SAUDI-ARABIA')
    with pytest.raises(RuntimeError) as e:
        i = ii.Timestamp_WTZ()
    assert str(e.value) == 'no initial value'

def test_of_str_value_assignment():
    set_timezone('NA-MOUNTAIN')
    i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123')
    i.value = '1997-06-27 06:54:32.534'
    assert i.value == datetime.datetime(1997, 6, 27, 6, 54, 32, 534000,
        tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=64800)))

def test_of_time_value_assignment():
    set_timezone('AUSTRALIA-QUEENSLAND')
    i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123+01:00',4)
    i.value = datetime.datetime(2024, 6, 21, 6, 54, 32, 123000,
        tzinfo=datetime.timezone(datetime.timedelta(seconds=3600)))
    assert i.formatted() == '2024-06-21 06:54:32.1230+01:00'

def test_of_permitted_NULL_assignment():
    set_timezone('GMT')
    i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123+01:00',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_NULL_assignment_flagged_null():
    set_timezone('GMT')
    i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123+01:00',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.datavalue.dv_null == True

def test_of_disallowed_NULL_assignment():
    set_timezone('GMT')
    with pytest.raises(ValueError) as e:
        i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123+01:00',
            nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.Timestamp_WTZ(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.Timestamp_WTZ(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    set_timezone('GMT')
    with pytest.raises(TypeError) as e:
        i = ii.Timestamp_WTZ(3.14)
    assert str(e.value) == 'must be str or datetime.datetime'

def test_of_isoformat_checking():
    set_timezone('GMT')
    with pytest.raises(ValueError) as e:
        i = ii.Timestamp_WTZ('monkey business')
    assert str(e.value) == 'type conversion failed'

def test_of_extra_positional():
    set_timezone('GMT')
    with pytest.raises(RuntimeError) as e:
        i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123+01:00',0,'7 months')
    assert str(e.value) == 'too many arguments'

def test_of_poke():
    set_timezone('GMT-5')
    i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123+01:00',1)
    i._poke('d107010bf32301000027b9293ad40000')
    assert i.formatted() == '2001-01-11 15:45:39.7-05:00'

def test_of_user_assigned_name():
    set_timezone('GMT')
    i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123+01:00',name='risenshine')
    assert i.descriptor.ds_columnName == b'risenshine'

def test_of_readable_type_name():
    set_timezone('GMT')
    i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123+01:00',7)
    type_name = i.SQL_declaration
    assert type_name == 'TIMESTAMP(7) WITH TIME ZONE'

def test_of_python_value_type():
    set_timezone('GMT')
    i = ii.Timestamp_WTZ('2024-06-21 06:54:32.123+01:00')
    python_type = type(i.value)
    assert python_type is datetime.datetime    
