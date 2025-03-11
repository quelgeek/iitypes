import pytest
import pyngres as py
import iitypes.standard as ii

def test_of_True_instantiation():
    i = ii.Boolean(True)
    assert i.value == True

def test_of_repr():
    i = ii.Boolean(True)
    assert repr(i) == 'iitypes.types.IIAPI_BOOL_TYPE(True)'

def test_of_False_instantiation():
    i = ii.Boolean(False)
    assert i.value == False

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Boolean()
    assert str(e.value) == 'no initial value'

def test_of_value_assignment():
    i = ii.Boolean(False)
    i.value = 1
    assert i.value == True

def test_of_permitted_NULL_assignment():
    i = ii.Boolean(False,nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_disallowed_NULL_assignment():
    with pytest.raises(ValueError) as e:
        i = ii.Boolean(False,nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.Boolean(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.Boolean(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_value_when_NULL():
    i = ii.Boolean(ii.NULL,nullable=ii.WITHNULL)
    v = i.value
    assert v is None

def test_of_0_as_False():
    i = ii.Boolean(0)
    assert i.value == False

def test_of_1_as_True():
    i = ii.Boolean(1)
    assert i.value == True

def test_of_formatted_display():
    i = ii.Boolean(True)
    assert i.formatted() == 'TRUE'

def test_of_domain_checking():
    with pytest.raises(ValueError) as e:
        i = ii.Boolean('monkey business')
    assert str(e.value) == 'must be True or False'

def test_of_spurious_positional():
    with pytest.raises(RuntimeError) as e:
        i = ii.Boolean(True,False)
    assert str(e.value) == 'too many arguments'
    
def test_of_instantiation_from_descriptor():
    d = py.IIAPI_DESCRIPTOR()
    d.ds_dataType=py.IIAPI_BOOL_TYPE    
    d.ds_nullable=1     
    d.ds_length=py.IIAPI_BOOL_LEN       
    d.ds_precision=0    
    d.ds_scale=0        
    d.ds_columnType=0   
    d.ds_columnName=None    
    i = ii.Boolean(descriptor=d)
    assert i.datavalue.dv_value > 0
    
def test_of_poke():
    i = ii.Boolean(False)
    i._poke('0x3F')     ##  garbage value to poke, but poke is allowed to
    assert i._peek() == '3f'

def test_of_poke_overflow_prevention():
    i = ii.Boolean(False)
    i._poke('0x010101010101010101010101')
    assert i._peek() == '01'

def test_of_user_assigned_name():
    i = ii.Boolean(False,name='truth')
    assert i.descriptor.ds_columnName == b'truth'

def test_of_readable_type_name():
    i = ii.Boolean(False)
    type_name = i.SQL_declaration
    assert type_name == 'BOOLEAN'

def test_of_python_value_type():
    i = ii.Boolean(True)
    python_type = type(i.value)
    assert python_type is bool
