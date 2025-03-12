import pytest
import pyngres as py
import iitypes as ii
import datetime

def test_envHandle_set():
    ##  Suppress this test if the envHandle is set (by some previous test)
    envHandle = ii.get_envHandle()
    if envHandle:
        assert True
    else:
        with pytest.raises(RuntimeError) as e:
            i = ii.Ingresdate('01-jan-1960')
        assert str(e.value) == '_envHandle not set; call publish_envHandle()'    

def test_of_date_repr():
    ii.publish_envHandle()
    i = ii.Ingresdate('01-jan-1960')
    assert repr(i) == "iitypes.types.IIAPI_DTE_TYPE('01-jan-1960')"

def test_of_str_value_instantiation():
    ii.publish_envHandle()  
    i = ii.Ingresdate('11-jan-1960')
    assert i.value == datetime.date(1960,1,11)
    
def test_of_TODAY_instantiation():
    ii.publish_envHandle()  
    i = ii.Ingresdate('today')
    assert type(i.value) is datetime.date
    
def test_of_NOW_insantiation():
    ii.publish_envHandle()  
    i = ii.Ingresdate('now')
    assert type(i.value) is datetime.datetime
    
def test_of_formatted_display():
    ii.publish_envHandle()  
    i = ii.Ingresdate('11/01/1960')
    ##  assuming II_DATE_FORMAT=US
    assert i.formatted() == '01-nov-1960' 

def test_of_user_assigned_name():
    ii.publish_envHandle()  
    i = ii.Ingresdate('today',name='today')
    assert i.descriptor.ds_columnName == b'today'

def test_of_readable_type_name():
    ii.publish_envHandle()  
    i = ii.Ingresdate('TODAY')
    type_name = i.SQL_declaration
    assert type_name == 'INGRESDATE'

def test_of_absolute_date_as_python_value_type():
    ii.publish_envHandle()  
    i = ii.Ingresdate('today')
    python_type = type(i.value)
    assert python_type is datetime.date

def test_of_invalid_string_conversion_checking():
    ii.publish_envHandle()  
    with pytest.raises(ValueError) as e:
        i = ii.Ingresdate('monkey business')
    assert str(e.value) == 'type conversion failed'

def test_of_poke():
    ii.publish_envHandle()  
    i = ii.Ingresdate('')
    i._poke('1D00E8070600030000000000')
    assert i.value == datetime.date(2024, 6, 3)

def test_of_poke_overflow_prevention():
    ii.publish_envHandle()  
    i = ii.Ingresdate('')
    i._poke('1D00E8070600030000000000727269616765')
    assert i.value == datetime.date(2024, 6, 3)

def test_of_date_with_time_as_python_value_type():
    ii.publish_envHandle()  
    i = ii.Ingresdate('now')
    python_type = type(i.value)
    assert python_type is datetime.datetime

def test_of_interval_as_python_value_type():
    ii.publish_envHandle()  
    i = ii.Ingresdate('10 hours 1 minute 42 seconds')
    python_type = type(i.value)
    assert python_type is datetime.timedelta

def test_of_interval_repr():
    ii.publish_envHandle()
    i = ii.Ingresdate('10 hours 1 minute 42 seconds')
    assert repr(i) == "iitypes.types.IIAPI_DTE_TYPE('10 hrs 1 mins 42 secs')"

    
