import pytest
import iitypes.classic as ii
import struct

def test_of_instantiation():
    value = 'Give me your answer, do!'
    i = ii.Text(value,len(value))
    assert i.value == value

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Text()
    assert str(e.value) == 'no initial value'

def test_of_implied_size_instantiation():
    value = b'Hello World!'
    i = ii.Text(value)
    assert i.descriptor.ds_length == len(value)

def test_of_repr():
    i = ii.Text('Open the pod-bay doors, HAL.')
    assert repr(i) == 'iitypes.types.IIAPI_TXT_TYPE("Open the pod-bay doors, HAL.",28)'

def test_of_explicit_size_instantiation():
    value = b'Hello World!'
    length = 101
    i = ii.Text(value,length)
    assert i.descriptor.ds_length == length

def test_of_embedded_NUL_replacement():
    i = ii.Text('Hello world',101)
    value = 'Give\x00me\x00your\x00answer,\x00do!'
    i.value = value
    assert i.value == 'Give me your answer, do!'

def test_of_instantiation_overflow():
    with pytest.raises(OverflowError) as e:
        value = 'Great fat jelly-wobbling fat-bastard'
        i = ii.Text(value,10)
    assert str(e.value) == 'TEXT(10) capacity exceeded'

def test_of_assignment_overflow():
    with pytest.raises(OverflowError) as e:
        value = 'Great fat jelly-wobbling fat-bastard'
        i = ii.Text('Stick insect',20)
        i.value = value
    assert str(e.value) == 'TEXT(20) capacity exceeded'

def test_of_instantiation_NOTNULL_nullability():
    i = ii.Text('Daisy')
    assert i.descriptor.ds_nullable == False

def test_of_instantiation_WITHNULL_nullability():
    i = ii.Text('Daisy',nullable=ii.WITHNULL)
    assert i.descriptor.ds_nullable == True

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.Text(3.14)
    assert str(e.value) == 'not bytes, bytearray, or str'

def test_of_double_positional():
    with pytest.raises(RuntimeError) as e:
        i = ii.Text("I'm half crazy",30,30)
    assert str(e.value) == 'too many arguments'
    
def test_of_poke():
    i = ii.Text('All for the love of you!',30)
    pokeage = b"It won't be a stylish marriage"
    i._poke(pokeage)
    assert i.value == "It won't be a stylish marriage"

def test_of_poke_overflow_prevention():
    i = ii.Text('All for the love of you!')
    pokeage =  b"It won't be a stylish marriage"
    i._poke(pokeage)
    assert i.value == "It won't be a stylish ma"

def test_of_readable_type_name():
    i = ii.Text(b'\x00' * 42)
    type_name = i.SQL_declaration
    assert type_name == 'TEXT(42)'

def test_of_python_value_type():
    i = ii.Text("I can't afford a carriage")
    python_type = type(i.value)
    assert python_type is str    
