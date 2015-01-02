#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Template script for selecting a set of .fcs files and operating on them one-by-one

NOTE: There are some files that are not found because of discordance of filename \
and filename internal to .fcs file (meta info)
"""
import logging
from os import path

from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.FCS import FCS
from FlowAnal.HDF5_IO import HDF5_IO
from FlowAnal.__init__ import package_data, __version__
from FlowAnal.Analysis_Variables import coords,comp_file,test_fcs_fn

log = logging.getLogger(__name__)

def build_parser(parser):
    parser.add_argument('-hdf','--hdf', help='Location of HDF5 file to store [default: \
    db/fcs_features.hdf5]', default="db/fcs_features.hdf5", type=str)
    parser.add_argument('-tubes', '--tubes', help='List of tube types to select',
                        nargs='+', action='store',
                        default=None, type=str)
    parser.add_argument('-dates', '--daterange',
                        help='Start and end dates to bound selection of cases \
                        [Year-Month-Date Year-Month-Date]',
                        nargs=2, action='store', type=str)
    parser.add_argument('-db', '--db', help='Input sqlite db containing flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-cases', '--cases', help='List of cases to select',
                        nargs='+', action='store',
                        default=None, type=str)


def action(args):
    # Connect to database
    db = FCSdatabase(db=args.db, rebuild=False)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    #initialize HDF_obj
    HDF_obj = HDF5_IO(filepath=args.hdf)

    case_tube_list=[]
    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            log.info("Case: %s, Case_tube_idx: %s, File: %s" % (case, case_tube_idx, relpath))
            case_tube_list.append(case_tube_idx)

    output_DF = HDF_obj.make_single_tube_analysis(case_tube_list)
    print output_DF
    """
    meta_db search not yet built    
    """

