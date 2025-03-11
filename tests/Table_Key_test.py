import pytest
import pyngres as py
import iitypes.standard as ii

##  example: 0x54010000B4E10A66

def test_of_str_value_instantiation():
    i = ii.Table_Key('54010000B4E10A66')
    assert i.value==b'T\x01\x00\x00\xb4\xe1\nf'

def test_of_repr():
    i = ii.Table_Key('54010000B4E10A66')
    assert repr(i) == "iitypes.types.IIAPI_TABKEY_TYPE('54010000b4e10a66')"

def test_of_byte_value_instantiation():
    b = bytes.fromhex('54010000B4E10A66')
    i = ii.Table_Key(b)
    assert i.value==b'T\x01\x00\x00\xb4\xe1\nf'

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Table_Key()
    assert str(e.value) == 'no initial value'

def test_of_str_value_assignment():
    i = ii.Table_Key('0101010101010101')
    i.value = '54010000B4E10A66'
    assert i.value==b'T\x01\x00\x00\xb4\xe1\nf'

def test_of_permitted_NULL_assignment():
    b = bytes.fromhex('54010000B4E10A66')
    i = ii.Table_Key(b,nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_NULL_assignment_flagged_null():
    b = bytes.fromhex('54010000B4E10A66')
    i = ii.Table_Key(b,nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.datavalue.dv_null == True

def test_of_disallowed_NULL_assignment():
    with pytest.raises(ValueError) as e:
        b = bytes.fromhex('54010000B4E10A66')
        i = ii.Table_Key(b,nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.Table_Key(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.Table_Key(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.Table_Key(3.14)
    assert str(e.value) == 'not bytes, bytearray, or str'
    
def test_of_single_positional():
    b = bytes.fromhex('54010000B4E10A66')
    with pytest.raises(RuntimeError) as e:
        i = ii.Table_Key(b,False)
    assert str(e.value) == 'too many arguments'

def test_of_poke():
    b = bytes.fromhex('0101010101010101')
    i = ii.Table_Key('54010000B4E10A66')
    i._poke(b)
    assert i.value == b

def test_of_user_assigned_name():
    i = ii.Table_Key('54010000B4E10A66',name='this_here')
    assert i.descriptor.ds_columnName == b'this_here'

def test_of_readable_type_name():
    i = ii.Table_Key('54010000B4E10A66')
    type_name = i.SQL_declaration
    assert type_name == 'TABLE_KEY'

def test_of_python_value_type():
    i = ii.Table_Key('54010000B4E10A66')
    python_type = type(i.value)
    assert python_type is bytes
