from __future__ import annotations

import os
import sys
import shlex
import inspect
import argparse
from typing import Callable, Optional

from aqt import mw, gui_hooks
from aqt.qt import *
from aqt.utils import show_info, ask_user_dialog, getText
from aqt.operations import QueryOp

# https://stackoverflow.com/a/11158224
script_file = inspect.getfile(inspect.currentframe())
base_folder = os.path.dirname(os.path.abspath(script_file))
sys.path.append(os.path.join(base_folder, "tools"))


# import as if this script was under tools/
import utils as jpmn_utils
import install as jpmn_install
import batch as jpmn_batch

SETUP_CHANGES_URL = "https://aquafina-water-bottle.github.io/jp-mining-note/setupchanges/"


def get_args(raw_args: str, *args: Callable[[argparse.ArgumentParser], None]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    for add_args_func in args:
        add_args_func(parser)

    try:
        # we cannot rely on ArgumentParser(exit_on_error=False) to always throw an error
        # instead of an exception, so we use this gross hack to ensure Anki doesn't shut down...
        return parser.parse_args(args=shlex.split(raw_args))
    except SystemExit:
        raise RuntimeError("Error in arguments")


def install(update=False, args_str: str = ""):
    # TODO: check if it's already installed, etc.

    # some crazy hack because install_op doesn't seem to preserve post_message
    # if we just set post_message = ...
    post_message = {}
    KEY = "A"

    args = get_args(args_str, jpmn_utils.add_args, jpmn_install.add_args)
    if update:
        args.update = True
        args.dev_never_warn = True # prevents input() from being ran
        args.dev_return_notes = True

    def install_op():
        post_message[KEY] = jpmn_install.main(args)

    def install_success():
        msg = f"Successfully {'updated' if update else 'installed'} jp-mining-note!"
        if post_message[KEY] is not None:
            #msg += "\n\n" + post_message[KEY]
            msg += "<br><br>" + f'You\'re not finished yet! See the <a href="{SETUP_CHANGES_URL}">Setup Changes</a> page to update everything else.'
        show_info(msg, textFormat=Qt.TextFormat.RichText) # RichText to make html work

    op = QueryOp(
        parent=mw,
        op=lambda _: install_op(),
        success=lambda _: install_success(),
    )

    msg = f"{'Updating' if update else 'Installing'} jp-mining-note..."
    op.with_progress(msg).run_in_background()


def install_custom_args():
    (args_str, ret) = getText("Enter the installer arguments below.")
    if ret == 0: # user cancelled
        return
    install(args_str=args_str)


def confirm_update_warning():
    warning_msg = ("Updating will override any changes you made to jp-mining-note! "
                   "Please make a backup of your collection before continuing. "
                   "If you already made a backup and are fine with losing any changes, "
                   "press 'OK' to update. Otherwise, please press 'cancel'.")

    buttons = [QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel]

    def callback(idx: int):
        if idx == 0: # okay
            install(update=True)

    ask_user_dialog(warning_msg, callback, buttons=buttons, default_button=1)


def run_batch():
    (args_str, ret) = getText("Enter the batch command below.")
    if ret == 0: # user cancelled
        return
    args_arr = shlex.split(args_str)

    try:
        # we cannot rely on ArgumentParser(exit_on_error=False) to always throw an error
        # instead of an exception, so we use this gross hack to ensure Anki doesn't shut down...
        args = jpmn_batch.get_args(jpmn_batch.PUBLIC_FUNCTIONS_ANKI, args=args_arr)
    except SystemExit:
        raise RuntimeError("Error in arguments")

    # some crazy hack because install_op doesn't seem to preserve post_message
    # if we just set post_message = ...
    post_message = {}
    EXCEPTION_KEY = "exception"
    RESULT_KEY = "result"

    if "func" in args:
        def batch_op():
            # code copied from batch main()
            try:
                func_args = vars(args)
                func = func_args.pop("func")
                post_message[RESULT_KEY] = func(**func_args)
            except Exception as e:
                post_message[EXCEPTION_KEY] = str(e)

        def batch_success():
            if EXCEPTION_KEY in post_message:
                msg = post_message[EXCEPTION_KEY]
            else:
                msg = "Successfully ran batch command!"
                if RESULT_KEY in post_message:
                    result = post_message[RESULT_KEY]
                    if result is not None:
                        msg += "\n\n" + post_message[RESULT_KEY]
            show_info(msg)

        op = QueryOp(
            parent=mw,
            op=lambda _: batch_op(),
            success=lambda _: batch_success(),
        )

        msg = f"Running batch script..."
        op.with_progress(msg).run_in_background()

    else:
        show_info("Cannot find batch function")


def init_gui():
    menu = mw.form.menuTools.addMenu("JPMN Manager")

    install_action = QAction("Install jp-mining-note", mw)
    qconnect(install_action.triggered, lambda: install())
    menu.addAction(install_action)

    update_action = QAction("Update jp-mining-note", mw)
    qconnect(update_action.triggered, lambda: confirm_update_warning())
    menu.addAction(update_action)

    install_args_action = QAction("Run installer with arguments", mw)
    qconnect(install_args_action.triggered, lambda: install_custom_args())
    menu.addAction(install_args_action)

    batch_action = QAction("Run batch command", mw)
    qconnect(batch_action.triggered, lambda: run_batch())
    menu.addAction(batch_action)


init_gui()

