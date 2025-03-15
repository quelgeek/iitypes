import sys
import os
import pyngres as py
import iitypes.standard as ii
import datetime


try:
    dbname = os.environ['DBNAME']
except KeyError:
    print('')
    print('** Supply the database name with the DBNAME environment variable **')
    print('')
    raise

def test_LOB_locator_retrieved():
    target = dbname.encode()
    query = b'SELECT * FROM delivery WHERE ol_number = 1' 

    wtp = py.IIAPI_WAITPARM()
    wtp.wt_timeout = -1

    inp = py.IIAPI_INITPARM()
    inp.in_version = py.IIAPI_VERSION
    inp.in_timeout = -1
    py.IIapi_initialize(inp)
    connHandle = inp.in_envHandle

    cop = py.IIAPI_CONNPARM()
    cop.co_target = target
    cop.co_type = py.IIAPI_CT_SQL
    cop.co_connHandle = connHandle
    cop.co_timeout = -1
    py.IIapi_connect(cop)
    while not cop.co_genParm.gp_completed:
        py.IIapi_wait(wtp)
    if cop.co_genParm.gp_status != py.IIAPI_ST_SUCCESS:
        print(f'\n*** can\'t open database "{dbname}"\n')
        assert False
        return

    qyp = py.IIAPI_QUERYPARM()
    qyp.qy_connHandle = cop.co_connHandle
    qyp.qy_flags = py.IIAPI_QF_LOCATORS     ##  ask for locators not segments
    qyp.qy_queryType = py.IIAPI_QT_QUERY
    qyp.qy_queryText = query
    qyp.qy_parameters = False
    py.IIapi_query(qyp)
    while not qyp.qy_genParm.gp_completed:
        py.IIapi_wait(wtp)

    gdp = py.IIAPI_GETDESCRPARM()
    gdp.gd_stmtHandle = qyp.qy_stmtHandle
    py.IIapi_getDescriptor(gdp)
    while not gdp.gd_genParm.gp_completed:
        py.IIapi_wait(wtp)

    row = {}
    columnData = (py.IIAPI_DATAVALUE * gdp.gd_descriptorCount)()
    for column_index in range(gdp.gd_descriptorCount):
        descriptor = gdp.gd_descriptor[column_index]
        clone = type(descriptor).from_buffer_copy(descriptor)
        descriptor = clone
        buffer_allocator = ii.allocator_for_type(descriptor)
        buffer = buffer_allocator(descriptor=descriptor)
        columnData[column_index] = buffer.datavalue
        columnName = descriptor.ds_columnName.decode()
        row[columnName] = buffer

    gcp = py.IIAPI_GETCOLPARM()
    gcp.gc_rowCount = 1
    gcp.gc_columnCount = gdp.gd_descriptorCount
    gcp.gc_columnData = columnData
    gcp.gc_stmtHandle = qyp.qy_stmtHandle
    while True:
        py.IIapi_getColumns(gcp)
        while not gcp.gc_genParm.gp_completed:
            py.IIapi_wait(wtp)

        if gcp.gc_genParm.gp_status == py.IIAPI_ST_NO_DATA:
            break

    cnp = py.IIAPI_CANCELPARM()
    cnp.cn_stmtHandle = qyp.qy_stmtHandle
    py.IIapi_cancel(cnp)
    while not cnp.cn_genParm.gp_completed:
        py.IIapi_wait(wtp)

    clp = py.IIAPI_CLOSEPARM()
    clp.cl_stmtHandle = qyp.qy_stmtHandle
    py.IIapi_close(clp)
    while not clp.cl_genParm.gp_completed:
        py.IIapi_wait(wtp)

    rbp = py.IIAPI_ROLLBACKPARM()
    rbp.rb_tranHandle = qyp.qy_tranHandle
    py.IIapi_rollback(rbp)
    while not rbp.rb_genParm.gp_completed:
        py.IIapi_wait(wtp)

    dcp = py.IIAPI_DISCONNPARM()
    dcp.dc_connHandle = cop.co_connHandle
    py.IIapi_disconnect(dcp)
    while not dcp.dc_genParm.gp_completed:
        py.IIapi_wait(wtp)

    rep = py.IIAPI_RELENVPARM()
    rep.re_envHandle = inp.in_envHandle
    py.IIapi_releaseEnv(rep)

    tmp = py.IIAPI_TERMPARM()
    py.IIapi_terminate(tmp)

    assert (
        row['warehouse'].value == 10 and
        row['district'].value == 7 and
        row['order'].value == 2312 and
        row['proof'].value == 1 and
        row['ol_number'].value == 1 )

