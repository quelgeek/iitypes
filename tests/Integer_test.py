import pytest
import pyngres as py
import iitypes.standard as ii

def test_of_Integer1_instantiation():
    i = ii.Integer1(99)
    assert i.value == 99

def test_of_Tinyint_instantiation():
    i = ii.Tinyint(99)
    assert i.value == 99

def test_of_Integer2_instantiation():
    i = ii.Integer2(99)
    assert i.value == 99

def test_of_Smallint_instantiation():
    i = ii.Smallint(99)
    assert i.value == 99

def test_of_Integer4_instantiation():
    i = ii.Integer4(99)
    assert i.value == 99

def test_of_Integer_instantiation():
    i = ii.Integer(99)
    assert i.value == 99

def test_of_Integer8_instantiation():
    i = ii.Integer8(99)
    assert i.value == 99

def test_of_Bigint_instantiation():
    i = ii.Bigint(99)
    assert i.value == 99

def test_of_Tinyint_repr():
    i = ii.Tinyint(-65)
    assert repr(i) == 'iitypes.types.IIAPI_INT_TYPE(-65,1)'

def test_of_Smallint_repr():
    i = ii.Smallint(-65)
    assert repr(i) == 'iitypes.types.IIAPI_INT_TYPE(-65,2)'

def test_of_Integer_repr():
    i = ii.Integer(-65)
    assert repr(i) == 'iitypes.types.IIAPI_INT_TYPE(-65,4)'

def test_of_Bigint_repr():
    i = ii.Bigint(-65)
    assert repr(i) == 'iitypes.types.IIAPI_INT_TYPE(-65,8)'

def test_of_overflow_detection():
    with pytest.raises(OverflowError) as e:
        i = ii.Smallint(32768)
    assert e

def test_of_nagative_overflow_detection():
    with pytest.raises(OverflowError) as e:
        i = ii.Smallint(-32769)
    assert e

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Integer4()
    ##  the error message is misleading in this case, but...pffffft
    assert str(e.value) == 'no size specified'

def test_of_Integer_value_assignment():
    i = ii.Integer(0)
    i.value = 1
    assert i.value == 1

def test_of_permitted_NULL_assignment():
    i = ii.Integer4(-1,nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_disallowed_NULL_assignment():
    with pytest.raises(ValueError) as e:
        i = ii.Integer4(99,nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.Integer4(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.Integer4(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.Integer4('monkey business')
    assert str(e.value) == 'not int'

def test_of_invalid_size():
    with pytest.raises(ValueError) as e:
        i = ii.Integer8(3,55)
    assert str(e.value) == 'invalid size' 
    
def test_of_instantiation_from_descriptor():
    d = py.IIAPI_DESCRIPTOR()
    d.ds_dataType=py.IIAPI_INT_TYPE    
    d.ds_nullable=1     
    d.ds_length=1
    d.ds_precision=0    
    d.ds_scale=0        
    d.ds_columnType=0   
    d.ds_columnName=None    
    i = ii.Integer4(descriptor=d)
    assert i.datavalue.dv_value > 0
    
def test_of_poke():
    i = ii.Integer2(0)
    i._poke('0xd207')
    assert i.value == 2002

def test_of_poke_overflow_prevention():
    i = ii.Integer2(0)
    i._poke('0x010101010101010101010101')
    assert i._peek() == '0101'

def test_of_user_assigned_name():
    i = ii.Integer4(36,name='square')
    assert i.descriptor.ds_columnName == b'square'

def test_of_readable_type_name():
    i = ii.Integer8(36)
    type_name = i.SQL_declaration
    assert type_name == 'BIGINT'

def test_of_python_value_type():
    i = ii.Integer4(36)
    python_type = type(i.value)
    assert python_type is int
