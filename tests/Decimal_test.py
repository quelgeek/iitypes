import pytest
import pyngres as py
import iitypes.standard as ii
import datetime
import ctypes
import decimal

ii.publish_envHandle()

def test_of_DECIMAL_instantiation_no_precision_no_scale():
    i = ii.Decimal(3.14)
    assert 2.999999 <= i.value <= 3.000000

def test_of_repr():
    i = ii.Decimal(3.14159265358,5,4)
    assert repr(i) == "iitypes.types.IIAPI_DEC_TYPE(3.1415,5,4)"

def test_of_DECIMAL_instantiation_no_precision():
    i = ii.Decimal(3.14,5)
    assert i.formatted() == '3'

def test_of_DECIMAL_instantiation():
    i = ii.Decimal(3.14,5,4)
    assert i.formatted() == '3.1400'

def test_of_NUMERIC_instantiation():
    i = ii.Numeric(3.14,5,4)
    assert i.formatted() == '3.1400'

def test_of_scale_out_of_range():
    with pytest.raises(OverflowError) as e:
        i = ii.Numeric(3.14,5,6)
    assert str(e.value) == 'scale cannot exceed precision'

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Decimal()
    assert str(e.value) == 'no initial value'

def test_of_Integer_value_assignment():
    i = ii.Decimal(0.0,5,3)
    i.value = 1
    assert 0.999999 <= i.value <= 1.000001

def test_of_decimal_Decimal_value_assignment():
    i = ii.Decimal(0.0,5,4)
    i.value = decimal.Decimal(3.14)
    assert 3.1399 <= i.value <= 3.1401

def test_of_permitted_NULL_assignment():
    i = ii.Decimal(-1.0,20,10,nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_disallowed_NULL_assignment():
    with pytest.raises(ValueError) as e:
        i = ii.Decimal(99.99,4,2,nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.Decimal(ii.NULL,10,5,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.Decimal(ii.NULL,10,5,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.Decimal('monkey business',5,4)
    assert str(e.value) == 'not int, float, or decimal.Decimal'

def test_of_invalid_size():
    with pytest.raises(OverflowError) as e:
        i = ii.Decimal(3,55)
    assert str(e.value) == 'precision cannot exceed 39' 
    
def test_of_instantiation_from_descriptor():
    d = py.IIAPI_DESCRIPTOR()
    d.ds_dataType=py.IIAPI_DEC_TYPE    
    d.ds_nullable=1     
    d.ds_length=6
    d.ds_precision=10    
    d.ds_scale=5        
    d.ds_columnType=0   
    d.ds_columnName=None    
    i = ii.Decimal(descriptor=d)
    assert i.datavalue.dv_value > 0
    
def test_of_poke():
    i = ii.Decimal(0.,5,2)
    i._poke('00314c')
    assert 3.139999 <= i.value <= 3.140001

def test_of_poke_overflow_prevention():
    i = ii.Decimal(3.14,5,2)
    i._poke('0x010101010101010101010101')
    assert i._peek() == '010101'

def test_of_user_assigned_name():
    i = ii.Decimal(36.65,5,2,name='temperature')
    assert i.descriptor.ds_columnName == b'temperature'

def test_of_readable_type_name():
    i = ii.Decimal(36.65,5,2)
    type_name = i.SQL_declaration
    assert type_name == 'DECIMAL(5,2)'

def test_of_python_value_type():
    i = ii.Decimal(36.65)
    python_type = type(i.value)
    assert python_type is float
