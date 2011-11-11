# Copyright (c) 2011, Enthought, Ltd.
# Author: Pietro Berkes <pberkes@enthought.com>
# License: Modified BSD license (2-clause)

"""Plot tools to save plots and copy their data inside to the clipboard.
"""

from chaco.plot_graphics_context import PlotGraphicsContext
from chaco.tools.save_tool import SaveTool
from enable.base_tool import BaseTool
from traits.has_traits import HasTraits
from traits.trait_types import Int, Any, File
from pyface.api import clipboard
from chaco.default_colors import palette11 as CLASS_COLORS
from chaco.default_colors import cbrewer as ANNOTATOR_COLORS

from traitsui.editors.file_editor import FileEditor
from traitsui.group import VGroup
from traitsui.item import Item
from traitsui.menu import OKCancelButtons
from traitsui.view import View

import os.path
import numpy as np


def get_annotator_color(idx):
    return list(ANNOTATOR_COLORS[idx % len(ANNOTATOR_COLORS)])

def get_class_color(idx):
    return list(CLASS_COLORS[idx % len(CLASS_COLORS)])


# NOTE this code can be deleted after the next release of enthought.enable
# NOTE current version is enable.__version__ == '4.0.1'
def _key_event_repackaging(key_event):
    """Workaround for Issue #37 in enable.

    Remap keys in wx and qt to have a consistent behavior across platforms
    """

    import wx
    from pyface.qt import QtCore, QtGui
    import enable.wx.constants as wx_constants
    from enable.events import KeyEvent

    def wx_key_event_repackaging(key_event, gui_event):
        key_code = gui_event.GetKeyCode()
        if key_code in wx_constants.KEY_MAP:
            character = wx_constants.KEY_MAP[key_code]
        elif key_code == wx.WXK_COMMAND:
            character = 'Menu'
        else:
            character = unichr(key_code).lower()

        return KeyEvent(event_type=key_event.event_type,
                        character=character,
                        x=key_event.x, y=key_event.y,
                        control_down=gui_event.ControlDown(),
                        shift_down=gui_event.ShiftDown(),
                        meta_down=gui_event.MetaDown(),
                        event=gui_event,
                        window=key_event.window)

    def qt_new_behavior_key_event(key_event, gui_event):
        modifiers = gui_event.modifiers()

        character = key_event.character
        import sys
        if sys.platform == 'darwin':
            # manually switch Meta and Control for Mac OS X
            key_code = gui_event.key()
            if key_code == QtCore.Qt.Key_Control: character = 'Menu'
            elif key_code == QtCore.Qt.Key_Meta: character = 'Control'
            control_down = bool(modifiers & QtCore.Qt.MetaModifier)
            meta_down =  bool(modifiers & QtCore.Qt.ControlModifier)
        else:
            control_down = bool(modifiers & QtCore.Qt.ControlModifier)
            meta_down =  bool(modifiers & QtCore.Qt.MetaModifier)

        # re-package old event according to new criteria
        return KeyEvent(event_type=key_event.event_type,
                        character=character,
                        x=key_event.x, y=key_event.y,
                        alt_down=bool(modifiers & QtCore.Qt.AltModifier),
                        shift_down=bool(modifiers & QtCore.Qt.ShiftModifier),
                        control_down=control_down,
                        meta_down=meta_down,
                        event=gui_event,
                        window=key_event.window)


    gui_event = key_event.event

    if isinstance(gui_event, wx._core.KeyEvent):
        key_event = wx_key_event_repackaging(key_event, gui_event)
    elif isinstance(gui_event, QtGui.QKeyEvent):
        key_event = qt_new_behavior_key_event(key_event, gui_event)

    return key_event


def _is_control_down(key_event):
    """Return true if the Ctrl or Cmd key is down."""

    return key_event.control_down or key_event.meta_down


class SaveFileDialog(HasTraits):
    save_file = File(exists=False)
    dpi = Int(300)

    traits_view = View(
        VGroup(
            Item('save_file', label='Save to:',
                 editor=FileEditor(allow_dir=False,
                                   dialog_style='save',
                                   entries=0),
                 style='simple'),
            Item('dpi', label='Resolution (dpi):')
        ),
        title = 'Save plot',
        width = 400,
        resizable=True,
        buttons=OKCancelButtons
    )


class SaveToolPlus(SaveTool):
    """Subclass of SaveTool that requests a filename and dpi before saving."""

    def normal_key_pressed(self, event):
        """Handles a key-release when the tool is in the 'normal' state.

        Saves an image of the plot when the user presses Ctrl-S.
        """

        if self.component is None: return

        # workaround for differences in Mac OS X, wx, and qt
        event = _key_event_repackaging(event)

        if event.character == "s" and _is_control_down(event):
            dialog = SaveFileDialog()
            dialog.edit_traits(kind='modal')

            self.filename = dialog.save_file

            if self.filename != '':
                if os.path.splitext(self.filename)[-1] == ".pdf":
                    self._save_pdf()
                else:
                    self._save_raster(dpi=dialog.dpi)

            event.handled = True

    def _save_raster(self, dpi=300):
        """ Saves an image of the component."""
        self.component.do_layout(force=True)
        # NOTE saving only works properly when dpi is a multiple of 72
        gc = PlotGraphicsContext((int(self.component.outer_width),
                                  int(self.component.outer_height)),
                                 dpi=np.ceil(dpi / 72.0)*72)
        gc.render_component(self.component)
        gc.save(self.filename)


class CopyDataToClipboardTool(BaseTool):
    """Tool that copies the plot's data to the clipboard."""

    data = Any

    def normal_key_pressed(self, event):
        """Handles a key-release when the tool is in the 'normal' state.

        Copy `data` to the keyboard when the user presses Ctrl-C.
        """

        if self.component is None: return

        # workaround for differences in Mac OS X, wx, and qt
        event = _key_event_repackaging(event)

        if event.character == "c"  and _is_control_down(event):
            # save numpy print options
            old_printoptions = np.get_printoptions()
            np.set_printoptions(infstr='numpy.inf', nanstr='numpy.nan',
                                suppress=True, threshold=1000000,
                                precision=6)

            # copy data to clipboard
            clipboard.data = repr(self.data)

            # reset numpy print options
            np.set_printoptions(**old_printoptions)

            event.handled = True