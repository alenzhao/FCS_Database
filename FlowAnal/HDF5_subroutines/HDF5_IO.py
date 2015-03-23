# -*- coding: utf-8 -*-
"""
Created on Fri 09 Jan 2015 03:22:34 PM PST
This file describes a HDF5 interface class for pushing and pulling a pandas
dataframe

@author: David Ng, MD
"""
__author__ = "David Ng, MD"
__copyright__ = "Copyright 2015"
__license__ = "GPL v3"
__version__ = "1.0"
__maintainer__ = "David Ng"
__email__ = "ngdavid@uw.edu"
__status__ = "Production"

import pandas as pd
import numpy as np
import h5py
import os
import logging
log = logging.getLogger(__name__)


class HDF5_IO(object):
    def __init__(self, filepath, clobber=False):
        """ Base interface with HDF file/object
        """
        self.filepath = filepath

        if clobber is True and os.path.exists(filepath):
            log.info('Clobbering {}'.format(filepath))
            os.remove(filepath)

    def push_Series(self, SR, path, ext_filehandle=None):
        """
        Method for pushing a full pandas series to the hdf5 file
        """
        if ext_filehandle:
            fh = ext_filehandle
        else:
            fh = h5py.File(self.filepath, 'a')
        fh[os.path.join(path, 'index')] = [str(i) for i in SR.index]
        fh[os.path.join(path, 'data')] = SR.values.astype(str)
        fh[os.path.join(path, 'dtype')] = SR.dtype
        if not ext_filehandle:
            fh.close()

    def pull_Series(self, path, ext_filehandle=None, dtype=np.int64):
        """
        Method for returning a full pandas dataframe from teh files
        """
        if ext_filehandle:
            fh = ext_filehandle
        else:
            fh = h5py.File(self.filepath, 'r')

        # if os.path.join(path, 'dtype') in fh:
        #     dtype = fh[os.path.join(path, 'dtype')].value

        SR = pd.Series(data=fh[os.path.join(path, 'data')].value,
                       index=fh[os.path.join(path, 'index')].value,
                       dtype=dtype)
        if not ext_filehandle:
            fh.close()
        return SR

    def push_DataFrame(self, DF, path, ext_filehandle=None):
        """
        Method for pushing a full pandas dataframe to the hdf5 file
        """
        if ext_filehandle:
            fh = ext_filehandle
        else:
            fh = h5py.File(self.filepath, 'a')

        il = []
        for i in DF.index:
            if isinstance(i, (tuple, list)):
                il.append([str(j) for j in i])
            else:
                il.append(str(i))

        cl = []
        for i in DF.columns.values:
            if isinstance(i, (tuple, list)):
                cl.append([str(j) for j in i])
            else:
                cl.append(str(i))

        fh[os.path.join(path, 'index')] = il
        fh[os.path.join(path, 'columns')] = cl
        fh[os.path.join(path, 'data')] = DF.values.astype(str)

        if not ext_filehandle:
            fh.close()

    def pull_DataFrame(self, path, ext_filehandle=None,
                       dtype=None):
        """
        Method for returning a full pandas dataframe from teh files
        """
        if ext_filehandle:
            fh = ext_filehandle
        else:
            fh = h5py.File(self.filepath, 'r')

        ix = fh[os.path.join(path, 'index')].value
        cols = fh[os.path.join(path, 'columns')].value

        if len(cols.shape) > 1:
            cols = [np.asarray(x)
                    for x in zip(*cols)]

        if len(ix.shape) > 1:
            ix = [np.asarray(x)
                  for x in zip(*ix)]

        if dtype is not None:
            DF = pd.DataFrame(data=fh[os.path.join(path, 'data')].value,
                              index=ix,
                              columns=cols,
                              dtype=dtype)
        else:
            DF = pd.DataFrame(data=fh[os.path.join(path, 'data')].value,
                              index=ix,
                              columns=cols)

        if not ext_filehandle:
            fh.close()
        return DF
