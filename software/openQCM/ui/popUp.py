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
    # Shows a pop-up question dialog with yes and no buttons (unused)
    ###########################################################################
    @staticmethod
    def question_QCM(parent, title, message):
        """
        :param parent: Parent window for the dialog.
        :param title: Title of the dialog :type title: str.
        :param message: Message to be shown in the dialog :type message: str.
        :return: 1 if button1 was pressed, 0 if button2   :rtype: int.
        """
        #ans = QtGui.QMessageBox.question(parent, title, message, QtGui.QMessageBox.Yes, QtGui.QMessageBox.No)
        #if ans == QtGui.QMessageBox.Yes:
        #    print('Si')
        #    return True
        #elif ans == QtGui.QMessageBox.No:
        #    print('No')
        #    return False
        left = 700
        top = 400
        width = 340
        height = 220
        box = QtGui.QMessageBox(parent)
        box.setIcon(QtGui.QMessageBox.Question)
        box.setWindowTitle(title)
        box.setGeometry(left, top, width, height)
        box.setText(message)
        box.setStandardButtons(QtGui.QMessageBox.Yes|QtGui.QMessageBox.No)
        button1 = box.button(QtGui.QMessageBox.Yes)
        button1.setText('@10MHz')
        button2 = box.button(QtGui.QMessageBox.No)
        button2.setText(' @5MHz')
        box.exec_()
        
        if box.clickedButton() == button1:
            print(TAG, 'Quartz Crystal Sensor installed on the openQCM Device: @10MHz')
            return 1
        elif box.clickedButton() == button2:
            print(TAG, 'Quartz Crystal Sensor installed on the openQCM Device: @5MHz')
            return 0

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
        #msgBox=QtGui.QMessageBox.warning(parent, title, message, QtGui.QMessageBox.Ok)
        #msgBox = QtGui.QMessageBox()
        #msgBox.setIconPixmap( QtGui.QPixmap("favicon.png"))
        #msgBox.exec_() 

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
        
# =============================================================================
#         msg.setModal(True)
#         msg.show()
# =============================================================================    
        
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
        
# =============================================================================
#         msg.setModal(True)
#         msg.show()
# =============================================================================    
        
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
        # msg.show()
        msg.exec_()