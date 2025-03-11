import pytest
import iitypes.standard as ii

def test_of_instantiation():
    ##  What is this you idiot?
    value ='?? ?? ???'
    i = ii.Nchar(value)
    assert i.value == value

def test_of_repr():
    i = ii.Nchar('MBH\'s 30th birthday')
    assert repr(i) == "iitypes.types.IIAPI_NCHA_TYPE('MBH\\\'s 30th birthday',19)"

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Nchar()
    assert str(e.value) == 'no initial value'

def test_of_implied_size_instantiation():
    value = b'What is this you idiot?'
    i = ii.Nchar(value)
    assert i.descriptor.ds_length == len(value)

def test_of_explicit_size_instantiation():
    value = b'Hello World!'
    length = 101
    i = ii.Nchar(value,length)
    ##  UCS-2 characters use 2 bytes each
    assert i.descriptor.ds_length == length * 2

def test_of_instantiation_overflow():
    with pytest.raises(OverflowError) as e:
        value = 'Great fat jelly-wobbling fat-bastard'
        i = ii.Nchar(value,10)
    assert str(e.value) == 'NCHAR(10) capacity exceeded'

def test_of_assignment_overflow():
    with pytest.raises(OverflowError) as e:
        value = 'Great fat jelly-wobbling fat-bastard'
        i = ii.Nchar('Stick insect',20)
        i.value = value
    assert str(e.value) == 'NCHAR(20) capacity exceeded'

def test_of_instantiation_NOTNULL_nullability():
    i = ii.Nchar(b'Daisy')
    assert i.descriptor.ds_nullable == False

def test_of_instantiation_WITHNULL_nullability():
    i = ii.Nchar(b'Daisy',nullable=ii.WITHNULL)
    assert i.descriptor.ds_nullable == True

def test_of_domain_checking():
    with pytest.raises(TypeError) as e:
        i = ii.Nchar(3.14)
    assert str(e.value) == 'not bytes, bytearray, or str'

def test_of_double_positional():
    with pytest.raises(RuntimeError) as e:
        i = ii.Nchar("I'm half crazy",30,30)
    assert str(e.value) == 'too many arguments'
    
def test_of_poke():
    i = ii.Nchar('All for the love of you!',30)
    pokeage = "It won't be a stylish marriage".encode('utf-16le')
    i._poke(pokeage)
    assert i._peek() == '49007400200077006f006e00270074002000620065002000610020007300740079006c0069007300680020006d006100720072006900610067006500'

def test_of_poke_overflow_prevention():
    i = ii.Nchar('All for the love of you!')
    pokeage = "It won't be a stylish marriage".encode('utf-16le')
    i._poke(pokeage)
    assert i._peek() == '49007400200077006f006e00270074002000620065002000610020007300740079006c0069007300680020006d006100'

def test_of_readable_type_name():
    i = ii.Nchar(b'\x00' * 42)
    type_name = i.SQL_declaration
    ##  UCS-2 characters are 2 bytes each so 42 bytes is 21 UCS-2 characters
    assert type_name == 'NCHAR(21)'

def test_of_python_value_type():
    i = ii.Nchar("I can't afford a carriage")
    python_type = type(i.value)
    assert python_type is str
