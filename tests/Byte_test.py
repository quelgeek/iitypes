import pytest
import iitypes.standard as ii

def test_of_instantiation():
    value = b'Give me your answer, do!'
    i = ii.Byte(value,len(value))
    assert i.value == value

def test_of_repr():
    value = b'Give me your answer, do!\x00'
    i = ii.Byte(value,25,nullable=ii.WITHNULL)
    assert repr(i) == "iitypes.types.IIAPI_BYTE_TYPE(b'Give me your answer, do!\\x00',25,nullable=iitypes.types.WITHNULL)"

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Byte()
    assert str(e.value) == 'no initial value'

def test_of_implied_size_instantiation():
    value = b'Hello World!'
    i = ii.Byte(value)
    assert i.descriptor.ds_length == len(value)

def test_of_explicit_size_instantiation():
    value = b'Hello World!'
    length = 101
    i = ii.Byte(value,length)
    assert i.descriptor.ds_length == length

def test_of_non_ASCII_instantiation():
    value = b'\x80\xa3\xd0\xfe'
    i = ii.Byte(value)
    assert i.value == value

def test_of_instantiation_overflow():
    with pytest.raises(OverflowError) as e:
        value = 'Great fat jelly-wobbling fat-bastard'
        i = ii.Byte(value,10)
    assert str(e.value) == 'BYTE(10) capacity exceeded'

def test_of_assignment_overflow():
    with pytest.raises(OverflowError) as e:
        value = 'Great fat jelly-wobbling fat-bastard'
        i = ii.Byte('Stick insect',20)
        i.value = value
    assert str(e.value) == 'BYTE(20) capacity exceeded'

def test_of_instantiation_NOTNULL_nullability():
    i = ii.Byte(b'Daisy')
    assert i.descriptor.ds_nullable == False

def test_of_instantiation_WITHNULL_nullability():
    i = ii.Byte(b'Daisy',nullable=ii.WITHNULL)
    assert i.descriptor.ds_nullable == True

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.Byte(3.14)
    assert str(e.value) == 'not bytes, bytearray, or str'

def test_of_double_positional():
    with pytest.raises(RuntimeError) as e:
        i = ii.Byte("I'm half crazy",30,30)
    assert str(e.value) == 'too many arguments'
    
def test_of_poke():
    i = ii.Byte('All for the love of you!',30)
    pokeage = b"It won't be a stylish marriage"
    i._poke(pokeage)
    assert i._peek() == '497420776f6e27742062652061207374796c697368206d61727269616765'

def test_of_poke_overflow_prevention():
    i = ii.Byte('All for the love of you!')
    pokeage = b"It won't be a stylish marriage"
    i._poke(pokeage)
    assert i._peek() == '497420776f6e27742062652061207374796c697368206d61'

def test_of_readable_type_name():
    i = ii.Byte(b'\x00' * 42)
    type_name = i.SQL_declaration
    assert type_name == 'BYTE(42)'

def test_of_python_value_type():
    i = ii.Byte("I can't afford a carriage")
    python_type = type(i.value)
    assert python_type is bytes    
