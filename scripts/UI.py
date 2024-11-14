import os
from threading import Thread

from ui.UI_VLCync import Ui_VLCync
from PyQt5 import QtGui
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog
from PyQt5.QtCore import pyqtSignal

from scripts.hash import getHash
from scripts.logger import VLCync_Logger
from scripts.common_toolkit import ClsCommonToolkit as CTK


class MainWindow(QMainWindow):
    consoleSignal = pyqtSignal()
    msgSignal = pyqtSignal(str, str)
    hashesMatch = False
    isFileSelected = False
    hasVoted = False
    safeDC = False

    def __init__(self, config, connection_handler, playerUtil):
        super(MainWindow, self).__init__()
        self.logger = VLCync_Logger.get_logger('Client')
        self.config = config
        self.connection_handler = connection_handler
        self.playerUtil = playerUtil
        # self.ignoreHash = self.config.getValue("default", "ignorehash")

        self.ui = Ui_VLCync()
        self.ui.setupUi(self)

        self.receptionThread = None

        self.toPg1()
        self.ui.liveConsoleOutput.setText("")

        self.consoleSignal.connect(self.unintentionalDC)
        self.msgSignal.connect(self.dispMessage)

        self.ui.inp_username.setText(self.connection_handler.def_usn)
        self.ui.inp_ip.setText(self.connection_handler.defaultAddr())
        self.ui.connectButton.clicked.connect(self.connectToServer)
        self.ui.disconnectButton.clicked.connect(self.intentionalDC)
        self.ui.mediaSelectButton.clicked.connect(self.selectMedia)
        self.ui.voteButton.clicked.connect(self.voteToggle)

        self.setWindowIcon(QtGui.QIcon("ui/logo.png"))
        self.show()

    def toPg2(self):
        self.ui.label_output.setText("")

        self.ui.stackedWidget.setCurrentWidget(self.ui.lobbyScreen)
        self.receptionThread = Thread(target=self.receiver)
        self.receptionThread.start()

    def toPg1(self):
        self.ui.liveConsoleOutput.setText("")
        self.ui.fileNameDisplay.setText("")
        self.hasVoted = False
        self.ui.voteButton.setText("Vote to start")

        if self.receptionThread is not None and self.receptionThread.is_alive():
            self.receptionThread.join()
        self.ui.stackedWidget.setCurrentWidget(self.ui.loginScreen)        

    def connectToServer(self):
        usn = self.ui.inp_username.text()
        try:
            CTK.is_valid_username(usn)
            if self.ui.inp_ip.text().lower() == "default":
                self.ui.inp_ip.setText("")

            CTK.is_valid_ip(self.ui.inp_ip.text())
            self.logger.debug(f"Server key = {self.ui.inp_password.text()}")
            addr, port = CTK.split_addr(self.ui.inp_ip.text())
            self.logger.info(f"Attempting connection with {addr}:{port} as {usn}")
            self.connection_handler.setKey(self.ui.inp_password.text())
            name, msg, _ = self.connection_handler.connect(addr, int(port), usn)

            self.dispMessage(name, msg)

            if self.connection_handler.isConnected:
                self.toPg2()
                self.config.saveUsername(self.ui.inp_username.text())
                self.config.saveServerAddr(self.ui.inp_ip.text())

        except Exception as e:
            self.logger.exception(str(e))
            self.ui.label_output.setText(f"<font color=red>{str(e)}</font>")

    def receiver(self):
        while self.connection_handler.isConnected:
            try: 
                stream = self.connection_handler.receive()
                if stream is True:
                    continue
                if stream is False:
                    self.consoleSignal.emit()
                    break

                name, msg, forVLC = stream
                self.logger.info(f"Received => {name}: {msg}")
                if forVLC:
                    self.playerUtil.outsideInput(msg)
                
                else:
                    self.msgParser(name, msg)
            
            except Exception as e:
                self.logger.exception(e)
                return e
        
        if not self.safeDC:
            self.consoleSignal.emit()

    def dispMessage(self, name, msg):
        old = self.ui.liveConsoleOutput.text()
        new = f"<font color=#04cc72>{name}</font>: <font color=#ddd>{msg}</font><br>"
        self.logger.debug(f"Wrote to liveConsole -> {name}:{msg}")
        # if not len(old):
        #     self.ui.liveConsoleOutput.setText(f"{new}")
        self.ui.liveConsoleOutput.setText(f"{old}{new}")

    def disconnectFromServer(self):
        try:
            if self.connection_handler.isConnected:
                self.connection_handler.disconnect()
            
            self.toPg1()

        except Exception as e:
            self.logger.exception(str(e))
            self.ui.liveConsoleOutput.setText(f"<font color=red>{str(e)}</font>")

    def intentionalDC(self):
        self.safeDC = True
        self.disconnectFromServer()
        self.logger.info("Safely disconnected from server")

    def unintentionalDC(self):
        self.disconnectFromServer()
        self.ui.label_output.setText(f"<font color=red>Connection lost</font>")
        self.logger.error("Connection lost!")

    def selectMedia(self):
        file_addr = QFileDialog.getOpenFileName()[0]
        # self.logger.debug(f"{file_addr.split('/')}, {type(file_addr.split('/'))}")
        if os.name=="nt":
            file_addr = file_addr.replace('/', "\\")
        try:
            file_hash = getHash(file_addr)
            self.logger.debug(f"{file_addr} -> {file_hash}")
        except Exception as e:
            self.logger.exception(str(e))
            self.ui.fileNameDisplay.setText(str(e))
            return

        self.logger.info(f"Selected {file_addr}")
        self.dispMessage("You", f"Selected {file_addr}")
        self.file_path = file_addr
        self.ui.fileNameDisplay.setText(file_addr)
        self.isFileSelected = True
        self.connection_handler.send(f"SELECTED FILE HASH={file_hash}", False)

    def voteToggle(self):
        if self.isFileSelected and self.hashesMatch and not self.hasVoted:
            self.hasVoted = True
            self.connection_handler.send("VOTE", False)
            self.logger.info("Voted notified")
            self.ui.voteButton.setText("Unvote")
            return

        if self.hasVoted:
            self.hasVoted = False
            self.connection_handler.send("UNVOTE", False)
            self.logger.info("Vote withdrawal notified")
            self.ui.voteButton.setText("Vote to start")
            return

        if self.isFileSelected and not self.hashesMatch:
            self.logger.info("Attempted voting without file verification")
            self.dispMessage("CLIENT", "Please wait for others to select files and server to verify file.")
            return

        self.logger.info("Attempted vote without selecting file")
        self.dispMessage("CLIENT", "Please select a file before voting")

    def msgParser(self, name, msg):
        if msg.isupper():
            if "HASHES MATCH" in msg:
                self.msgSignal.emit(name, "Files match!")
                self.hashesMatch = True
                return

            if "HASHES DO NOT MATCH" in msg:
                self.msgSignal.emit(name, "Files do not match")
                return

            if "HASH BOOL RESET" in msg:
                self.hashesMatch = False
                return

            if "EVERYONE HAS VOTED" in msg:
                self.playerUtil.beginPlayback(self.file_path)
                return

        self.msgSignal.emit(name, msg)        


def run_ui(config, connection_handler, playerUtil):
    app = QApplication([])
    window = MainWindow(config, connection_handler, playerUtil)
    app.exec_()
