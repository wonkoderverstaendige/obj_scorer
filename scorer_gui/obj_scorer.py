from PyQt5 import QtWidgets
from PyQt5 import QtCore
from scorer_gui.obj_scorer_ui import Ui_MainWindow
from scorer_gui.obj_scorer_model import CameraDevice, find_how_many_cameras


class ScorerMainWindow(QtWidgets.QMainWindow):
    key_action = QtCore.pyqtSignal(str, name="ScorerMainWindow.key_action")

    def __init__(self):
        # noinspection PyUnresolvedReferences
        flags_ = QtCore.Qt.WindowFlags()
        super(ScorerMainWindow, self).__init__(flags=flags_)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setMenuBar(self.ui.menubar)
        self._device = None
        self.ui.actionQuit.triggered.connect(self.close_all)
        self.ui.actionOpen_Camera.triggered.connect(self.get_camera_id_to_open)
        self.ui.actionOpen_File.triggered.connect(self.get_video_file_to_open)
        self.ui.actionSave_to.triggered.connect(self.get_save_video_file)
        self.ui.actionSave_to.setEnabled(False)
        self.ui.rawVideoCheckBox.setEnabled(False)
        self.ui.displayTsCheckBox.setChecked(True)

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, dev):
        self._device = dev
        if dev:
            # noinspection PyUnresolvedReferences
            self.key_action.connect(self._device.obj_state_change)
            self.ui.mirroredButton.setEnabled(True)
            self.ui.mirroredButton.toggled.connect(self.device.set_mirror)
            self.device.can_acquire_signal.connect(self.change_acquisition_state)
            self.device.is_acquiring_signal.connect(self.acquisition_started_stopped)
            self.device.is_paused_signal.connect(self.has_paused)
            self.device.video_finished_signal.connect(self.video_finished)
            self.device.frame_pos_signal.connect(self.ui.videoInSlider.setValue)
            self.ui.playButton.clicked.connect(self.device.start_acquisition)
            self.ui.pauseButton.clicked.connect(self.device.set_paused)
            self.ui.stopButton.clicked.connect(self.device.stop_acquisition)
            self.ui.videoInSlider.sliderMoved.connect(self.device.skip_to_frame)
            self.ui.rawVideoCheckBox.toggled.connect(self.device.set_raw_out)
            self.ui.rawVideoCheckBox.setChecked(True)
            self.ui.rawVideoCheckBox.setEnabled(True)
            self.ui.displayTsCheckBox.toggled.connect(self.device.set_display_time)
        self.ui.cameraWidget.set_device(self.device)

    @QtCore.pyqtSlot()
    def video_finished(self):
        msg = QtWidgets.QMessageBox()
        msg.setIcon(QtWidgets.QMessageBox.Information)

        msg.setText("Video Completed")
        msg.setStandardButtons(QtWidgets.QMessageBox.Ok | QtWidgets.QMessageBox.Cancel)
        msg.exec_()

    @QtCore.pyqtSlot(bool)
    def change_acquisition_state(self, can_acquire):
        self.ui.playButton.setEnabled(can_acquire)
        if can_acquire:
            self.ui.pauseButton.setEnabled(False)
            self.ui.stopButton.setEnabled(False)

    @QtCore.pyqtSlot(bool)
    def acquisition_started_stopped(self, val):
        self.ui.playButton.setEnabled(False)
        if val:
            self.ui.pauseButton.setEnabled(True)
            self.ui.stopButton.setEnabled(True)
            self.ui.scaleComboBox.setEnabled(False)
        else:
            self.ui.pauseButton.setEnabled(False)
            self.ui.stopButton.setEnabled(False)

    @QtCore.pyqtSlot(bool)
    def has_paused(self, val):
        if val:
            self.ui.playButton.setEnabled(True)
            self.ui.pauseButton.setEnabled(False)
            self.ui.stopButton.setEnabled(True)
        else:
            self.ui.playButton.setEnabled(False)
            self.ui.pauseButton.setEnabled(True)
            self.ui.stopButton.setEnabled(True)

    @QtCore.pyqtSlot()
    def close_all(self):
        import sys
        if self.device:
            self.device.cleanup()
        sys.exit()

    @QtCore.pyqtSlot()
    def get_camera_id_to_open(self):
        n_cameras = find_how_many_cameras()
        ops = [str(i) for i in range(n_cameras)]
        # noinspection PyCallByClass,PyTypeChecker,PyArgumentList
        dialog_out = QtWidgets.QInputDialog.getItem(self, "Open Camera", "Which camera id do you want to open?", ops)
        if not dialog_out[1]:
            return
        self.set_camera(int(dialog_out[0]))

    # noinspection PyArgumentList
    @QtCore.pyqtSlot()
    def get_video_file_to_open(self):
        import os
        # noinspection PyCallByClass,PyTypeChecker
        dialog_out = QtWidgets.QFileDialog.getOpenFileName(self, "Open Video File",
                                                           os.getcwd(), "Videos (*.avi)")
        open_video_file = dialog_out[0]
        if open_video_file:
            self.set_video(open_video_file)

    # noinspection PyArgumentList
    @QtCore.pyqtSlot()
    def get_save_video_file(self):
        import os
        # noinspection PyCallByClass,PyTypeChecker
        dialog_out = QtWidgets.QFileDialog.getSaveFileName(self, "Save Video File",
                                                           os.path.join(os.getcwd(), 'untitled.avi'),
                                                           "Videos (*.avi)")
        save_video_file = dialog_out[0]
        if save_video_file:
            self.device.set_out_video_file(save_video_file)
            self.ui.destLabel.setText(os.path.basename(save_video_file))
            self.ui.rawVideoCheckBox.setEnabled(False)

    def set_camera(self, camera_id):
        if self.device:
            self.device.cleanup()
        self.device = CameraDevice(camera_id=camera_id, mirrored=False)
        self.ui.sourceLabel.setText("Camera: " + str(camera_id))
        self.ui.videoInSlider.setEnabled(False)
        self.ui.actionSave_to.setEnabled(True)
        self.ui.scaleComboBox.addItems(self.device.scales_possible)
        self.ui.scaleComboBox.setCurrentIndex(self.device.scale_init)
        self.ui.scaleComboBox.setEnabled(True)
        self.ui.scaleComboBox.currentIndexChanged.connect(self.device.change_scale)


    def set_video(self, video_filename):
        import os
        if self.device:
            self.device.cleanup()
        self.device = CameraDevice(video_file=video_filename, mirrored=False)
        self.ui.sourceLabel.setText("File: " + os.path.basename(video_filename))
        last_frame = self.device.video_last_frame()
        self.ui.videoInSlider.setEnabled(True)
        self.ui.videoInSlider.setMinimum(0)
        self.ui.videoInSlider.setMaximum(last_frame)
        self.ui.actionSave_to.setEnabled(True)
        self.ui.scaleComboBox.setEnabled(False)

    def keyPressEvent(self, event):
        if self.device:
            if not event.isAutoRepeat() and event.key() in self.device.dir_keys:
                msg = CameraDevice.dir_keys[event.key()] + '1'
                self.key_action.emit(msg)
        event.accept()

    def keyReleaseEvent(self, event):
        if self.device:
            if event.key() in self.device.dir_keys:
                msg = CameraDevice.dir_keys[event.key()] + '0'
                self.key_action.emit(msg)
        event.accept()


def _main():
    import sys
    app = QtWidgets.QApplication(sys.argv)

    window = ScorerMainWindow()
    # window.device = CameraDevice(mirrored=True)
    window.show()
    app.quitOnLastWindowClosed = False
    # noinspection PyUnresolvedReferences
    app.lastWindowClosed.connect(window.close_all)
    app.exec_()


if __name__ == '__main__':
    _main()