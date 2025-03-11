import pytest
import iitypes.standard as ii
import struct

def test_of_instantiation():
    ##  What is this you idiot?
    value ='?? ?? ???'
    i = ii.Nvarchar(value,len(value))
    assert i.value == value

def test_of_repr():
    i = ii.Nvarchar('MBH\'s 30th birthday')
    assert repr(i) == "iitypes.types.IIAPI_NVCH_TYPE('MBH\\\'s 30th birthday',19)"

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Nvarchar()
    assert str(e.value) == 'no initial value'

def test_of_implied_size_instantiation():
    value = 'Hello World!'
    i = ii.Nvarchar(value)
    ##  UCS-2 characters use 2 bytes for each character and there is a
    ##  2 bytes overhead for the internal length indication 
    assert i.descriptor.ds_length == len(value) * 2 + 2

def test_of_explicit_size_instantiation():
    value = 'Hello World!'
    length = 101
    i = ii.Nvarchar(value,length)
    ##  UCS-2 characters use 2 bytes for each character and there is a
    ##  2 bytes overhead for the internal length indication 
    assert i.descriptor.ds_length == length * 2 + 2

def test_of_instantiation_overflow():
    with pytest.raises(OverflowError) as e:
        value = 'Great fat jelly-wobbling fat-bastard'
        i = ii.Nvarchar(value,10)
    assert str(e.value) == 'NVARCHAR(10) capacity exceeded'

def test_of_assignment_overflow():
    with pytest.raises(OverflowError) as e:
        value = 'Great fat jelly-wobbling fat-bastard'
        i = ii.Nvarchar('Stick insect',20)
        i.value = value
    assert str(e.value) == 'NVARCHAR(20) capacity exceeded'

def test_of_instantiation_NOTNULL_nullability():
    i = ii.Nvarchar('Daisy')
    assert i.descriptor.ds_nullable == False

def test_of_instantiation_WITHNULL_nullability():
    i = ii.Nvarchar('Daisy',nullable=ii.WITHNULL)
    assert i.descriptor.ds_nullable == True

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.Nvarchar(3.14)
    assert str(e.value) == 'not bytes, bytearray, or str'

def test_of_double_positional():
    with pytest.raises(RuntimeError) as e:
        i = ii.Nvarchar("I'm half crazy",30,30)
    assert str(e.value) == 'too many arguments'
    
def test_of_poke():
    i = ii.Nvarchar('All for the love of you!',30)
    value = "It won't be a stylish marriage".encode('utf-16le')
    length = len(value)
    format = f'h{length}s'
    pokeage = struct.pack(format,length,value)
    i._poke(pokeage)
    assert i.value == "It won't be a stylish marriage"

def test_of_poke_overflow_prevention():
    ##  NB: this test puts a corrupt value in the buffer but that
    ##  is an explicitly stated risk of using _poke() which ingtypes doesn't
    ##  attempt to prevent
    i = ii.Nvarchar('All for the love of you!')
    value = "It won't be a stylish marriage"
    encoded_value = value.encode('utf-16le')
    length = len(value)
    encoded_length = len(encoded_value)
    format = f'h{encoded_length}s'
    pokeage = struct.pack(format,length,encoded_value)
    i._poke(pokeage)
    assert i._peek() == '1e0049007400200077006f006e00270074002000620065002000610020007300740079006c0069007300680020006d0061007200'

def test_of_readable_type_name():
    i = ii.Nvarchar(' ' * 42)
    type_name = i.SQL_declaration
    assert type_name == 'NVARCHAR(42)'

def test_of_python_value_type():
    i = ii.Nvarchar("I can't afford a carriage")
    python_type = type(i.value)
    assert python_type is str    
