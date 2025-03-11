import pytest
import pyngres as py
import iitypes.classic as ii

##  C() is currently implemented by aliasing Char() so the only additional
##  test is that the readable name is rendered correctly

def test_of_readable_type_name():
    i = ii.C('C is alias for Char')
    type_name = i.SQL_declaration
    assert type_name == 'C19'
