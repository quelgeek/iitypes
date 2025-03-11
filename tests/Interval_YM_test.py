import pytest
import pyngres as py
import iitypes.standard as ii
import datetime

ii.publish_envHandle()

def test_of_repr():
    i = ii.Interval_YM('1960-01')
    assert repr(i) == "iitypes.types.IIAPI_INTYM_TYPE('1960-01')"

def test_of_str_value_instantiation():
    i = ii.Interval_YM('1960-01')
    assert i.value == (1960,1)

def test_of_tuple_value_instantiation():
    i = ii.Interval_YM((2300,3))
    assert i.value == (2300,3)

def test_of_timedelta_value_instantiation():
    ##  NB this is only a test that we get the expected value, not
    ##  a test of the correctness of the rendering of the timedelta;
    ##  timedelta is an imperfect match for Interval_YM
    delta = datetime.timedelta(days=183, seconds=29156, microseconds=10)
    i = ii.Interval_YM(delta)
    assert i.value == (0,6)

def test_of_timedelta_value_instantiation_formatted():
    delta = datetime.timedelta(days=183, seconds=29156, microseconds=10)
    i = ii.Interval_YM(delta)
    assert i.formatted() == '0-06'

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Interval_YM()
    assert str(e.value) == 'no initial value'

def test_of_str_value_assignment():
    i = ii.Interval_YM('1960-01')
    i.value = '1984-06'
    assert i.value == (1984,6)

def test_of_timedelta_value_assignment():
    i = ii.Interval_YM('1960-01')
    delta = datetime.timedelta(days=183, seconds=29156, microseconds=10)
    i.value = delta
    assert i.value == (0,6)

def test_of_Ingresdate_value_assignment():
    ##  note: this operation is subject to the same odd behaviour Ingres
    ##  demonstrates. 190 days is not treated as 6 months so the result
    ##  comes back as (0,0) instead of (0,6)
    d = ii.Ingresdate('6 months 5 hours 6 seconds')
    i = ii.Interval_YM('1960-01')
    i.value = d
    assert i.value == (0,6)

def test_of_permitted_NULL_assignment():
    i = ii.Interval_YM('1960-01',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_NULL_assignment_flagged_null():
    i = ii.Interval_YM('1960-01',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.datavalue.dv_null == True

def test_of_disallowed_NULL_assignment():
    with pytest.raises(ValueError) as e:
        i = ii.Interval_YM('1960-01',nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.Interval_YM(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.Interval_YM(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.Interval_YM(3.14)
    assert str(e.value) == 'must be tuple, str, Ingresdate, or datetime.timedelta'

def test_of_format_checking():
    with pytest.raises(ValueError) as e:
        i = ii.Interval_YM('monkey business')
    assert str(e.value) == "type conversion failed"

def test_of_single_positional():
    with pytest.raises(RuntimeError) as e:
        i = ii.Interval_YM('2001-01-13',datetime.date.today())
    assert str(e.value) == 'too many arguments'

def test_of_poke():
    i = ii.Interval_YM('1960-01')
    i._poke('090701')
    assert i.value == (1801,1)

def test_of_user_assigned_name():
    i = ii.Interval_YM('1960-01',name='ages')
    assert i.descriptor.ds_columnName == b'ages'

def test_of_readable_type_name():
    i = ii.Interval_YM('1960-01')
    type_name = i.SQL_declaration
    assert type_name == 'INTERVAL YEAR TO MONTH'

def test_of_python_value_type():
    i = ii.Interval_YM('1960-01')
    python_type = type(i.value)
    assert python_type is tuple
