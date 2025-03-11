import pytest
import pyngres as py
import iitypes.standard as ii
import uuid as uu

##  example: c8925082-d4ba-874b-8836-0d2a4ad9582f

def test_of_str_value_instantiation():
    i = ii.UUID('c8925082-d4ba-874b-8836-0d2a4ad9582f')
    assert i.value==uu.UUID('c8925082-d4ba-874b-8836-0d2a4ad9582f')

def test_of_repr():
    i = ii.UUID('c8925082-d4ba-874b-8836-0d2a4ad9582f')
    assert repr(i) == "iitypes.types.IIAPI_UUID_TYPE('c8925082-d4ba-874b-8836-0d2a4ad9582f')"

def test_of_byte_value_instantiation():
    b = bytes.fromhex('c8925082d4ba874b88360d2a4ad9582f')
    i = ii.UUID(b)
    assert i.value==uu.UUID('c8925082-d4ba-874b-8836-0d2a4ad9582f')

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.UUID()
    assert str(e.value) == 'no initial value'

def test_of_str_value_assignment():
    i = ii.UUID('c8925082-d4ba-874b-8836-0d2a4ad9582f')
    i.value = '91e18956-924f-7642-ab56-616cad4bb1a5'
    assert i.value==uu.UUID('91e18956-924f-7642-ab56-616cad4bb1a5')

def test_of_permitted_NULL_assignment():
    s = 'c8925082-d4ba-874b-8836-0d2a4ad9582f'
    i = ii.UUID(s,nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_NULL_assignment_flagged_null():
    s = 'c8925082-d4ba-874b-8836-0d2a4ad9582f'
    i = ii.UUID(s,nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.datavalue.dv_null == True

def test_of_disallowed_NULL_assignment():
    s = 'c8925082-d4ba-874b-8836-0d2a4ad9582f'
    with pytest.raises(ValueError) as e:
        i = ii.UUID(s,nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.UUID(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.UUID(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.UUID(3.14)
    assert str(e.value) == 'not uuid.UUID, bytes, bytearray, or str'
    
def test_of_single_positional():
    s = 'c8925082-d4ba-874b-8836-0d2a4ad9582f'
    with pytest.raises(RuntimeError) as e:
        i = ii.UUID(s,False)
    assert str(e.value) == 'too many arguments'

def test_of_poke():
    b = bytes.fromhex('01010101010101010101010101010101')
    i = ii.UUID('c8925082-d4ba-874b-8836-0d2a4ad9582f')
    i._poke(b)
    assert i.value == uu.UUID('01010101-0101-0101-0101-010101010101')

def test_of_user_assigned_name():
    i = ii.UUID('c8925082-d4ba-874b-8836-0d2a4ad9582f',name='sui_generis')
    assert i.descriptor.ds_columnName == b'sui_generis'

def test_of_readable_type_name():
    i = ii.UUID('c8925082-d4ba-874b-8836-0d2a4ad9582f')
    type_name = i.SQL_declaration
    assert type_name == 'UUID'

def test_of_python_value_type():
    i = ii.UUID('c8925082-d4ba-874b-8836-0d2a4ad9582f')
    python_type = type(i.value)
    assert python_type is uu.UUID
