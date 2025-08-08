import sys
import colorsys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem
)
from PyQt6.QtGui import QColor, QBrush, QPen
from PyQt6.QtCore import Qt
from pyqtgraph import mkPen


class DistinctColorGenerator:
    def __init__(self):
        self.index = 0
        self.used_colors = {}

    def get_color(self, key):
        if key in self.used_colors:
            return self.used_colors[key]

        # Large number of distinct colors using HSV spread
        h = (self.index * 0.61803398875) % 1  # Golden ratio ensures even hue spacing
        s = 0.8  # Saturation
        v = 0.95  # Brightness
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        color = QColor(int(r * 255), int(g * 255), int(b * 255))

        self.used_colors[key] = color
        self.index += 1
        return color


class TableWidgetOldPlots(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        # self.table.setRowCount(1000)
        
        self.table.setHorizontalHeaderLabels(["Run", "Color"])
        self.table.setSelectionBehavior(self.table.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(self.table.SelectionMode.MultiSelection)
        layout.addWidget(self.table)

        self.color_generator = DistinctColorGenerator()
        # self.populate_table()

        self.table.itemSelectionChanged.connect(self.on_selection_changed)

    def populate_table(self):
        for i in range(self.table.rowCount()):
            item_text = f"Item {i + 1}"
            item = QTableWidgetItem(item_text)
            item.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)  # Disable editing

            color_cell = QTableWidgetItem()
            color_cell.setFlags(Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled)  # Not selectable/editable

            self.table.setItem(i, 0, item)
            self.table.setItem(i, 1, color_cell)

    def on_selection_changed(self):

        self.selectedRuns={}

        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            color_cell = self.table.item(row, 1)

            if item.isSelected():
                key = item.text()
                color = self.color_generator.get_color(key)

                color_cell.setBackground(QBrush(color))
                color_cell.setToolTip(color.name())  # Show HEX color as tooltip

                pen = QPen(color)
                pen = mkPen(color, width=2)
                # pen.setWidth(1)
                self.selectedRuns[key]=pen
            else:
                color_cell.setBackground(QBrush(Qt.GlobalColor.white))
                color_cell.setToolTip("")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = TableWidgetOldPlots()
    window.show()
    sys.exit(app.exec())


