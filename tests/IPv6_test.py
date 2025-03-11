import pytest
import pyngres as py
import ipaddress as ip
import iitypes.standard as ii

ii.publish_envHandle()

def test_of_str_value_instantiation():
    i = ii.IPv6('2001:0db8:85a3:0042:1000:8a2e:0370:7334')
    assert i.value == ip.IPv6Address('2001:0db8:85a3:0042:1000:8a2e:0370:7334')

def test_of_repr():
    i = ii.IPv6('2001:0db8:85a3:0042:1000:8a2e:0370:7334')
    assert repr(i) == "iitypes.types.IIAPI_IPV6_TYPE('2001:db8:85a3:42:1000:8a2e:370:7334')"

def test_of_IPv6Address_instantiation():
    addr = ip.IPv6Address('2001:0db8:85a3:0042:1000:8a2e:0370:7334')
    i = ii.IPv6(addr)
    assert str(i.value) == '2001:db8:85a3:42:1000:8a2e:370:7334'

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.IPv6()
    assert str(e.value) == 'no initial value'

def test_of_value_assignment():
    i = ii.IPv6('2001:0db8:85a3:0042:1000:8a2e:0370:7334')
    i.value = '::ffff:c0a8:1'
    assert i.value == ip.IPv6Address('::ffff:c0a8:1')

def test_of_permitted_NULL_assignment():
    addr = ip.IPv6Address('2001:0db8:85a3:0042:1000:8a2e:0370:7334')
    i = ii.IPv6(addr,nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_disallowed_NULL_assignment():
    addr = ip.IPv6Address('2001:0db8:85a3:0042:1000:8a2e:0370:7334')
    with pytest.raises(ValueError) as e:
        i = ii.IPv6(addr,nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.IPv6(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.IPv6(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_IPv4_formatted_display():
    addr = ip.IPv6Address('::ffff:c0a8:1')
    i = ii.IPv6(addr)
    assert i.formatted() == '192.168.0.1'

def test_of_IPv6_formatted_display():
    addr = ip.IPv6Address('2001:0db8:85a3:0042:1000:8a2e:0370:7334')
    i = ii.IPv6(addr)
    assert i.formatted() == '2001:db8:85a3:42:1000:8a2e:370:7334'

def test_of_domain_checking():
    with pytest.raises(ValueError) as e:
        i = ii.IPv6('monkey business')
    assert str(e.value) == 'could not convert to IPV6'

def test_of_spurious_positional():
    addr = ip.IPv6Address('2001:0db8:85a3:0042:1000:8a2e:0370:7334')
    with pytest.raises(RuntimeError) as e:
        i = ii.IPv6(addr,'guffage')
    assert str(e.value) == 'too many arguments'
    
def test_of_instantiation_from_descriptor():
    d = py.IIAPI_DESCRIPTOR()
    d.ds_dataType=py.IIAPI_IPV6_TYPE    
    d.ds_nullable=1     
    d.ds_length=py.IIAPI_IPV6_LEN       
    d.ds_precision=0    
    d.ds_scale=0        
    d.ds_columnType=0   
    d.ds_columnName=None    
    i = ii.IPv6(descriptor=d)
    assert i.datavalue.dv_value > 0
    
def test_of_poke():
    i = ii.IPv6('192.168.1.254')
    i._poke('0x20010DB885A3004210008A2E03707334')
    assert i.formatted() == '2001:db8:85a3:42:1000:8a2e:370:7334'

def test_of_poke_overflow_prevention():
    i = ii.IPv6('192.168.1.254')
    i._poke('0x010101010101010101010101010101010101010101')
    assert i._peek() == '01010101010101010101010101010101'

def test_of_user_assigned_name():
    addr = ip.IPv6Address('2001:0db8:85a3:0042:1000:8a2e:0370:7334')
    i = ii.IPv6(addr,name='here')
    assert i.descriptor.ds_columnName == b'here'

def test_of_readable_type_name():
    addr = ip.IPv6Address('2001:0db8:85a3:0042:1000:8a2e:0370:7334')
    i = ii.IPv6(addr)
    type_name = i.SQL_declaration
    assert type_name == 'IPV6'

def test_of_python_value_type():
    addr = ip.IPv6Address('2001:0db8:85a3:0042:1000:8a2e:0370:7334')
    i = ii.IPv6(addr)
    python_type = type(i.value)
    assert python_type is ip.IPv6Address
