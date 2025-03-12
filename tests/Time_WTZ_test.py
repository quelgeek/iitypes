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
    i = ii.Time_WTZ('06:54:32.123')
    ##  default resolution is a second
    assert i.formatted() == '06:54:32+00:00'

def test_of_repr():
    set_timezone('GMT')
    i = ii.Time_WTZ('06:54:32.123',5)
    assert repr(i) == 'iitypes.types.IIAPI_TMTZ_TYPE("06:54:32.12300+00:00",5)'

def test_of_str_value_instantiation_0_precision():
    set_timezone('US-HAWAII')
    i = ii.Time_WTZ('06:54:32.123',0)
    assert i.formatted() == '06:54:32-10:00'

def test_of_str_value_instantiation_intermediate_precision():
    set_timezone('GMT1')
    i = ii.Time_WTZ('06:54:32.123',2)
    assert i.formatted() == '06:54:32.12+01:00'

def test_of_CURRENT_TIME_instantiation():
    i = ii.Time_WTZ(ii.CURRENT_TIME)
    assert type(i.value) is datetime.time

def test_of_NOW_disallowed():
    with pytest.raises(ValueError) as e:
        i = ii.Time_WTZ('now')
    assert str(e.value) == 'type conversion failed'

def test_of_time_value_instantiation():
    set_timezone('UNITED-KINGDOM')
    time_of_day = datetime.time.fromisoformat('06:54:32.123+04:00')
    i = ii.Time_WTZ(time_of_day,3)
    assert i.formatted() == '06:54:32.123+04:00'

def test_of_bare_instantiation():
    set_timezone('SAUDI-ARABIA')
    with pytest.raises(RuntimeError) as e:
        i = ii.Time_WTZ()
    assert str(e.value) == 'no initial value'

def test_of_str_value_assignment():
    set_timezone('GMT-6')
    i = ii.Time_WTZ('06:54:32.123')
    i.value = '23:30:01.542'
    assert i.value == datetime.time(23, 30, 1, 
        tzinfo=datetime.timezone(datetime.timedelta(days=-1, seconds=64800)))

def test_of_time_value_assignment():
    set_timezone('GMT')
    i = ii.Time_WTZ('06:54:32.123+01:00')
    i.value = datetime.time(23, 30, 1, 542000,
        tzinfo=datetime.timezone(datetime.timedelta(seconds=7200)))
    assert i.formatted() == '23:30:01+02:00'

def test_of_permitted_NULL_assignment():
    set_timezone('GMT')
    i = ii.Time_WTZ('06:54:32.123',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_NULL_assignment_flagged_null():
    set_timezone('GMT')
    i = ii.Time_WTZ('06:54:32.123',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.datavalue.dv_null == True

def test_of_disallowed_NULL_assignment():
    set_timezone('GMT')
    with pytest.raises(ValueError) as e:
        i = ii.Time_WTZ('06:54:32.123',nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.Time_WTZ(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.Time_WTZ(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    set_timezone('GMT')
    with pytest.raises(TypeError) as e:
        i = ii.Time_WTZ(3.14)
    assert str(e.value) == 'must be str or datetime.time'

def test_of_isoformat_checking():
    set_timezone('GMT')
    with pytest.raises(ValueError) as e:
        i = ii.Time_WTZ('monkey business')
    assert str(e.value) == 'type conversion failed'

def test_of_extra_positional():
    set_timezone('GMT')
    with pytest.raises(RuntimeError) as e:
        i = ii.Time_WTZ('06:54:32.123',0,'7 months')
    assert str(e.value) == 'too many arguments'

def test_of_poke():
    set_timezone('GMT-5')
    i = ii.Time_WTZ('00:54:32.723',1)
    i._poke('f32301000027b9293ad40000')
    assert i.formatted() == '15:45:39.7-05:00'

def test_of_user_assigned_name():
    set_timezone('GMT')
    i = ii.Time_WTZ('06:54:32.123',name='risenshine')
    assert i.descriptor.ds_columnName == b'risenshine'

def test_of_readable_type_name():
    set_timezone('GMT')
    i = ii.Time_WTZ('06:54:32.123',7)
    type_name = i.SQL_declaration
    assert type_name == 'TIME(7) WITH TIME ZONE'

def test_of_python_value_type():
    set_timezone('GMT')
    i = ii.Time_WTZ('06:54:32.123')
    python_type = type(i.value)
    assert python_type is datetime.time    
