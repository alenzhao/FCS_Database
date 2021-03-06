#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Created on Sat 27 DEC 2014 02:07:37 PM PST
Builds HDF5 file with features from FCS data

"""

__author__ = "David Ng, MD"
__copyright__ = "Copyright 2014"
__license__ = "GPL v3"
__version__ = "1.0"
__maintainer__ = "Daniel Herman"
__email__ = "ngdavid@uw.edu"
__status__ = "Production"

import sys
import logging
import pandas as pd
from itertools import chain

from os import path
from sqlalchemy.exc import IntegrityError

from __init__ import add_filter_args

from FlowAnal.FCS import FCS
from FlowAnal.database.FCS_database import FCSdatabase
from FlowAnal.Feature_IO import Feature_IO
from FlowAnal.Analysis_Variables import gate_coords, comp_file

log = logging.getLogger(__name__)


def build_parser(parser):
    parser.add_argument('dir', help='Directory with Flow FCS files [required]',
                        type=str)
    parser.add_argument('-db', '--db', help='Input sqlite3 db for Flow meta data \
    [default: db/fcs.db]',
                        default="db/fcs.db", type=str)
    parser.add_argument('-feature-hdf5', '--feature-hdf5', help='Output hdf5 filepath for FCS features \
    [default: db/fcs_features.hdf5]', dest='hdf5_fp',
                        default="db/fcs_features.hdf5", type=str)
    parser.add_argument('-method', '--feature-extration-method',
                        help='The method to use to extract features [default: Full]',
                        default='Full', type=str, dest='feature_extraction_method')
    parser.add_argument('-ow','--overwrite',help='Overwrite Feature-hdf5 file',type=bool,
                         default=True, dest='clobber')
    add_filter_args(parser)


def action(args):
    log.info('Creating hdf5 file [%s] with features extracted by method [%s]' %
             (args.hdf5_fp, args.feature_extraction_method))

    # Connect to database
    log.info("Loading database input %s" % args.db)
    db = FCSdatabase(db=args.db, rebuild=False)

    # Create query
    q = db.query(exporttype='dict_dict', getfiles=True, **vars(args))

    # Create HDF5 object
    HDF_obj = Feature_IO(filepath=args.hdf5_fp, clobber=args.clobber)

    # initalize empty list to append case_tube_idx that failed feature extraction
    feature_failed_CTIx = []

    num_results = len(list(chain(*q.results.values())))
    i = 1
    log.info("Found {} case_tube_idx's".format(num_results))
    for case, case_info in q.results.items():
        for case_tube_idx, relpath in case_info.items():
            # this nested for loop iterates over all case_tube_idx
            log.info("Case: %s, Case_tube_idx: %s, File: %s [%s of %s]" %
                     (case, case_tube_idx, relpath, i, num_results))
            filepath = path.join(args.dir, relpath)
            fFCS = FCS(filepath=filepath, case_tube_idx=case_tube_idx, import_dataframe=True)

            try:
                fFCS.comp_scale_FCS_data(compensation_file=comp_file,
                                         gate_coords=gate_coords,
                                         rescale_lim=(-0.5, 1),
                                         strict=False, auto_comp=False)
                fFCS.feature_extraction(extraction_type=args.feature_extraction_method,
                                        bins=10)
                HDF_obj.push_fcs_features(case_tube_idx=case_tube_idx,
                                          FCS=fFCS, db=db)
            except ValueError, e:
                print("Skipping feature extraction for case: {} because of 'ValueError {}'".
                      format(case, str(e)))
            except KeyError, e:
                print "Skipping FCS %s because of KeyError: %s" % (filepath, str(e))
            except IntegrityError, e:
                print "Skipping Case: {}, Tube: {}, Date: {}, filepath: {} because \
                of IntegrityError: {}".format(case, case_tube_idx, filepath, str(e))
            except:
                print "Skipping FCS %s because of unknown error related to: %s" % \
                    (filepath, sys.exc_info()[0])
                e = sys.exc_info()[0]

            print("{:6d} of {} cases found and loaded\r".format(i, num_results)),
            if 'e' in locals():
                feature_failed_CTIx.append([case, case_tube_idx, e])
                del(e)

            i += 1

    if feature_failed_CTIx == []:
        # if no features failed, we will create a dummy dataframe to load
        # otherwise when reading this will cause a failure
        failed_DF = pd.DataFrame([['NaN', 'NaN', 'NaN']],
                                 columns=['case_number', 'case_tube_idx', 'error_message'])
        log.info("Nothing failed feature extraction!")
    else:
        failed_DF = pd.DataFrame(feature_failed_CTIx,
                                 columns=['case_number', 'case_tube_idx', 'error_message'])
        log.info("Case_numbers that failed feature extraction: {}".
                 format(failed_DF.case_number.unique()))
        log.info("Case_tubes that failed feature extraction: {}".
                 format(failed_DF.case_tube_idx.unique()))

    HDF_obj.push_failed_cti_list(failed_DF)


