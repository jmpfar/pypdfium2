# SPDX-FileCopyrightText: 2021 geisserml <geisserml@gmail.com>
# SPDX-License-Identifier: Apache-2.0


class PageCountInvalidError (Exception):
    """
    Raised if ``FPDF_GetPageCount()`` returns a value less than 1.
    This may hint at an invalid file path or a missing password.
    """
    pass

class PageIndexError (IndexError):
    """ Raised on the attempt to load an out-of-bounds page number. """
    pass