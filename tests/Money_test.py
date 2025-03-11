import pytest
import pyngres as py
import iitypes.classic as ii
import decimal as dec

ii.publish_envHandle()

def test_of_str_value_instantiation():
    i = ii.Money('$100.23')
    assert 100.22999 <= i.value <= 100.23001

def test_of_repr():
    i = ii.Money('100.23')
    assert repr(i) == "iitypes.types.IIAPI_MNY_TYPE('$100.23')"

def test_of_float_value_instantiation():
    dosh = 100.23
    i = ii.Money(dosh)
    assert 100.22999 <= i.value <= 100.23001

def test_of_Decimal_instantiation():
    dosh = dec.Decimal(100.23)
    i = ii.Money(dosh)
    assert 100.22999 <= i.value <= 100.23001

def test_of_formatted_display():
    i = ii.Money('100.23')
    ##  assuming II_MONEY_FORMAT=L:$
    assert i.formatted() == '$100.23' 

def test_of_bare_instantiation():
    with pytest.raises(RuntimeError) as e:
        i = ii.Money()
    assert str(e.value) == 'no initial value'

def test_of_str_value_assignment():
    i = ii.Money('100.23')
    i.value = '9.99'
    assert 9.98999 <= i.value <= 9.99001

def test_of_float_value_assignment():
    dosh = 100.23
    i = ii.Money('100.23')
    i.value = dosh
    assert 100.22999 <= i.value <= 100.23001

def test_of_permitted_NULL_assignment():
    dosh = 100.23
    i = ii.Money(dosh,nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.value is None

def test_of_NULL_assignment_flagged_null():
    dosh = 100.23
    i = ii.Money(dosh,nullable=ii.WITHNULL)
    i.value = ii.NULL
    assert i.datavalue.dv_null == True

def test_of_disallowed_NULL_assignment():
    dosh = 100.23
    with pytest.raises(ValueError) as e:
        i = ii.Money(dosh,nullable=ii.NOTNULL)
        i.value = ii.NULL
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_NOTNULL():
    with pytest.raises(ValueError) as e:
        i = ii.Money(ii.NULL,nullable=ii.NOTNULL)
    assert str(e.value) == 'not nullable'

def test_of_instantiation_to_NULL_with_WITHNULL():
    i = ii.Money(ii.NULL,nullable=ii.WITHNULL)
    assert i.value is None

def test_of_domain_checking():
    with pytest.raises(ValueError) as e:
        i = ii.Money('jiggery-pokery')
    assert str(e.value) == 'type conversion failed'

def test_of_single_positional():
    dosh = 100.23
    with pytest.raises(RuntimeError) as e:
        i = ii.Money(dosh,True)
    assert str(e.value) == 'too many arguments'

def test_of_poke():
    i = ii.Money('9.99')
    i._poke('0000000000408f40')     ##  should be 10.00
    assert 9.99999 <= i.value <= 10.00001

def test_of_user_assigned_name():
    i = ii.Money('0.99',name='bargain')
    assert i.descriptor.ds_columnName == b'bargain'

def test_of_readable_type_name():
    i = ii.Money('9.99')
    type_name = i.SQL_declaration
    assert type_name == 'MONEY'

def test_of_python_value_type():
    i = ii.Money('9.99')
    python_type = type(i.value)
    assert python_type is float
