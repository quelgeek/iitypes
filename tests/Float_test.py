import pytest
import pyngres as py
import iitypes.classic as ii

def test_of_FLOAT4_instantiation():
    i = ii.Float4(3.14)
    assert 3.139999 <= i.value <= 3.140001

def test_of_FLOAT4_repr():
    i = ii.Float4(3.1415926535897932384626433832795)
    assert repr(i) == 'iitypes.types.IIAPI_FLT_TYPE(3.1415927,4)' 

def test_of_FLOAT8_repr():
    i = ii.Float8(3.1415926535897932384626433832795)
    assert repr(i) == 'iitypes.types.IIAPI_FLT_TYPE(3.14159265358979,8)' 

def test_of_REAL_instantiation():
    i = ii.Real(3.14)
    assert 3.139999 <= i.value <= 3.140001

def test_of_FLOAT8_instantiation():
    i = ii.Float8(3.14)
    assert 3.13999999999 <= i.value <= 3.14000000001

def test_of_FLOAT_instantiation():
    i = ii.Float(3.14)
    assert 3.13999999999 <= i.value <= 3.14000000001

def test_of_DOUBLE_PRECISION_instantiation():
    i = ii.Double_Precision(3.14)
    assert 3.13999999999 <= i.value <= 3.14000000001

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Float4()
    ##  the error message is misleading in this case, but...pffffft
    assert str(e.value) == 'no size specified'

def test_of_REAL_value_assignment():
    i = ii.Real(0.0)
    i.value = 1
    assert 0.999999 <= i.value <= 1.000001

def test_of_permitted_NULL_assignment():
    i = ii.Float4(-1.0,nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_disallowed_NULL_assignment():
    with pytest.raises(ValueError) as e:
        i = ii.Float4(99.99,nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.Float4(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.Float4(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.Float4('monkey business')
    assert str(e.value) == 'not float or int'

def test_of_invalid_size():
    with pytest.raises(ValueError) as e:
        i = ii.Float8(3,55)
    assert str(e.value) == 'invalid size' 
    
def test_of_instantiation_from_descriptor():
    d = py.IIAPI_DESCRIPTOR()
    d.ds_dataType=py.IIAPI_FLT_TYPE    
    d.ds_nullable=1     
    d.ds_length=4
    d.ds_precision=0    
    d.ds_scale=0        
    d.ds_columnType=0   
    d.ds_columnName=None    
    i = ii.Float4(descriptor=d)
    assert i.datavalue.dv_value > 0
    
def test_of_poke():
    i = ii.Float4(0.)
    i._poke('0xc3f54840')
    assert 3.139999 <= i.value <= 3.140001

def test_of_poke_overflow_prevention():
    i = ii.Float4(3.14)
    i._poke('0x010101010101010101010101')
    assert i._peek() == '01010101'

def test_of_user_assigned_name():
    i = ii.Float4(36.65,name='temperature')
    assert i.descriptor.ds_columnName == b'temperature'

def test_of_readable_type_name():
    i = ii.Float4(36.65)
    type_name = i.SQL_declaration
    assert type_name == 'FLOAT4'

def test_of_python_value_type():
    i = ii.Float4(36.65)
    python_type = type(i.value)
    assert python_type is float
