#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import sys
from PySide import QtCore, QtGui


class SystemTrayIcon(QtGui.QSystemTrayIcon):

    def __init__(self, icon, parent=None):
        super(SystemTrayIcon, self).__init__(icon, parent)
        menu = QtGui.QMenu(parent)
        exitAction = menu.addAction("Exit")
        exitAction.triggered.connect(parent.close)
        self.setContextMenu(menu)


class MainWindow(QtGui.QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, 250, 150)
        self.setWindowTitle('Icon')
        self.tray_icon = SystemTrayIcon(QtGui.QIcon('favicon.ico'), self)
        self.tray_icon.show()
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file', 'C:\\')
        print(fname)
        self.show()


if __name__ == '__main__':
    app = QtGui.QApplication([])
    w = MainWindow()
    sys.exit(app.exec_())