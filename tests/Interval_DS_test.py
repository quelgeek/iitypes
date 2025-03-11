import pytest
import pyngres as py
import iitypes.standard as ii
import datetime

ii.publish_envHandle()

##  NB default precision of INTERVAL DAY TO SECOND is 0

def test_of_str_value_instantiation():
    i = ii.Interval_DS('7 6:54:32.123')
    assert i.value == datetime.timedelta(days=7, seconds=24872)

def test_of_Ingres_format_value_instantiation():
    i = ii.Interval_DS('23 days 5 hours 6 seconds')
    assert i.value == datetime.timedelta(days=23, seconds=18006)

def test_of_str_value_instantiation_default_precision():
    i = ii.Interval_DS('7 6:54:32.123')
    assert i.formatted() == '7 06:54:32'

def test_of_str_value_instantiation_0_precision():
    i = ii.Interval_DS('7 6:54:32.123',0)
    assert i.formatted() == '7 06:54:32'

def test_of_str_value_instantiation_intermediate_precision():
    i = ii.Interval_DS('7 6:54:32.123',2)
    assert i.formatted() == '7 06:54:32.12'

def test_of_repr():
    i = ii.Interval_DS('7 6:54:32.123',2)
    assert repr(i) == 'iitypes.types.IIAPI_INTDS_TYPE("7 06:54:32.12",2)' 

def test_of_timedelta_value_instantiation():
    interval = datetime.timedelta(days=40, seconds=2400, microseconds=0)
    i = ii.Interval_DS(interval,3)
    assert i.formatted() == '40 00:40:00.000'

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Interval_DS()
    assert str(e.value) == 'no initial value'

def test_of_str_value_assignment():
    i = ii.Interval_DS('7 6:54:32.123')
    i.value = '0 23:30:01.542'
    assert i.value == datetime.timedelta(seconds=84601)

def test_of_timedelta_value_assignment():
    i = ii.Interval_DS('7 6:54:32.123')
    i.value = datetime.timedelta(seconds=84601, microseconds=542000)
    assert i.formatted() == '0 23:30:01'

def test_of_Ingresdate_value_assignment():
    d = ii.Ingresdate('23 days 5 hours 6 seconds')
    i = ii.Interval_DS('7 6:54:32.123')
    i.value = d
    assert i.value == datetime.timedelta(days=23, seconds=18006)

def test_of_permitted_NULL_assignment():
    i = ii.Interval_DS('7 6:54:32.123',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_NULL_assignment_flagged_null():
    i = ii.Interval_DS('7 6:54:32.123',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.datavalue.dv_null == True

def test_of_disallowed_NULL_assignment():
    with pytest.raises(ValueError) as e:
        i = ii.Interval_DS('7 6:54:32.123',nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.Interval_DS(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.Interval_DS(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.Interval_DS(3.14)
    assert str(e.value) == 'must be str, Ingresdate, or datetime.timedelta'

def test_of_isoformat_checking():
    with pytest.raises(ValueError) as e:
        i = ii.Interval_DS('monkey business')
    assert str(e.value) == 'type conversion failed'

def test_of_extra_positional():
    with pytest.raises(RuntimeError) as e:
        i = ii.Interval_DS('7 6:54:32.123',0,'7 months')
    assert str(e.value) == 'too many arguments'

def test_of_poke():
    i = ii.Interval_DS('1 00:54:32.123',1)
    i._poke('0700000028610000c0d45407')
    assert i.formatted() == '7 06:54:32.1'

def test_of_user_assigned_name():
    i = ii.Interval_DS('7 6:54:32.123',name='weekish')
    assert i.descriptor.ds_columnName == b'weekish'

def test_of_readable_type_name():
    i = ii.Interval_DS('7 6:54:32.123',7)
    type_name = i.SQL_declaration
    assert type_name == 'INTERVAL DAY TO SECOND(7)'

def test_of_python_value_type():
    i = ii.Interval_DS('7 6:54:32.123')
    python_type = type(i.value)
    assert python_type is datetime.timedelta    
