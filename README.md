# iitypes

**iitypes** is a package to marshall Actian **Ingres** and **Vector** data between Python
and the Actian DBMS.

## Installation

Use [pip](https://pip.pypa.io/en/stable/) to install **iitypes**.

```bash
pip install iitypes
```

## Usage

To make use of the "classic" Ingres data types:

```python
import iitypes as ii
```

To exploit all the standard Ingres data types (excluding the geospatial types):

```python
import iitypes.standard as ii
```

**Linux/Darwin:** initialize your Ingres environment by executing **~/.ing**XX**sh**, where XX
is your installation identifier (usually **II**). Example:

```
. ~/.ingIIsh
```

**Windows:** your Ingres installation will usually be initialized already.

## Notes

The **iitypes** containers are hashable and hence may be used as dictionary keys or
as members of a set.

The IIAPI_LBYTE_TYPE, IIAPI_LVCH_TYPE, IIAPI_LBYTE_TYPE, and IIAPI_LNVCH_TYPE
containers are not supported. Use locator containers instead. When a query
could return 
a large object, configure the **IIapi_query()** parameter block to return 
locators:
```
qyp.qy_flags = py.IIAPI_QF_LOCATORS
```
The query will return one or more of IIAPI_LBLOC_TYPE, IIAPI_LCLOC_TYPE, or
IIAPI_LNLOC_TYPE. (Refer to the OpenAPI documentation for information about
fetching objects using these locators.)

Support for the geospatial types will be added in a future release. (Let us
know if you have an imminent need for the geospatial types.)


## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)

