"""View for model and data pair."""
from traits.has_traits import HasTraits, on_trait_change
from traits.trait_numeric import Array
from traits.trait_types import Any, File, Instance, Button, Enum, Str, Range, Bool, Float, Event, List
from traitsui.editors.file_editor import FileEditor
from traitsui.editors.instance_editor import InstanceEditor
from traitsui.editors.tabular_editor import TabularEditor
from traitsui.group import HGroup, VGroup
from traitsui.item import Item, Spring
from traitsui.menu import OKCancelButtons
from traitsui.view import View
from pyanno.modelBt import ModelBt
from pyanno.ui.arrayview import Array2DAdapter
from pyanno.ui.model_bt_view import ModelBtView

import numpy as np

ANNOTATIONS_INFO_STR = """Annotations file {}
Number of annotations: {}
Number of annotators: {}
Labels: {}"""


# TODO fix size, scroll bar on second line
# TODO remember last setting of parameters
class NewModelDialog(HasTraits):
    model_name = Str
    nclasses = Range(low=3, high=50)

    def traits_view(self):
        traits_view = View(
            VGroup(
                Item(name='nclasses',
                     label='Number of annotation classes:',
                     id='test')
            ),
            buttons=OKCancelButtons,
            title='Create new ' + self.model_name,
            kind='modal'
        )
        return traits_view


class DataView(HasTraits):
    data = Array

    def traits_view(self):
        return View(
            VGroup(Item('data',
                        editor=TabularEditor
                            (
                            adapter=Array2DAdapter(ncolumns=len(self.data[0]),
                                                   format='%d',
                                                   show_index=False)),
                        show_label=False)),
            title='Model B-with-Theta, gamma parameters',
            width=500,
            height=800,
            resizable=True,
            buttons=OKCancelButtons
        )


