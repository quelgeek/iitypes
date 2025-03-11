# iitypes

**iitypes** is a package to marshall Actian **Ingres** and **Vector** data into Python
applications.

## Installation

Use [pip](https://pip.pypa.io/en/stable/) to install **iitypes**.

```bash
pip install iitypes
```

(Note for **Conda** and **Miniconda** users: there is an as-yet undiagnosed problem that prevents **pip** from properly resolving the dependency on **loguru**. As a workaround install loguru before installing pyngres.)

## Usage

To make use of the "classic" Ingres data types:

```python
import iitypes as ii
```

To exploit all the standard Ingres data types (excluding the geospatial types):

```python
import iitypes.standard as ii
```

**Linux:** initialize your Ingres environment by executing **~/.ing**XX**sh**, where XX
is your installation identifier (usually **II**). Example:

```
. ~/.ingIIsh
```

**Windows:** your Ingres installation will usually be initialized already.

## Notes

The **iitypes** containers are hashable and hence may be used as dictionary keys or
as members of a set.

The IIAPI_LBYTE_TYPE, IIAPI_LVCH_TYPE, IIAPI_LBYTE_TYPE, and IIAPI_LNVCH_TYPE
containers are not supported. When a query could return a BLOb, set
```
qyp.qy_flags = py.IIAPI_QF_LOCATORS
```
in the **IIapi_query()** parameter block and 
expect to receive BLOb locator (IIAPI_LBLOC_TYPE, IIAPI_LCLOC_TYPE, or
IIAPI_LNLOC_TYPE) instead.


## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)

