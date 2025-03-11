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

def test_of_str_value_instantiation_default_precision():
    set_timezone('GMT')
    i = ii.Time_WLTZ('06:54:32.123')
    ##  default resolution is seconds
    assert i.formatted() == '06:54:32'

def test_of_repr():
    i = ii.Time_WLTZ('06:54:32.123',2)
    assert repr(i) == 'iitypes.types.IIAPI_TIME_TYPE("06:54:32.12",2)' 

def test_of_str_value_instantiation_0_precision():
    set_timezone('GMT')
    i = ii.Time_WLTZ('06:54:32.123',0)
    assert i.formatted() == '06:54:32'

def test_of_str_value_instantiation_intermediate_precision():
    set_timezone('GMT')
    i = ii.Time_WLTZ('06:54:32.123',2)
    assert i.formatted() == '06:54:32.12'

def test_of_time_value_instantiation():
    set_timezone('UNITED-KINGDOM')
    interval = datetime.time.fromisoformat('06:54:32.123')
    i = ii.Time_WLTZ(interval,3)
    assert i.formatted() == '06:54:32.123'

def test_of_disallowed_time_value_with_tzinfo():
    set_timezone('UNITED-KINGDOM')
    interval = datetime.time.fromisoformat('06:54:32.123+01:00')
    with pytest.raises(ValueError) as e:
        i = ii.Time_WLTZ(interval,3)
    assert str(e.value) == 'tzinfo not allowed'

def test_of_bare_instantiation():
    set_timezone('GMT')
    with pytest.raises(RuntimeError) as e:
        i = ii.Time_WLTZ()
    assert str(e.value) == 'no initial value'

def test_of_str_value_assignment():
    set_timezone('NA-MOUNTAIN')
    i = ii.Time_WLTZ('06:54:32.123')
    i.value = '23:30:01.542'
    assert i.value == datetime.time(23, 30, 1)

def test_of_time_value_assignment():
    set_timezone('GMT')
    i = ii.Time_WLTZ('06:54:32.123',9)
    i.value = datetime.time(23, 30, 1, 542000)
    assert i.formatted() == '23:30:01.542000000'

def test_of_timezone_display_adjustment():
    set_timezone('GMT')
    i = ii.Time_WLTZ('06:54:32.123',3)
    set_timezone('GMT-4')
    ##  note expected display is four hours earlier
    assert i.formatted() == '02:54:32.123'

def test_of_permitted_NULL_assignment():
    set_timezone('GMT')
    i = ii.Time_WLTZ('06:54:32.123',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_NULL_assignment_flagged_null():
    set_timezone('GMT')
    i = ii.Time_WLTZ('06:54:32.123',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.datavalue.dv_null == True

def test_of_disallowed_NULL_assignment():
    set_timezone('GMT')
    with pytest.raises(ValueError) as e:
        i = ii.Time_WLTZ('06:54:32.123',nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.Time_WLTZ(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.Time_WLTZ(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    set_timezone('GMT')
    with pytest.raises(TypeError) as e:
        i = ii.Time_WLTZ(3.14)
    assert str(e.value) == 'must be str or datetime.time'

def test_of_isoformat_checking():
    set_timezone('GMT')
    with pytest.raises(ValueError) as e:
        i = ii.Time_WLTZ('monkey business')
    assert str(e.value) == 'type conversion failed'

def test_of_extra_positional():
    set_timezone('GMT')
    with pytest.raises(RuntimeError) as e:
        i = ii.Time_WLTZ('06:54:32.123',0,'7 months')
    assert str(e.value) == 'too many arguments'

def test_of_poke():
    set_timezone('GMT')
    i = ii.Time_WLTZ('00:54:32.723',1)
    i._poke('0c7d00000027b9293c000000')
    assert i.formatted() == '08:53:32.7'

def test_of_user_assigned_name():
    set_timezone('GMT')
    i = ii.Time_WLTZ('06:54:32.123',name='risenshine')
    assert i.descriptor.ds_columnName == b'risenshine'

def test_of_readable_type_name():
    set_timezone('GMT')
    i = ii.Time_WLTZ('06:54:32.123',7)
    type_name = i.SQL_declaration
    assert type_name == 'TIME(7) WITH LOCAL TIME ZONE'

def test_of_python_value_type():
    set_timezone('GMT')
    i = ii.Time_WLTZ('06:54:32.123')
    python_type = type(i.value)
    assert python_type is datetime.time    
