    def closeEvent(self, event):
        quit_msg = "Are you sure you want to quit?"
        reply = JMQtMessageBox(self, quit_msg, mbtype='question')
        if reply == QMessageBox.Yes:
            event.accept()
            if self.reactor.threadpool is not None:
                self.reactor.threadpool.stop()
            stop_reactor()
        else:
            event.ignore()