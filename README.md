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

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)

