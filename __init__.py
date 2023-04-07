import os
import sys
import inspect
import argparse
from typing import Callable

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import showInfo
from aqt.operations import QueryOp

# https://stackoverflow.com/a/11158224
script_file = inspect.getfile(inspect.currentframe())
base_folder = os.path.dirname(os.path.abspath(script_file))
sys.path.append(os.path.join(base_folder, "tools"))


# import as if this script was under tools/
import utils as jpmn_utils
import install as jpmn_install


def get_args(raw_args: str, *args: Callable[[argparse.ArgumentParser], None]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    for add_args_func in args:
        add_args_func(parser)

    return parser.parse_args(args=raw_args.split())


def install(update=False):
    # TODO: check if it's already installed, etc.

    def install_op():
        args = get_args("", jpmn_utils.add_args, jpmn_install.add_args)
        if update:
            args.update = True
        jpmn_install.main(args)

    def install_success():
        msg = f"Successfully {'updated' if update else 'installed'} jp-mining-note!"
        showInfo(msg)

    op = QueryOp(
        parent=mw,
        op=lambda _: install_op(),
        success=lambda _: install_success(),
    )


    msg = f"{'Updating' if update else 'Installing'} jp-mining-note..."
    op.with_progress(msg).run_in_background()


class ConfirmUpdateDialog(QDialog):
    def __init__(self, *args):
        super().__init__(*args)
        self._button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self._setup()
        self.exec()

    def _setup(self):
        # vl: vertical layout
        vl = QVBoxLayout()
        warning_msg = ("WARNING:\n"
                       "This will override any changes you made to your template!\n"
                       "Please make a backup of your collection before continuing.\n"
                       "If you have not made a backup, please press 'cancel'.")
        vl.addWidget(QLabel(warning_msg))
        vl.addWidget(self._button_box)
        self.setLayout(vl)

        qconnect(self._button_box.accepted, self.accept)
        qconnect(self._button_box.rejected, self.reject)

    def accept(self) -> None:
        # TODO actually update the note?
        return super().accept()


def init_gui():
    menu = mw.form.menuTools.addMenu("JPMN Manager")

    install_action = QAction("Install jp-mining-note", mw)
    qconnect(install_action.triggered, lambda: install())
    menu.addAction(install_action)

    update_action = QAction("Update jp-mining-note", mw)
    qconnect(update_action.triggered, lambda: ConfirmUpdateDialog(mw))
    menu.addAction(update_action)


init_gui()

