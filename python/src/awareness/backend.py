#
# This file is part of the Awareness Operator Python implementation.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#


from abc import ABCMeta, abstractproperty, abstractmethod
import multiprocessing
import threading
import socket
import misc
import affinity as i_affinity
import algorithm as i_algorithm
import data as i_data
import operator as i_operator
import protocol as i_protocol


class Backend:
    __metaclass__ = ABCMeta

    @abstractmethod
    def threadingAsync(self, function, args=(), kwargs={}, callback=None):
        raise NotImplementedError()

    @abstractmethod
    def connect(self, host, port=1600):
        raise NotImplementedError()

    @abstractmethod
    def listen(self, host='', port=1600, use_ipv6=False, backlog=5):
        raise NotImplementedError()



class NativeBackend(Backend):


    def threadingAsync(self, function, args=(), kwargs={}, callback=None):
        if not callback: callback = lambda *args,**kwargs:None

        def wrapWithCallback(function, callback): return lambda *args, **kwargs: callback(function(*args, **kwargs))

        thread = threading.Thread(target=wrapWithCallback(function, callback), args=args, kwargs=kwargs)
        thread.daemon = True
        thread.start()


    def connect(self, host, port=1600):
        return socket.create_connection((host, port))


    def listen(self, host='', port=1600, use_ipv6=False, backlog=5):
        type = socket.AF_INET6 if use_ipv6 else socket.AF_INET

        listener = socket.socket(type, socket.SOCK_STREAM)
        listener.bind((host, port))
        listener.listen(backlog)

        return listener
