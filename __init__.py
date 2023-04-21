from __future__ import annotations

import os
import sys
import time
import shlex
import inspect
import argparse
from typing import Callable

from aqt import mw, gui_hooks
from aqt.qt import (
    Qt,
    QMessageBox,
    QCheckBox,
    qconnect,
    QAction
)

#from aqt.utils import show_info, ask_user_dialog # TODO: use these when 2.1.60 becomes the min supported version
from aqt.utils import showInfo, askUserDialog, getText, ButtonedDialog, tooltip

from aqt.operations import QueryOp

# https://stackoverflow.com/a/11158224
script_file = inspect.getfile(inspect.currentframe())
base_folder = os.path.dirname(os.path.abspath(script_file))
sys.path.append(os.path.join(base_folder, "tools"))


# import as if this script was under tools/
import utils as jpmn_utils
import install as jpmn_install
import batch as jpmn_batch
import version as jpmn_version


# TODO change to not be using prerelease version
#SETUP_CHANGES_URL = "https://aquafina-water-bottle.github.io/jp-mining-note/setupchanges/"
SETUP_CHANGES_URL = "https://aquafina-water-bottle.github.io/jp-mining-note-prerelease/setupchanges/"
UPDATING_URL = "https://aquafina-water-bottle.github.io/jp-mining-note-prerelease/updating/"




def _get_collection():
    collection = mw.col
    if collection is None:
        raise Exception('collection is not available')

    return collection


def _get_version_from_anki(error=False, fallback_to_ankiconnect=True) -> jpmn_version.Version | None:
    """
    gets jpmn version from Anki, if installed.
    """

    MODEL_NAME = "JP Mining Note"

    model = _get_collection().models.byName(MODEL_NAME)
    if model is None:
        if error:
            raise Exception('model was not found: {}'.format(MODEL_NAME))
        return None

    # checks all sides before erroring
    for template in model['tmpls']:
        for side in [template['qfmt'], template['afmt']]: # front, back
            jpmn_version_str = jpmn_utils.get_version_from_template_side(side, error=error)
            if jpmn_version_str is not None:
                return jpmn_version.Version.from_str(jpmn_version_str)

    if fallback_to_ankiconnect:
        print("Falling back to jpmn_utils.get_version_from_anki...")
        jpmn_ver_anki = jpmn_utils.get_version_from_anki(MODEL_NAME)
        return jpmn_version.Version.from_str(jpmn_ver_anki)

    return None # explicit return


def check_updates():
    """
    compares version in template to version.txt
    """

    script_folder = os.path.dirname(os.path.abspath(__file__))
    version_file_path = os.path.join(script_folder, "version.txt")

    with open(version_file_path) as f:
        latest = jpmn_version.Version.from_str(f.read())

    def op_func():
        # NOTE: This is put in a QueryOp call because without one, Anki seems to deadlock itself.
        # I'm guessing it has to do with how we remain in the main thread, but Anki-Connect
        # itself runs in the main thread.
        return _get_version_from_anki()

    def success_func(curr: jpmn_version.Version):
        if curr is None:
            msg = f"Could not find the jp-mining-note version. Is the note installed?"
        elif latest.cmp(curr, check_prerelease=True) == 1: # latest > curr
            msg = f'An update to jp-mining-note is available!<br>- Current version: {curr}<br>- Latest version: {latest}<br>See how to update the note <a href="{UPDATING_URL}">here</a>.'
        else:
            msg = f"jp-mining-note is up to date. No update is necessary."
        showInfo(msg, textFormat="rich")

    op = QueryOp(
        parent=mw,
        op=lambda _: op_func(),
        success=lambda version: success_func(version),
    )

    msg = f"Querying Anki for the jp-mining-note version..."
    op.with_progress(msg).run_in_background()



def get_args(raw_args: str, *args: Callable[[argparse.ArgumentParser], None]) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    for add_args_func in args:
        add_args_func(parser)

    try:
        # we cannot rely on ArgumentParser(exit_on_error=False) to always throw an error
        # instead of exiting, so we use this gross hack to ensure Anki doesn't shut down...
        return parser.parse_args(args=shlex.split(raw_args))
    except SystemExit:
        raise RuntimeError("Error in arguments")


def install(update=False, args_str: str = ""):
    """
    installs or updates the note
    """

    args = get_args(args_str, jpmn_utils.add_args, jpmn_install.add_args)
    # because backup/ will be deleted on every addon update
    args.backup_folder = os.path.join("user_files", "backup")
    if update:
        args.update = True

    args.dev_never_warn = True # prevents input() from being ran
    args.dev_raise_anki_error = True # raises visible errors for Anki users to see, instead of silently returning

    def install_op():
        return jpmn_install.main(args)

    def install_success(post_message):
        msg = f"Successfully {'updated' if update else 'installed'} jp-mining-note!"
        if post_message is not None:
            msg += "<br><br>" + f'You\'re not finished yet! See the <a href="{SETUP_CHANGES_URL}">Setup Changes</a> page to update everything else.'
        #show_info(msg, textFormat=Qt.TextFormat.RichText) # RichText to make html work
        showInfo(msg, textFormat="rich") # RichText to make html work

    op = QueryOp(
        parent=mw,
        op=lambda _: install_op(),
        success=lambda post_message: install_success(post_message),
    )

    msg = f"{'Updating' if update else 'Installing'} jp-mining-note..."
    op.with_progress(msg).run_in_background()


def install_custom_args():
    (args_str, ret) = getText("Enter the installer arguments below.")
    if ret == 0: # user cancelled
        return
    install(args_str=args_str)


