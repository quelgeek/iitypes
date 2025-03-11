import pytest
import iitypes.classic as ii
import struct

def test_of_instantiation():
    value = 'Give me your answer, do!'
    i = ii.Varchar(value,len(value))
    assert i.value == value

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Varchar()
    assert str(e.value) == 'no initial value'

def test_of_implied_size_instantiation():
    value = b'Hello World!'
    i = ii.Varchar(value)
    ##  there is a 2 bytes overhead for the internal length indicator
    assert i.descriptor.ds_length == len(value) + 2

def test_of_explicit_size_instantiation():
    value = b'Hello World!'
    length = 101
    i = ii.Varchar(value,length)
    ##  there is a 2 bytes overhead for the internal length indicator
    assert i.descriptor.ds_length == length + 2

def test_of_repr():
    i = ii.Varchar("I'm sorry Dave, I'm afraid I can't do that")
    assert repr(i) == 'iitypes.types.IIAPI_VCH_TYPE("I\'m sorry Dave, I\'m afraid I can\'t do that",42)'

def test_of_instantiation_overflow():
    with pytest.raises(OverflowError) as e:
        value = 'Great fat jelly-wobbling fat-bastard'
        i = ii.Varchar(value,10)
    assert str(e.value) == 'VARCHAR(10) capacity exceeded'

def test_of_assignment_overflow():
    with pytest.raises(OverflowError) as e:
        value = 'Great fat jelly-wobbling fat-bastard'
        i = ii.Varchar('Stick insect',20)
        i.value = value
    assert str(e.value) == 'VARCHAR(20) capacity exceeded'

def test_of_instantiation_NOTNULL_nullability():
    i = ii.Varchar('Daisy')
    assert i.descriptor.ds_nullable == False

def test_of_instantiation_WITHNULL_nullability():
    i = ii.Varchar('Daisy',nullable=ii.WITHNULL)
    assert i.descriptor.ds_nullable == True

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.Varchar(3.14)
    assert str(e.value) == 'not bytes, bytearray, or str'

def test_of_double_positional():
    with pytest.raises(RuntimeError) as e:
        i = ii.Varchar("I'm half crazy",30,30)
    assert str(e.value) == 'too many arguments'
    
def test_of_poke():
    i = ii.Varchar('All for the love of you!',30)
    value = b"It won't be a stylish marriage"
    length = len(value)
    format = f'h{length}s'
    pokeage = struct.pack(format,length,value)
    i._poke(pokeage)
    #assert i._peek() == '1e00497420776f6e27742062652061207374796c697368206d61727269616765'
    assert i.value == "It won't be a stylish marriage"

def test_of_poke_overflow_prevention():
    ##  NB: this test puts a corrupt value in the buffer but that
    ##  is an explicitly stated risk of using _poke() which ingtypes doesn't
    ##  attempt to prevent
    i = ii.Varchar('All for the love of you!')
    value = b"It won't be a stylish marriage"
    length = len(value)
    format = f'h{length}s'
    pokeage = struct.pack(format,length,value)
    i._poke(pokeage)
    assert i._peek() == '1e00497420776f6e27742062652061207374796c697368206d61'

def test_of_readable_type_name():
    i = ii.Varchar(b'\x00' * 42)
    type_name = i.SQL_declaration
    assert type_name == 'VARCHAR(42)'

def test_of_python_value_type():
    i = ii.Varchar("I can't afford a carriage")
    python_type = type(i.value)
    assert python_type is str    
