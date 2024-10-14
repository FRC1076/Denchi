import tarfile
import io
import os
import pandas as pd
import tomli
from typing import BinaryIO
from batconReader import batteryTest

def exportLogToTar(log : batteryTest, verbose = False, **kwargs) -> ta:
    '''
    kwargs is a list of filetypes to export to. Options include:
    csv,tsv,xml,arrow,parquet,orc,json'''
    pass