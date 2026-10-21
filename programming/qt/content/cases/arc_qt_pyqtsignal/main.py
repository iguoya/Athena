# This Python file uses the following encoding: utf-8
import sys
from PySide2.QtWidgets import QApplication, QWidget, QMainWindow
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile, QIODevice

class main(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        # self.ui = QUiLoader().load('MainWindow.ui')
        


if __name__ == "__main__":
    app = QApplication([])
    # window = main()
    window = QUiLoader().load('MainWindow.ui')
    # window.ui = 
    window.show()
    sys.exit(app.exec_())
