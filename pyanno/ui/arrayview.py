import numpy as np

from traits.api import HasTraits, Property, Array
from traits.trait_types import List, Int, Bool, Str
from traitsui.api import View, Item, TabularEditor
from traitsui.group import VGroup
from traitsui.tabular_adapter import TabularAdapter
from traitsui.menu import NoButtons


class Array2DAdapter(TabularAdapter):
    columns = List
    show_index = Bool(True)
    ncolumns = Int
    data_format = Str('%s')

    font = 'Courier 10'
    alignment = 'right'
    format = data_format
    index_text = Property


    def _get_index_text(self):
        return str(self.row)


    def _columns_default(self):
        columns = [('el%d' % (i+1), i) for i in range(self.ncolumns)]
        if self.show_index:
            columns.insert(0, ('row\col', 'index'))
        return columns


#### Testing and debugging ####################################################

def main():
    """Entry point for standalone testing/debugging."""

    class TestShowArray(HasTraits):

        data = Array

        view = View(
            Item(
                'data',
                editor=TabularEditor
                         (
                         adapter=Array2DAdapter(ncolumns=2,
                                                format='%s',
                                                show_index=False)),
                show_label=False
            ),
            title     = 'Array2D editor',
            width     = 0.3,
            height    = 0.8,
            resizable = True,
            buttons   = NoButtons
        )

        VGroup(Item('data',
                     editor=TabularEditor
                         (
                         adapter=Array2DAdapter(ncolumns=2,
                                                format='%d',
                                                show_index=False)),
                     show_label=False)),

    data = [['a', 'b'], [1, 2]]
    blah = TestShowArray(data=data)
    blah.data = data
    print blah.data
    blah.configure_traits()


if __name__ == '__main__':
    main()