def confirm_update_warning():
    #warning_msg = ("Updating will override any changes you made to jp-mining-note! "
    #               "Please make a backup of your collection before continuing. "
    #               "If you already made a backup and are fine with losing any changes, "
    #               "press 'Ok'. Otherwise, please press 'cancel'.")

    #buttons = [QMessageBox.StandardButton.Ok, QMessageBox.StandardButton.Cancel]

    #def callback(idx: int):
    #    if idx == 0: # okay
    #        install(update=True)

    #ask_user_dialog(warning_msg, callback, buttons=buttons, default_button=1)


    CANCEL = "Cancel"
    UPDATE = "Update!"
    warning_msg = ("Updating will override any changes you made to jp-mining-note! "
                   "Please make a backup of your collection before continuing. "
                   "If you already made a backup and are fine with losing any changes, "
                   f"press '{UPDATE}'. Otherwise, please press 'cancel'.")

    buttons = [UPDATE, CANCEL]
    dialog = askUserDialog(warning_msg, buttons=buttons)
    dialog.setDefault(0)
    result = dialog.run()
    if result == UPDATE:
        install(update=True)


def run_batch():
    """
    runs batch.py function
    """

    (args_str, ret) = getText("Enter the batch command below.")
    if ret == 0: # user cancelled
        return
    args_arr = shlex.split(args_str)

    try:
        # we cannot rely on ArgumentParser(exit_on_error=False) to always throw an error
        # instead of exiting, so we use this gross hack to ensure Anki doesn't shut down...
        args = jpmn_batch.get_args(jpmn_batch.PUBLIC_FUNCTIONS_ANKI, args=args_arr)
    except SystemExit:
        raise RuntimeError("Error in arguments")

    if "func" in args:
        def batch_op():
            # code copied from batch main()
            time.sleep(1) # to ensure the popup is shown properly?
            try:
                func_args = vars(args)
                func = func_args.pop("func")
                return func(**func_args)
            except Exception as e:
                return e

        def batch_success(result):
            if isinstance(result, Exception):
                msg = str(result)
            else:
                msg = "Successfully ran batch command!"
                if result is not None:
                    msg += "\n\n" + result
            showInfo(msg)

        op = QueryOp(
            parent=mw,
            op=lambda _: batch_op(),
            success=lambda result: batch_success(result),
        )

        msg = f"Running batch script..."
        op.with_progress(msg).run_in_background()

    else:
        showInfo("Cannot find batch function")


def init_gui():
    menu = mw.form.menuTools.addMenu("JPMN Manager")

    check_update_action = QAction("Check for note updates", mw)
    qconnect(check_update_action.triggered, lambda: check_updates())
    menu.addAction(check_update_action)

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


def check_updates_popup(ignore_until_ver: jpmn_utils.Version | None):
    script_folder = os.path.dirname(os.path.abspath(__file__))
    version_file_path = os.path.join(script_folder, "version.txt")

    with open(version_file_path) as f:
        latest = jpmn_version.Version.from_str(f.read())

    # should be safe to not put in a background op, since ankiconnect call isn't used
    # calling a background op here seems to interfere with AJT Japanese
    curr = _get_version_from_anki(fallback_to_ankiconnect=False)

    if curr is None:
        msg = "(startup) Could not find the jp-mining-note version. Is the note installed?"
        print(msg)
    elif latest.cmp(curr, check_prerelease=True) == 1: # latest > curr
        # check if we ignore this
        # we ignore the update if ignore_until_ver >= latest
        if ignore_until_ver is not None and ignore_until_ver.cmp(latest, check_prerelease=True) >= 0: # ignore_until_ver >= current
            msg = f"(startup) A jp-mining-note update is available! However, this update is ignored by the user.\nIgnored until: {ignore_until_ver}\nCurrent version: {curr}\nLatest version: {latest}"
            print(msg)
        else:
            msg = f'An update to jp-mining-note is available!<br>- Current version: {curr}<br>- Latest version: {latest}<br>Selecting \'Okay\' will not update the note. See how to update the note <a href="{UPDATING_URL}">here</a>.'

            OKAY = "Okay"
            SKIP = "Skip update"
            NEVER_NOTIFY = "Never notify again"
            buttons = [OKAY, SKIP, NEVER_NOTIFY]
            bd = ButtonedDialog(msg, buttons, mw, title="JPMN Manager")
            bd.setIcon(QMessageBox.Icon.Information)
            bd.setTextFormat(Qt.TextFormat.RichText)
            bd.setDefault(0)

            # disables/ignores here
            selection = bd.run()
            if selection == SKIP:
                config = mw.addonManager.getConfig(__name__)
                config["check_update_ignore_until_ver"] = str(latest)
                mw.addonManager.writeConfig(__name__, config)
                tooltip(f"Notifications for {latest} will no longer show.")

            elif selection == NEVER_NOTIFY:
                config = mw.addonManager.getConfig(__name__)
                config["check_update_on_startup"] = False
                mw.addonManager.writeConfig(__name__, config)
                tooltip("There will be no update notifications in the future.")

    else:
        msg = f"(startup) jp-mining-note is up to date. No update is necessary."
        print(msg)


def optional_popup():
    config = mw.addonManager.getConfig(__name__)
    check_update = config["check_update_on_startup"]

    if check_update:
        ignore_until_ver_str = config["check_update_ignore_until_ver"]
        if ignore_until_ver_str is not None:
            ignore_until_ver = jpmn_version.Version.from_str(ignore_until_ver_str)
        else:
            ignore_until_ver = None
        check_updates_popup(ignore_until_ver)



init_gui()

# required for collection to be fully initialized
gui_hooks.main_window_did_init.append(optional_popup)

