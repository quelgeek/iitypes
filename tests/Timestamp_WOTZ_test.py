import pytest
import iitypes.standard as ii

##  Timestamp_WOTZ is an alias for Timestamp and IIAPI_TSWO_TYPE

def test_of_alias_Timestamp():
    assert type(ii.Timestamp_WOTZ) == type(ii.Timestamp)

def test_of_alias_IIAPI_TSWO_TYPE():
    assert type(ii.Timestamp_WOTZ) == type(ii.IIAPI_TSWO_TYPE)
