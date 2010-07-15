#
#  This file is part of the Connection-Set Algebra (CSA).
#  Copyright (C) 2010 Mikael Djurfeldt
#
#  CSA is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  CSA is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import _misc

def disc (r):
    return _misc.Disc (r)

def gaussian (sigma, cutoff):
    return _misc.Gaussian (sigma, cutoff)

def block (M, N = None):
    return _misc.Block (M, M if N == None else N)

transpose = _misc.Transpose ()

fix = _misc.Fix ()

#del _misc                               # not for export
