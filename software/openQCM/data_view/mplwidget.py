# ------------------------------------------------------
# -------------------- mplwidget.py --------------------
# ------------------------------------------------------
from PyQt5.QtWidgets import*

from matplotlib.backends.backend_qt5agg import FigureCanvas

from matplotlib.figure import Figure

    
class MplWidget(QWidget):
    
    def __init__(self, parent = None):

        QWidget.__init__(self, parent)
        
        # self.canvas = FigureCanvas(Figure())
        # VER 0.1.6 use tight_layout
        # using tight_layout adjust padding between and around subplots        
        # tight_layout() for FigureCanvasTkAgg
        # https://stackoverflow.com/a/62640384/4030282
        self.canvas = FigureCanvas(Figure(tight_layout=True))
        
        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.canvas)
        
        self.canvas.axes = self.canvas.figure.add_subplot(111)
        self.setLayout(vertical_layout)