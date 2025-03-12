import pytest
import pyngres as py
import iitypes.standard as ii
import datetime
import ctypes

ii.publish_envHandle()

##  NB default precision of TIME is 0

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
    i = ii.Time('06:54:32.123')
    assert i.formatted() == '06:54:32'

def test_of_repr():
    i = ii.Time('06:54:32.123',2)
    assert repr(i) == 'iitypes.types.IIAPI_TMWO_TYPE("06:54:32.12",2)' 

def test_of_str_value_instantiation_0_precision():
    i = ii.Time('06:54:32.123',0)
    assert i.formatted() == '06:54:32'

def test_of_str_value_instantiation_intermediate_precision():
    i = ii.Time('06:54:32.123',2)
    assert i.formatted() == '06:54:32.12'

def test_of_LOCAL_TIME_instantiation():
    i = ii.Time(ii.LOCAL_TIME)
    assert type(i.value) is datetime.time

def test_of_NOW_instantiation():
    i = ii.Time('now')
    assert type(i.value) is datetime.time

def test_of_time_value_instantiation():
    interval = datetime.time.fromisoformat('06:54:32.123')
    i = ii.Time(interval,3)
    assert i.formatted() == '06:54:32.123'

def test_of_disallowed_time_value_with_tzinfo():
    interval = datetime.time.fromisoformat('06:54:32.123+01:00')
    with pytest.raises(ValueError) as e:
        i = ii.Time(interval,3)
    assert str(e.value) == 'tzinfo not allowed'

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Time()
    assert str(e.value) == 'no initial value'

def test_of_str_value_assignment():
    i = ii.Time('06:54:32.123')
    i.value = '23:30:01.542'
    assert i.value == datetime.time(23, 30, 1)

def test_of_time_value_assignment():
    i = ii.Time('06:54:32.123')
    i.value = datetime.time(23, 30, 1, 542000)
    assert i.formatted() == '23:30:01'

def test_of_timezone_invariance():
    set_timezone('NA-MOUNTAIN')
    i = ii.Time('06:54:32.123')
    set_timezone('UNITED-KINGDOM')
    assert i.formatted() == '06:54:32'

def test_of_permitted_NULL_assignment():
    i = ii.Time('06:54:32.123',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_NULL_assignment_flagged_null():
    i = ii.Time('06:54:32.123',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.datavalue.dv_null == True

def test_of_disallowed_NULL_assignment():
    with pytest.raises(ValueError) as e:
        i = ii.Time('06:54:32.123',nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.Time(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.Time(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.Time(3.14)
    assert str(e.value) == 'must be LOCAL_TIME, or a str or datetime.time'

def test_of_isoformat_checking():
    with pytest.raises(ValueError) as e:
        i = ii.Time('monkey business')
    assert str(e.value) == 'type conversion failed'

def test_of_extra_positional():
    with pytest.raises(RuntimeError) as e:
        i = ii.Time('06:54:32.123',0,'7 months')
    assert str(e.value) == 'too many arguments'

def test_of_poke():
    i = ii.Time('00:54:32.123',1)
    i._poke('28610000C0D454073C00')
    assert i.formatted() == '06:54:32.1'

def test_of_user_assigned_name():
    i = ii.Time('06:54:32.123',name='risenshine')
    assert i.descriptor.ds_columnName == b'risenshine'

def test_of_readable_type_name():
    i = ii.Time('06:54:32.123',7)
    type_name = i.SQL_declaration
    assert type_name == 'TIME(7)'

def test_of_python_value_type():
    i = ii.Time('06:54:32.123')
    python_type = type(i.value)
    assert python_type is datetime.time    
