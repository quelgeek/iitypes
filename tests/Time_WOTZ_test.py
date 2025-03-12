import pytest
import iitypes.standard as ii

##  Time_WOTZ is an alias for Time and IIAPI_TMWO_TYPE

def test_of_alias_Time():
    assert type(ii.Time_WOTZ) == type(ii.Time)

def test_of_alias_IIAPI_TMWO_TYPE():
    assert type(ii.Time_WOTZ) == type(ii.IIAPI_TMWO_TYPE)
