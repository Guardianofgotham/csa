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

import random as _random
import numpy as _numpy
import copy

import connset as _cs
import intervalset as _is


class OneToOne (_cs.Mask):
    def __init__ (self):
        _cs.Mask.__init__ (self)
    
    def iterator (self, low0, high0, low1, high1, state):
        for i in xrange (max (low0, low1), min (high0, high1)):
            yield (i, i)


class ConstantRandomMask (_cs.Mask):
    def __init__ (self, p):
        _cs.Mask.__init__ (self)
        self.p = p
        self.state = _random.getstate ()

    def startIteration (self, state):
        _random.setstate (self.state)
        return self

    def iterator (self, low0, high0, low1, high1, state):
        for j in xrange (low1, high1):
            for i in xrange (low0, high0):
                if _random.random () < self.p:
                    yield (i, j)


class SampleNRandomOperator (_cs.Operator):
    def __init__ (self, N):
        self.N = N

    def __mul__ (self, other):
        assert isinstance (other, _cs.Finite) \
               and isinstance (other, _cs.Mask), \
               'expected finite mask'
        return SampleNRandomMask (self.N, other)


class SampleNRandomMask (_cs.Finite,_cs.Mask):
    # The algorithm based on first sampling the number of connections
    # per partition has been arrived at through discussions with Hans
    # Ekkehard Plesser.
    #
    def __init__ (self, N, mask):
        _cs.Mask.__init__ (self)
        self.N = N
        assert isinstance (mask, _cs.IntervalSetMask), \
               'SampleNRandomMask only operates on IntervalSetMask:s'
        self.mask = mask
        self.randomState = _random.getstate ()
        self.npRandomState = _numpy.random.get_state ()

    def bounds (self):
        return self.mask.bounds ()

    def startIteration (self, state):
        obj = copy.copy (self)  # local state: N, N0, perTarget, sources
        _random.setstate (self.randomState)
        obj.isPartitioned = False
        if 'partitions' in state:
            obj.isPartitioned = True
            partitions = map (self.mask.intersection, state['partitions'])
            sizes = map (len, partitions)
            total = sum (sizes)
            
            # The following yields the same result on all processes.
            # We should add a seed function to the CSA.
            if 'seed' in state:
                seed = state['seed']
            else:
                seed = 'SampleNRandomMask'
            _numpy.random.seed (hash (seed))
            
            N = _numpy.random.multinomial (self.N, _numpy.array (sizes) \
                                           / float (total))
            obj.N = N[state['selected']]
            obj.mask = partitions[state['selected']]
            assert isinstance (obj.mask, _cs.IntervalSetMask), \
                   'SampleNRandomMask iterator only handles IntervalSetMask partitions'
        obj.mask = obj.mask.startIteration (state)
        obj.N0 = len (obj.mask.set0)
        obj.lastBound0 = False
        N1 = len (obj.mask.set1)
        _numpy.random.set_state (self.npRandomState)
        obj.perTarget = _numpy.random.multinomial (obj.N, [1.0 / N1] * N1)
        return obj

    def iterator (self, low0, high0, low1, high1, state):
        m = self.mask.set1.count (0, low1)
        
        if self.isPartitioned and m > 0:
            # "replacement" for a proper random.jumpahead (n)
            # This is required so that different partitions of this
            # mask aren't produced using the same stream of random
            # numbers.
            _random.seed (_random.getrandbits (32) + m)
            
        if self.lastBound0 != (low0, high0):
            self.lastBound0 = (low0, high0)
            self.sources = []
            for i in self.mask.set0.boundedIterator (low0, high0):
                self.sources.append (i)

        nSources = len (self.sources)
        for j in self.mask.set1.boundedIterator (low1, high1):
            s = []
            for k in xrange (0, self.perTarget[m]):
                i = _random.randint (0, self.N0 - 1)
                if i < nSources:
                    s.append (self.sources[i])
            s.sort ()
            for i in s:
                yield (i, j)
            m += 1


