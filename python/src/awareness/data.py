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


import exception
import misc
import affinity as i_affinity
import algorithm as i_algorithm
import backend as i_backend
import operator as i_operator
import protocol as i_protocol


class Item:

    parameters = ()

    def __init__(self, parameters):
        self.parameters = tuple(parameters)

    def to_datums(self):
        datums = []
        for parameter in self.parameters:
            datums.append((float(parameter),))  # The parameter in a 1-tuple
        return datums


    @classmethod
    def from_datums(self, datums):
        parameters = []
        for datum in datums:
            parameters.append(datum[0])  # First (only) tuple item
        return Item(tuple(parameters))

    @property
    def count(self):
        return len(self.parameters)



class Stream:


    items = []

    def __init__(self, items):
        self.items = list(items)


    def to_datums(self):
        datums = []
        for item in self.items:
            datums += item.to_datums()
        return datums

    def extract(self, start_parameter, end_parameter):
        output = Stream([])
        for item in self.items:
            output.items.append(Item(item.parameters[start_parameter:end_parameter]))

        return output

    def inject(self, other_stream, start_parameter, end_parameter):
        for i in range(len(self.items)):
            parameter_list = list(self.items[i].parameters)
            parameter_list[start_parameter:end_parameter + 1] = list(other_stream.items[i].parameters)
            self.items[i].parameters = tuple(parameter_list)


    @classmethod
    def from_count_datums(self, count, datums):
        items = []
        n_params = len(datums) / count if count != 0 else 0

        for item_index in range(count):
            start_pos = item_index * n_params
            end_pos = (item_index + 1) * n_params
            items.append(Item.from_datums(datums[start_pos:end_pos]))

        return Stream(items)


    @property
    def count(self):
        return len(self.items)

    @classmethod
    def blankFromCountParameters(self, count, parameters):
        items = []
        for i in range(count):
            items.append(Item((0,) * parameters))
        return Stream(items)



class Set:

    input_stream = None
    output_stream = None

    def __init__(self, input_stream, output_stream):
        self.input_stream = input_stream
        self.output_stream = output_stream


    def to_datums(self):
        return self.input_stream.to_datums() + self.output_stream.to_datums()  # concat


    @classmethod
    def from_inputs_outputs_count_datums(self, n_inputs, n_outputs, count, datums):

        inputs = datums[:n_inputs*count]
        outputs = datums[n_inputs*count:(n_inputs*count) + n_outputs*count]

        input_stream = Stream.from_count_datums(count, inputs)
        output_stream = Stream.from_count_datums(count, outputs)


        return Set(input_stream, output_stream)


    @property
    def count(self):
        return self.input_stream.count

    @property
    def n_inputs(self):
        return self.input_stream.items[0].count

    @property
    def n_outputs(self):
        return self.output_stream.items[0].count


class Assembly:

    # List of tuples (addr, port, index, in_offset, out_offset)
    operations = []

    def __init__(self, operations):

        self.operations = operations


    def to_datums(self):
        return self.operations

    @classmethod
    def from_datums(self, datums):

        operations = []
        for datum in datums:
            listdatum = list(datum)
            listdatum[0] = listdatum[0].rstrip('\0')
            operations.append(tuple(listdatum))

        return Assembly(operations)


    def run(self, input_stream, progress_frequency=0, progress_callback=None):


        stream_state = input_stream  # Pump pipeline on first iteration

        for operation in self.operations:

            with i_operator.RemoteOperator(operation[0], port=operation[1]) as operator:
                operator.retrieve_affinities()

                data_in_start_idx = operation[3]  # in_offset
                data_in_end_idx = operation[3] + operator.affinities[operation[2]].inputs  # plus number of inputs

                data_section = stream_state.extract(data_in_start_idx, data_in_end_idx)

                result = operator.process(operation[2], data_section)

                data_out_start_idx = operation[4]  # out_offset
                data_out_end_idx = operation[4] + operator.affinities[operation[2]].outputs  # plus number of outputs
                stream_state.inject(result, data_out_start_idx, data_out_end_idx)  # stream_state will then be used above to construct a new Stream for the next operation


        return stream_state
