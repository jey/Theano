import numpy
from theano import gof
from theano.gof import Constant, Generic, Op
from basic import tensor
##########################
# Disk Access
##########################


class LoadFromDisk(Op):
    """
    An operation to load an array from disk

    See Also
        load

    @note: Non-differentiable.
    """
    def __init__(self, dtype, broadcastable, mmap_mode=None):
        self.dtype = numpy.dtype(dtype)  # turn "float64" into numpy.float64
        self.broadcastable = broadcastable
        if mmap_mode not in (None, 'c'):
            raise ValueError("The only supported values for mmap_mode "
                    "are None and 'c', got %s" % mmap_mode)
        self.mmap_mode = mmap_mode
        self._info = (dtype, broadcastable, mmap_mode)

    def __eq__(self, other):
        return (type(self) == type(other) and self._info == other._info)

    def __hash__(self):
        return hash(self._info)

    def make_node(self, path):
        if isinstance(path, str):
            path = Constant(Generic(), path)
        return gof.Apply(self, [path], [tensor(self.dtype,
                                        broadcastable=self.broadcastable)])

    def perform(self, node, inp, out):
        path = inp[0]
        if (path.split('.')[-1] == 'npz'):
            raise ValueError("Expected a .npy file, got %s instead" % path)
        result = numpy.load(path, mmap_mode=self.mmap_mode)
        if result.dtype != self.dtype:
            raise TypeError("Expected an array of type %s, got %s instead" %
                    (self.dtype, result.dtype))
        print 'result:', result, type(result)
        out[0][0] = result

    def __str__(self):
        return "Load{dtype:%s, broadcastable:%s, mmep:%s}" % self._info


def load(path, dtype, broadcastable, mmap_mode=None):
    """
    Load an array from an .npy file.

    :param path: A Generic symbolic variable, that will contain a string
    :param dtype: The data type of the array to be read.
    :param broadcastable: The broadcastable pattern of the loaded array,
      for instance, (False,) for a vector, (False, True) for a column,
      (False, False) for a matrix.
    :param mmap_mode: How the file will be loaded. None means that the
      data will be copied into an array in memory, 'c' means that the file
      will be mapped into virtual memory, so only the parts that are
      needed will be actually read from disk and put into memory.
      Other modes supported by numpy.load ('r', 'r+', 'w+') cannot
      be supported by Theano.

    >>> from theano import *
    >>> path = Variable(Generic())
    >>> x = tensor.load(path, 'int64', (False,))
    >>> y = x*2
    >>> fn = function([path], y)
    >>> fn("stored-array.npy")
    array([0, 2, 4, 6, 8], dtype=int64)
    """

    return LoadFromDisk(dtype, broadcastable, mmap_mode)(path)
