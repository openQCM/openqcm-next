# VER 0.1.2
# importing from PyQt5 or PySide2 
try:
    from PyQt5 import QtGui
except:  
    from PySide2 import QtGui

TAG = "[PopUp]"

###############################################################################
# Warning dialog module
###############################################################################
class PopUp:
    
    ###########################################################################
    # Shows a Pop up warning dialog with a Ok buttons
    ###########################################################################
    @staticmethod
    def warning(parent, title, message):
        """
        :param parent: Parent window for the dialog.
        :param title: Title of the dialog :type title: str.
        :param message: Message to be shown in the dialog :type message: str.
        """
        QtGui.QMessageBox.warning(parent, title, message, QtGui.QMessageBox.Ok)

    # VER 0.1.4
    # a non blocking pop up window 
    ###########################################################################
    # Shows a Pop up warning dialog with a Ok buttons
    ###########################################################################
    @staticmethod
    def warning_not_blocking(parent, title, message):
        """
        :param parent: Parent window for the dialog.
        :param title: Title of the dialog :type title: str.
        :param message: Message to be shown in the dialog :type message: str.
        """
        msg = QtGui.QMessageBox(parent)
        msg.setIcon(QtGui.QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QtGui.QMessageBox.Ok)
        # solution on github here PyQt:Why a popup dialog prevents execution of other code?
        # https://stackoverflow.com/a/8463769/4030282
        msg.show()    
    
    
    # VER 0.1.6 a  blocking pop up window 
    # 
    ###########################################################################
    # Shows a Pop up warning dialog with a Ok buttons
    ###########################################################################
    @staticmethod
    def warning_blocking(parent, title, message):
        """
        :param parent: Parent window for the dialog.
        :param title: Title of the dialog :type title: str.
        :param message: Message to be shown in the dialog :type message: str.
        """
        msg = QtGui.QMessageBox(parent)
        msg.setIcon(QtGui.QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QtGui.QMessageBox.Ok)
        # solution on github here PyQt:Why a popup dialog prevents execution of other code?
        # https://stackoverflow.com/a/8463769/4030282
        msg.exec_()  

    ###########################################################################
    # Shows a pop-up question dialog with yes and no buttons
    ###########################################################################
    @staticmethod
    def question(parent, title, message):
        """
        :param parent: Parent window for the dialog.
        :param title: Title of the dialog :type title: str.
        :param message: Message to be shown in the dialog :type message: str.
        :return: True if Yes button was pressed :rtype: bool.
        """
        ans = QtGui.QMessageBox.question(parent, title, message, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        
        if ans == QtGui.QMessageBox.Yes:
            return True
        else:
            return False
        
    
    # VER 0.1.4
    # a non blocking pop up window question 
    ###########################################################################
    # Shows a Pop up question dialog with a Ok button and No button
    ###########################################################################
    @staticmethod
    def warning_exec(parent, title, message):
        """
        :param parent: Parent window for the dialog.
        :param title: Title of the dialog :type title: str.
        :param message: Message to be shown in the dialog :type message: str.
        """
        msg = QtGui.QMessageBox(parent)
        msg.setIcon(QtGui.QMessageBox.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.addButton(QtGui.QMessageBox.Yes)
        msg.addButton(QtGui.QMessageBox.No)
        msg.setDefaultButton(QtGui.QMessageBox.Yes)
        # solution on github here PyQt:Why a popup dialog prevents execution of other code?
        # https://stackoverflow.com/a/8463769/4030282
        
        yes_button = msg.button(QtGui.QMessageBox.Yes)
        no_button = msg.button(QtGui.QMessageBox.No)
        
        
        msg.exec_()

        if msg.clickedButton() == yes_button:
            return True
        elif msg.clickedButton() == no_button:
            return False
        
    
    # VER 0.1.4
    # a non blocking pop up window critical 
    ###########################################################################
    # Shows a Pop up question dialog with a Ok button and No button
    ###########################################################################
    @staticmethod
    def critical_exec(parent, title, message):
        """
        :param parent: Parent window for the dialog.
        :param title: Title of the dialog :type title: str.
        :param message: Message to be shown in the dialog :type message: str.
        """
        msg = QtGui.QMessageBox(parent)
        msg.setIcon(QtGui.QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.addButton(QtGui.QMessageBox.Yes)
        msg.addButton(QtGui.QMessageBox.No)
        msg.setDefaultButton(QtGui.QMessageBox.Yes)
        # solution on github here PyQt:Why a popup dialog prevents execution of other code?
        # https://stackoverflow.com/a/8463769/4030282
        
        yes_button = msg.button(QtGui.QMessageBox.Yes)
        no_button = msg.button(QtGui.QMessageBox.No)
        
        
        msg.exec_()

        if msg.clickedButton() == yes_button:
            return True
        elif msg.clickedButton() == no_button:
            return False
        
    # VER 0.1.4
    # a non blocking information pop up window 
    ###########################################################################
    # Shows a Pop up warning dialog with a Ok buttons
    ###########################################################################
    @staticmethod
    def info_not_blocking(parent, title, message):
        """
        :param parent: Parent window for the dialog.
        :param title: Title of the dialog :type title: str.
        :param message: Message to be shown in the dialog :type message: str.
        """
        msg = QtGui.QMessageBox(parent)
        msg.setIcon(QtGui.QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QtGui.QMessageBox.Ok)
        # solution on github here PyQt:Why a popup dialog prevents execution of other code?
        # https://stackoverflow.com/a/8463769/4030282
        msg.show()    
        
        
    # VER 0.1.4
    # a non blocking info pop up window using rich text 
    ###########################################################################
    # Shows a Pop up info dialog with a Ok buttons
    ###########################################################################
    @staticmethod
    def info_not_blocking_rtf(parent, title, message):
        msg = QtGui.QMessageBox(parent)
        msg.setIcon(QtGui.QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setTextFormat(1)
        msg.setText(message)
        msg.setStandardButtons(QtGui.QMessageBox.Ok)
        # solution on github here PyQt:Why a popup dialog prevents execution of other code?
        # https://stackoverflow.com/a/8463769/4030282
        msg.show()
        
    # VER 0.1.4
    # a non blocking info pop up window using rich text 
    ###########################################################################
    # Shows a Pop up info dialog with a Ok buttons
    ###########################################################################
    @staticmethod
    def info_exec_rtf(parent, title, message):
        msg = QtGui.QMessageBox(parent)
        msg.setIcon(QtGui.QMessageBox.Information)
        msg.setWindowTitle(title)
        msg.setTextFormat(1)
        msg.setText(message)
        msg.setStandardButtons(QtGui.QMessageBox.Ok)
        # solution on github here PyQt:Why a popup dialog prevents execution of other code?
        # https://stackoverflow.com/a/8463769/4030282
        msg.exec_()