class FanInRandomOperator (_cs.Operator):
    def __init__ (self, fanIn):
        self.fanIn = fanIn

    def __mul__ (self, other):
        assert isinstance (other, _cs.Finite) \
               and isinstance (other, _cs.Mask), \
               'expected finite mask'
        return FanInRandomMask (self.fanIn, other)


# This code is copied and modified from SampleNRandomMask
# *fixme* refactor code and eliminate code duplication
class FanInRandomMask (_cs.Finite,_cs.Mask):
    # The algorithm based on first sampling the number of connections
    # per partition has been arrived at through discussions with Hans
    # Ekkehard Plesser.
    #
    def __init__ (self, fanIn, mask):
        _cs.Mask.__init__ (self)
        self.fanIn = fanIn
        assert isinstance (mask, _cs.IntervalSetMask), \
               'FanInRandomMask only operates on IntervalSetMask:s'
        self.mask = mask
        self.randomState = _random.getstate ()
        self.npRandomState = _numpy.random.get_state ()

    def bounds (self):
        return self.mask.bounds ()

    def startIteration (self, state):
        obj = copy.copy (self)  # local state: N, N0, perTarget, sources
        _random.setstate (self.randomState)
        obj.isPartitioned = False
        if 'partitions' in state:
            obj.isPartitioned = True
            partitions = map (self.mask.intersection, state['partitions'])
            
            # The following yields the same result on all processes.
            # We should add a seed function to the CSA.
            if 'seed' in state:
                seed = state['seed']
            else:
                seed = 'FanInRandomMask'
            _numpy.random.seed (hash (seed))

            selected = state['selected']
            obj.mask = partitions[selected]
            assert isinstance (obj.mask, _cs.IntervalSetMask), \
                   'SampleNRandomMask iterator only handles IntervalSetMask partitions'
        obj.mask = obj.mask.startIteration (state)
        obj.N0 = len (obj.mask.set0)
        obj.lastBound0 = False
        if obj.isPartitioned:
            _numpy.random.set_state (self.npRandomState)
            obj.perTarget = []
            for j in obj.mask.set1:
                size = 0
                sourceDist = _numpy.zeros (len (partitions))
                for k in xrange (len (partitions)):
                    if j in partitions[k].set1:
                        sourceDist[k] = len (partitions[k].set0)
                sourceDist /= sum (sourceDist)
                dist = _numpy.random.multinomial (self.fanIn, sourceDist)
                obj.perTarget.append (dist[selected])
        else:
            obj.perTarget = [self.fanIn] * len (obj.mask.set1)
        return obj

    def iterator (self, low0, high0, low1, high1, state):
        m = self.mask.set1.count (0, low1)
        
        if self.isPartitioned and m > 0:
            # "replacement" for a proper random.jumpahead (n)
            # This is required so that different partitions of this
            # mask aren't produced using the same stream of random
            # numbers.
            _random.seed (_random.getrandbits (32) + m)
            
        if self.lastBound0 != (low0, high0):
            self.lastBound0 = (low0, high0)
            self.sources = []
            for i in self.mask.set0.boundedIterator (low0, high0):
                self.sources.append (i)

        nSources = len (self.sources)
        for j in self.mask.set1.boundedIterator (low1, high1):
            s = []
            for k in xrange (0, self.perTarget[m]):
                i = _random.randint (0, self.N0 - 1)
                if i < nSources:
                    s.append (self.sources[i])
            s.sort ()
            for i in s:
                yield (i, j)
            m += 1


class FanOutRandomOperator (_cs.Operator):
    def __init__ (self, fanOut):
        self.fanOut = fanOut

    def __mul__ (self, other):
        assert isinstance (other, _cs.Finite) \
               and isinstance (other, _cs.Mask), \
               'expected finite mask'
        return _cs.TransposedMask (FanInRandomMask (self.fanOut, other))
