# SPDX-FileCopyrightText: 2022 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0 OR BSD-3-Clause 

import ctypes
from os.path import abspath
from typing import (
    Union,
    Tuple,
    BinaryIO,
)
from pypdfium2 import _pypdfium as pdfium
from pypdfium2._helpers.error_handler import *


def is_buffer(obj) -> bool:
    """
    Check whether an object is a byte buffer that implements ``seek()``, ``tell()``,
    and ``readinto()``.
    
    Returns:
        :data:`True` if the object implements all required methods, :data:`False` otherwise.
    """
    
    if all( callable(getattr(obj, a, None)) for a in ('seek', 'tell', 'readinto') ):
        return True
    else:
        return False


class _reader_class:
    """
    Class that implements the callback for ``FPDF_FILEACCESS.m_GetBlock()``, to incrementally
    read file data from a buffer.
    """
    
    def __init__(self, buffer):
        self.buffer = buffer
    
    def __call__(self, param, position, p_buf, size):
        self.buffer.seek(position)
        c_buf = (ctypes.c_char * size).from_address( ctypes.addressof(p_buf.contents) )
        self.buffer.readinto(c_buf)
        return 1


class LoaderData:
    """
    Class to store data associated to an ``FPDF_DOCUMENT`` that was opened using
    ``FPDF_LoadCustomDocument()``.
    
    Parameters:
        file_handle:
            File buffer that implements the ``close()`` method.
        reader_instance:
            The callable object for file access (a :class:`._reader_class` instance
            wrapped with the corresponding :func:`ctypes.CFUNCTYPE`).
    """
    
    def __init__(
            self,
            file_handle = None,
            reader_instance = None,
        ):
        self.file_handle = file_handle
        self.reader_instance = reader_instance
    
    def close(self):
        if self.file_handle is not None:
            self.file_handle.close()


def open_pdf_buffer(
        buffer: BinaryIO,
        password: Union[str, bytes] = None,
    ) -> Tuple[pdfium.FPDF_DOCUMENT, LoaderData]:
    """
    Open a PDF document incrementally from a byte buffer using ``FPDF_LoadCustomDocument()`` and
    a ctypes callback function.
    
    Parameters:
        buffer:
            A byte buffer as defined in :func:`.is_buffer`.
        password:
            A password to unlock the document, if encrypted.
    
    Returns:
        The handle to a PDFium document, and a :class:`.LoaderData` object to store associated
        file access data.
    
    See also :func:`.open_pdf_auto`. **The same warnings apply!**
    """
    
    if not is_buffer(buffer):
        raise ValueError("Buffer must implement the methods seek(), tell(), and readinto().")
    
    buffer.seek(0, 2)
    file_len = buffer.tell()
    buffer.seek(0)
        
    FuncType = ctypes.CFUNCTYPE(
        # restype
        ctypes.c_int,
        # argtypes
        ctypes.POINTER(None),
        ctypes.c_ulong,
        ctypes.POINTER(ctypes.c_ubyte),
        ctypes.c_ulong,
    )
    
    fileaccess = pdfium.FPDF_FILEACCESS()
    fileaccess.m_FileLen = file_len
    fileaccess.m_GetBlock = FuncType( _reader_class(buffer) )
    
    pdf = pdfium.FPDF_LoadCustomDocument(ctypes.byref(fileaccess), password)
    ld_data = LoaderData(buffer, fileaccess.m_GetBlock)
    
    if pdfium.FPDF_GetPageCount(pdf) < 1:
        handle_pdfium_error(False)
    
    return pdf, ld_data


def open_pdf_native(
        filepath: str,
        password: Union[str, bytes] = None,
    ) -> Tuple[pdfium.FPDF_DOCUMENT, LoaderData]:
    """    
    Open a PDF document from a file path, managing all file access natively in Python using
    :func:`.open_pdf_buffer`, without having to load the whole file into memory at once.
    This ensures independence from file access in PDFium, which currently has issues with
    widestring filepaths on Windows. However, it may be slower to a certain extent due to
    object conversions between C and Python involved in the callback.
    
    Please refer to :func:`.open_pdf_auto` for parameter and return documentation.
    **The same warnings apply!**
    """
    
    file_handle = open(abspath(filepath), 'rb')
    return open_pdf_buffer(file_handle, password)