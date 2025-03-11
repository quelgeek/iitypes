import pytest
import pyngres as py
import ipaddress as ip
import iitypes.standard as ii

ii.publish_envHandle()

def test_of_str_value_instantiation():
    i = ii.IPv4('172.16.0.2')
    assert i.value == ip.IPv4Address('172.16.0.2')

def test_of_repr():
    i = ii.IPv4('172.16.0.2')
    assert repr(i) == "iitypes.types.IIAPI_IPV4_TYPE('172.16.0.2')"

def test_of_IPv4Address_instantiation():
    addr = ip.IPv4Address('172.16.0.3')
    i = ii.IPv4(addr)
    assert str(i.value) == '172.16.0.3'

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.IPv4()
    assert str(e.value) == 'no initial value'

def test_of_value_assignment():
    i = ii.IPv4('172.16.0.2')
    i.value = '192.168.1.254'
    assert i.value == ip.IPv4Address('192.168.1.254')

def test_of_permitted_NULL_assignment():
    i = ii.IPv4('172.16.0.2',nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_disallowed_NULL_assignment():
    with pytest.raises(ValueError) as e:
        i = ii.IPv4('172.16.0.2',nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.IPv4(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.IPv4(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_formatted_display():
    i = ii.IPv4('172.16.0.2')
    assert i.formatted() == '172.16.0.2'

def test_of_domain_checking():
    with pytest.raises(ValueError) as e:
        i = ii.IPv4('monkey business')
    assert str(e.value) == 'could not convert to IPV4'

def test_of_spurious_positional():
    with pytest.raises(RuntimeError) as e:
        i = ii.IPv4('172.16.0.2','guffage')
    assert str(e.value) == 'too many arguments'
    
def test_of_instantiation_from_descriptor():
    d = py.IIAPI_DESCRIPTOR()
    d.ds_dataType=py.IIAPI_IPV4_TYPE    
    d.ds_nullable=1     
    d.ds_length=py.IIAPI_IPV4_LEN       
    d.ds_precision=0    
    d.ds_scale=0        
    d.ds_columnType=0   
    d.ds_columnName=None    
    i = ii.IPv4(descriptor=d)
    assert i.datavalue.dv_value > 0
    
def test_of_poke():
    i = ii.IPv4('192.168.1.254')
    i._poke('0x7f88ff55')
    assert i.formatted() == '127.136.255.85'

def test_of_poke_overflow_prevention():
    i = ii.IPv4('192.168.1.254')
    i._poke('0x010101010101010101010101')
    assert i._peek() == '01010101'

def test_of_user_assigned_name():
    i = ii.IPv4('192.168.1.254',name='here')
    assert i.descriptor.ds_columnName == b'here'

def test_of_readable_type_name():
    i = ii.IPv4('192.168.1.254')
    type_name = i.SQL_declaration
    assert type_name == 'IPV4'

def test_of_python_value_type():
    i = ii.IPv4('192.168.1.254')
    python_type = type(i.value)
    assert python_type is ip.IPv4Address
