import pytest
import pyngres as py
import iitypes.standard as ii
import datetime


def test_of_str_value_instantiation():
    i = ii.ANSIdate('1960-01-11')
    assert i.value == datetime.date(1960,1,11)

def test_of_repr():
    ii.publish_envHandle()
    i = ii.ANSIdate('1960-01-11',nullable=ii.WITHNULL)
    assert repr(i) == "iitypes.types.IIAPI_DATE_TYPE('1960-01-11',nullable=iitypes.types.WITHNULL)"

def test_of_datetime_value_instantiation():
    date = datetime.date(1994,5,15)
    i = ii.ANSIdate(date)
    assert i.value == date

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.ANSIdate()
    assert str(e.value) == 'no initial value'

def test_of_str_value_assignment():
    i = ii.ANSIdate('1960-01-11')
    i.value = '1984-06-16'
    assert i.value == datetime.date(1984,6,16)

def test_of_CURRENT_DATE_value_assignment():
    i = ii.ANSIdate(ii.CURRENT_DATE)
    assert type(i.value) is datetime.date

def test_of_TODAY_value_assignment():
    i = ii.ANSIdate('TODAY')
    assert type(i.value) is datetime.date

def test_of_date_value_assignment():
    i = ii.ANSIdate('1960-01-11')
    i.value = datetime.date(1984,6,16)
    assert str(i) == '1984-06-16'

def test_of_permitted_NULL_assignment():
    i = ii.ANSIdate('1960-01-11',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_NULL_assignment_flagged_null():
    i = ii.ANSIdate('1960-01-11',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.datavalue.dv_null == True

def test_of_disallowed_NULL_assignment():
    with pytest.raises(ValueError) as e:
        i = ii.ANSIdate('1960-01-11',nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.ANSIdate(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.ANSIdate(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.ANSIdate(3.14)
    assert str(e.value) == 'must be CURRENT_DATE, a str, or a datetime.date'

def test_of_isoformat_checking():
    with pytest.raises(ValueError) as e:
        i = ii.ANSIdate('monkey business')
    assert str(e.value) == "Invalid isoformat string: 'monkey business'"

def test_of_single_positional():
    with pytest.raises(RuntimeError) as e:
        i = ii.ANSIdate('2001-01-13',datetime.date.today())
    assert str(e.value) == 'too many arguments'

def test_of_poke():
    i = ii.ANSIdate('1960-01-11')
    i._poke('D6070A18')
    assert str(i) == '2006-10-24'

def test_of_user_assigned_name():
    i = ii.ANSIdate('1960-01-11',name='today')
    assert i.descriptor.ds_columnName == b'today'

def test_of_readable_type_name():
    i = ii.ANSIdate('1960-01-11')
    type_name = i.SQL_declaration
    assert type_name == 'ANSIDATE'

def test_of_python_value_type():
    i = ii.ANSIdate('1960-01-11')
    python_type = type(i.value)
    assert python_type is datetime.date    