class ModelDataView(HasTraits):

    model_name = Enum('Model B-with-theta',
                      'Model B (full model) [not ready yet]',
                      'Model A [not ready yet]')
    _model_name_to_class = {
        'Model B-with-theta': ModelBt
    }
    _model_name_to_view = {
        'Model B-with-theta': ModelBtView
    }

    model = Any
    model_view = Instance(ModelBtView)
    model_updated = Event
    model_update_suspended = Bool(False)

    annotations = Array(dtype=int, shape=(None, None))
    annotations_file = File
    annotations_updated = Event
    annotations_are_defined = Bool(False)

    annotations_info_str = Str

    info_string = Str
    log_likelihood = Float

    @on_trait_change('annotations_file')
    def _update_annotations_file(self):
        print 'loading file', self.annotations_file
        # load file
        # I don't use np.loadtxt to allow for format 1,2,3,\n
        # (i.e., last number is followed by comma)
        # TODO function in util to load arbitrary formats
        # TODO generalize to load all possible data values (including string annotations)
        # TODO allow different values for missing annotations
        annotations = []
        with open(self.annotations_file) as fh:
            for n, line in enumerate(fh):
                line = line.strip().replace(',', '')
                annotations.append(np.fromstring(line, dtype=int, sep=' '))

        self.annotations = np.asarray(annotations, dtype=int)
        self.annotations[self.annotations>-1] -= 1
        self.annotations_are_defined = True
        self.annotations_updated = True

    @on_trait_change('annotations_updated,model_updated')
    def _update_log_likelihood(self):
        print 'llhood'
        if self.annotations_are_defined:
            self.log_likelihood = self.model.log_likelihood(self.annotations)

    @on_trait_change('annotations_updated,model_updated')
    def _update_info_str(self):
        if not self.annotations_are_defined:
            self.info_string = ('Please define an annotations list.')
        else:
            self.info_string = ('Model and annotations are defined.')

    @on_trait_change('annotations_updated')
    def _update_annotations_info_str(self):
        print 'update string'
        classes = str(np.unique(self.annotations[self.annotations != -1]))
        self.annotations_info_str = ANNOTATIONS_INFO_STR.format(
            self.annotations_file,
            self.annotations.shape[0],
            self.annotations.shape[1],
            classes)

    @on_trait_change('model,model:theta,model:gamma')
    def _fire_model_updated(self):
        if not self.model_update_suspended:
            self.model_updated = True


    ### Actions ##############################################################

    ### Model creation actions
    # FIXME tooltip begins with "specifies..."
    new_model = Button(label='New model...')
    get_info_on_model = Button(label='Info...')

    ml_estimate = Button(label='ML estimate...',
                         desc=('Maximum Likelihood estimate of model '
                               'parameters'))
    map_estimate = Button(label='MAP estimate...')
    sample_theta_posterior = Button(label='Sample parameters...')
    estimate_labels = Button(label='Estimate labels...')

    edit_data = Button(label='Edit annotations...')

    def _new_model_fired(self):
        """Create new model."""
        model_name = self.model_name

        # dialog to request basic parameters
        dialog = NewModelDialog(model_name=model_name)
        dialog_ui = dialog.edit_traits()
        if dialog_ui.result:
            # user pressed 'Ok'
            # create model and update view
            model_class = self._model_name_to_class[model_name]
            self.model = model_class.create_initial_state(dialog.nclasses)
            self.model_view = self._model_name_to_view[model_name](
                model=self.model)

    def _ml_estimate_fired(self):
        """Request data file and run ML estimation of parameters."""
        print 'Estimate...'
        self.model_update_suspended = True
        model.mle(self.annotations, estimate_gamma=True, use_prior=False)
        self.model_update_suspended = False
        # TODO change this into event listener (self.model_updated)
        self._fire_model_updated()
        self.model_view.update_from_model()

    def _map_estimate_fired(self):
        """Request data file and run ML estimation of parameters."""
        print 'Estimate...'
        self.model_update_suspended = True
        model.mle(self.annotations, estimate_gamma=True, use_prior=True)
        self.model_update_suspended = False
        # TODO change this into event listener (self.model_updated)
        self._fire_model_updated()
        self.model_view.update_from_model()

    def _edit_data_fired(self):
        data_view = DataView(data=self.annotations)
        data_view.edit_traits(kind='modal')
        self.annotations_updated = True


    ### Views ################################################################

    def traits_view(self):
        ## Model view

        model_create_group = (
            HGroup(
                Item(name='model_name',show_label=False),
                Item(name='new_model', show_label=False),
                Item(name='get_info_on_model', show_label=False,
                     enabled_when='False'),
                show_border=True
            )
        )

        model_group = (
            VGroup (
                model_create_group,
                Item('model_view', style='custom', show_label=False),
                show_border = True,
                label = 'Model view',
            )
        )

        ## Data view

        data_create_group = VGroup(
            Item('annotations_file', style='simple', label='Annotations file',
                 width=400),
            show_border = True,
        )

        data_info_group = VGroup(
            Item('annotations_info_str',
                 show_label=False,
                 style='readonly',
                 height=80),
            HGroup(
                Item('edit_data',
                     enabled_when='annotations_are_defined',
                     show_label=False),
                Spring()
            ),
        )

        data_group = (
            VGroup (
                data_create_group,
                data_info_group,
                show_border = True,
                label = 'Data view',
            )
        )

        ## (Model,Data) view

        model_data_group = (
            VGroup(
                Item('info_string', show_label=False, style='readonly'),
                Item('log_likelihood', label='Log likelihood', style='readonly'),
                HGroup(
                    Item('ml_estimate',
                         enabled_when='annotations_are_defined',
                         show_label=False),
                    Item('map_estimate',
                         enabled_when='annotations_are_defined',
                         show_label=False),
                    Item('sample_theta_posterior',
                         enabled_when='annotations_are_defined',
                         show_label=False),
                    Item('estimate_labels',
                         enabled_when='annotations_are_defined',
                         show_label=False,
                         enabled_when='False'),
                ),
                show_border = True,
                label = 'Model-data view'
            )
        )


        ## Full view

        full_view = View(
            VGroup(
                HGroup(
                    model_group,
                    data_group
                ),
                model_data_group
            ),
            title='PyAnno - Models of data annotations by multiple curators',
            width = 1200,
            height = 800,
            resizable = True
        )

        return full_view



#### Testing and debugging ####################################################

def main():
    """ Entry point for standalone testing/debugging. """

    from pyanno.modelBt import ModelBt

    model = ModelBt.create_initial_state(5)
    model_data_view = ModelDataView(model=model,
                                    model_view=ModelBtView(model=model),
                                    annotations=model.generate_annotations
                                        (model.generate_labels(50*8)))
    model_data_view.configure_traits(view='traits_view')

    return model, model_data_view


if __name__ == '__main__':
    model, model_data_view = main()
