# Form implementation generated from reading ui file '/Users/gmondeel/Documents/MIT/NEPTUNE/BigGUI/BigSkyController/GuiBigSkyWidget.ui'
#
# Created by: PyQt6 UI code generator 6.9.0
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt6 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(774, 741)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setObjectName("formLayout")
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(24)
        font.setBold(True)
        font.setWeight(75)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.verticalLayout_8 = QtWidgets.QVBoxLayout()
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.qSwitchLabel = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.qSwitchLabel.setFont(font)
        self.qSwitchLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignTop)
        self.qSwitchLabel.setObjectName("qSwitchLabel")
        self.verticalLayout_8.addWidget(self.qSwitchLabel)
        self.qSwitchRadioButton_0 = QtWidgets.QRadioButton(parent=Form)
        self.qSwitchRadioButton_0.setChecked(True)
        self.qSwitchRadioButton_0.setObjectName("qSwitchRadioButton_0")
        self.buttonGroup_2 = QtWidgets.QButtonGroup(Form)
        self.buttonGroup_2.setObjectName("buttonGroup_2")
        self.buttonGroup_2.addButton(self.qSwitchRadioButton_0)
        self.verticalLayout_8.addWidget(self.qSwitchRadioButton_0)
        self.qSwitchRadioButton_1 = QtWidgets.QRadioButton(parent=Form)
        self.qSwitchRadioButton_1.setObjectName("qSwitchRadioButton_1")
        self.buttonGroup_2.addButton(self.qSwitchRadioButton_1)
        self.verticalLayout_8.addWidget(self.qSwitchRadioButton_1)
        self.qSwitchRadioButton_2 = QtWidgets.QRadioButton(parent=Form)
        self.qSwitchRadioButton_2.setObjectName("qSwitchRadioButton_2")
        self.buttonGroup_2.addButton(self.qSwitchRadioButton_2)
        self.verticalLayout_8.addWidget(self.qSwitchRadioButton_2)
        self.horizontalLayout_5.addLayout(self.verticalLayout_8)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_5.addItem(spacerItem)
        self.verticalLayout_9 = QtWidgets.QVBoxLayout()
        self.verticalLayout_9.setObjectName("verticalLayout_9")
        self.flashLampLabel = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(12)
        self.flashLampLabel.setFont(font)
        self.flashLampLabel.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignTop)
        self.flashLampLabel.setObjectName("flashLampLabel")
        self.verticalLayout_9.addWidget(self.flashLampLabel)
        self.flashLampRadioButton_0 = QtWidgets.QRadioButton(parent=Form)
        self.flashLampRadioButton_0.setChecked(True)
        self.flashLampRadioButton_0.setObjectName("flashLampRadioButton_0")
        self.buttonGroup = QtWidgets.QButtonGroup(Form)
        self.buttonGroup.setObjectName("buttonGroup")
        self.buttonGroup.addButton(self.flashLampRadioButton_0)
        self.verticalLayout_9.addWidget(self.flashLampRadioButton_0)
        self.flashLampRadioButton_1 = QtWidgets.QRadioButton(parent=Form)
        self.flashLampRadioButton_1.setObjectName("flashLampRadioButton_1")
        self.buttonGroup.addButton(self.flashLampRadioButton_1)
        self.verticalLayout_9.addWidget(self.flashLampRadioButton_1)
        self.horizontalLayout_5.addLayout(self.verticalLayout_9)
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.FrequencyLabel = QtWidgets.QLabel(parent=Form)
        self.FrequencyLabel.setObjectName("FrequencyLabel")
        self.horizontalLayout.addWidget(self.FrequencyLabel)
        self.frequencyDoubleSpinBox = QtWidgets.QDoubleSpinBox(parent=Form)
        self.frequencyDoubleSpinBox.setMaximum(56.0)
        self.frequencyDoubleSpinBox.setSingleStep(0.01)
        self.frequencyDoubleSpinBox.setObjectName("frequencyDoubleSpinBox")
        self.horizontalLayout.addWidget(self.frequencyDoubleSpinBox)
        self.frequencyUnitsLabel = QtWidgets.QLabel(parent=Form)
        self.frequencyUnitsLabel.setObjectName("frequencyUnitsLabel")
        self.horizontalLayout.addWidget(self.frequencyUnitsLabel)
        self.verticalLayout_3.addLayout(self.horizontalLayout)
        self.frequencyConfirmationButton = QtWidgets.QPushButton(parent=Form)
        self.frequencyConfirmationButton.setObjectName("frequencyConfirmationButton")
        self.verticalLayout_3.addWidget(self.frequencyConfirmationButton)
        self.horizontalLayout_5.addLayout(self.verticalLayout_3)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.laserSaveButton = QtWidgets.QPushButton(parent=Form)
        self.laserSaveButton.setObjectName("laserSaveButton")
        self.verticalLayout_4.addWidget(self.laserSaveButton)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Expanding)
        self.verticalLayout_4.addItem(spacerItem1)
        self.horizontalLayout_5.addLayout(self.verticalLayout_4)
        self.verticalLayout.addLayout(self.horizontalLayout_5)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout()
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.flashLampVoltageLabel = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.flashLampVoltageLabel.setFont(font)
        self.flashLampVoltageLabel.setObjectName("flashLampVoltageLabel")
        self.horizontalLayout_3.addWidget(self.flashLampVoltageLabel)
        self.flashLampVoltageLineEdit = QtWidgets.QLineEdit(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.flashLampVoltageLineEdit.setFont(font)
        self.flashLampVoltageLineEdit.setMaxLength(4)
        self.flashLampVoltageLineEdit.setObjectName("flashLampVoltageLineEdit")
        self.horizontalLayout_3.addWidget(self.flashLampVoltageLineEdit)
        self.label_3 = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label_3.setFont(font)
        self.label_3.setObjectName("label_3")
        self.horizontalLayout_3.addWidget(self.label_3)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_3.addItem(spacerItem2)
        self.verticalLayout_7.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2.addLayout(self.verticalLayout_7)
        spacerItem3 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem3)
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.lastUpdateOutput = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.lastUpdateOutput.setFont(font)
        self.lastUpdateOutput.setObjectName("lastUpdateOutput")
        self.gridLayout.addWidget(self.lastUpdateOutput, 4, 1, 1, 1)
        self.flashLampEnergyLabel = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.flashLampEnergyLabel.setFont(font)
        self.flashLampEnergyLabel.setObjectName("flashLampEnergyLabel")
        self.gridLayout.addWidget(self.flashLampEnergyLabel, 1, 0, 1, 1)
        self.temperatureOutput = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.temperatureOutput.setFont(font)
        self.temperatureOutput.setObjectName("temperatureOutput")
        self.gridLayout.addWidget(self.temperatureOutput, 3, 1, 1, 1)
        self.PowerEstimateLabel = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.PowerEstimateLabel.setFont(font)
        self.PowerEstimateLabel.setObjectName("PowerEstimateLabel")
        self.gridLayout.addWidget(self.PowerEstimateLabel, 2, 0, 1, 1)
        self.temperatureLabel = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.temperatureLabel.setFont(font)
        self.temperatureLabel.setObjectName("temperatureLabel")
        self.gridLayout.addWidget(self.temperatureLabel, 3, 0, 1, 1)
        self.flashLampEnergyValue = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.flashLampEnergyValue.setFont(font)
        self.flashLampEnergyValue.setObjectName("flashLampEnergyValue")
        self.gridLayout.addWidget(self.flashLampEnergyValue, 1, 1, 1, 1)
        self.lastUpdateLabel = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.lastUpdateLabel.setFont(font)
        self.lastUpdateLabel.setObjectName("lastUpdateLabel")
        self.gridLayout.addWidget(self.lastUpdateLabel, 4, 0, 1, 1)
        self.PowerEstimateValue = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(9)
        self.PowerEstimateValue.setFont(font)
        self.PowerEstimateValue.setObjectName("PowerEstimateValue")
        self.gridLayout.addWidget(self.PowerEstimateValue, 2, 1, 1, 1)
        self.horizontalLayout_2.addLayout(self.gridLayout)
        spacerItem4 = QtWidgets.QSpacerItem(1, 20, QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem4)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.verticalLayout.addLayout(self.horizontalLayout_4)
        self.lampActivationButton = QtWidgets.QPushButton(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.lampActivationButton.setFont(font)
        self.lampActivationButton.setObjectName("lampActivationButton")
        self.verticalLayout.addWidget(self.lampActivationButton)
        self.stopButton = QtWidgets.QPushButton(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(16)
        self.stopButton.setFont(font)
        self.stopButton.setObjectName("stopButton")
        self.verticalLayout.addWidget(self.stopButton)
        self.horizontalLayout_6 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_6.setObjectName("horizontalLayout_6")
        self.terminalOutputLabel = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.terminalOutputLabel.setFont(font)
        self.terminalOutputLabel.setObjectName("terminalOutputLabel")
        self.horizontalLayout_6.addWidget(self.terminalOutputLabel)
        self.terminalOutputTextBrowser = QtWidgets.QTextBrowser(parent=Form)
        self.terminalOutputTextBrowser.setObjectName("terminalOutputTextBrowser")
        self.horizontalLayout_6.addWidget(self.terminalOutputTextBrowser)
        self.verticalLayout.addLayout(self.horizontalLayout_6)
        self.horizontalLayout_7 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_7.setObjectName("horizontalLayout_7")
        self.toggleInputButton = QtWidgets.QPushButton(parent=Form)
        self.toggleInputButton.setObjectName("toggleInputButton")
        self.horizontalLayout_7.addWidget(self.toggleInputButton)
        self.terminalInputLabel = QtWidgets.QLabel(parent=Form)
        self.terminalInputLabel.setEnabled(True)
        font = QtGui.QFont()
        font.setPointSize(10)
        self.terminalInputLabel.setFont(font)
        self.terminalInputLabel.setObjectName("terminalInputLabel")
        self.horizontalLayout_7.addWidget(self.terminalInputLabel)
        self.terminalInputLineEdit = QtWidgets.QLineEdit(parent=Form)
        self.terminalInputLineEdit.setEnabled(True)
        self.terminalInputLineEdit.setObjectName("terminalInputLineEdit")
        self.horizontalLayout_7.addWidget(self.terminalInputLineEdit)
        self.verticalLayout.addLayout(self.horizontalLayout_7)
        self.formLayout.setLayout(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.verticalLayout)
        self.label_2 = QtWidgets.QLabel(parent=Form)
        font = QtGui.QFont()
        font.setPointSize(6)
        self.label_2.setFont(font)
        self.label_2.setAlignment(QtCore.Qt.AlignmentFlag.AlignBottom|QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing)
        self.label_2.setObjectName("label_2")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.label_2)
        self.verticalLayout_2.addLayout(self.formLayout)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label.setText(_translate("Form", "BIG SKY [SN] LASER CONTROL"))
        self.qSwitchLabel.setText(_translate("Form", "QSwitch\n"
"Trigger Setting"))
        self.qSwitchRadioButton_0.setText(_translate("Form", "Internal"))
        self.qSwitchRadioButton_1.setText(_translate("Form", "Burst"))
        self.qSwitchRadioButton_2.setText(_translate("Form", "External"))
        self.flashLampLabel.setText(_translate("Form", "Flash Lamp\n"
"Trigger Setting"))
        self.flashLampRadioButton_0.setText(_translate("Form", "Internal"))
        self.flashLampRadioButton_1.setText(_translate("Form", "External"))
        self.FrequencyLabel.setText(_translate("Form", "Pulse Rate:\n"
"(press \"Enter\" to confirm)"))
        self.frequencyUnitsLabel.setText(_translate("Form", "Hz"))
        self.frequencyConfirmationButton.setText(_translate("Form", "Confirm Frequency"))
        self.laserSaveButton.setText(_translate("Form", "Save Laser Settings"))
        self.flashLampVoltageLabel.setText(_translate("Form", "Flashlamp Voltage"))
        self.label_3.setText(_translate("Form", "V"))
        self.lastUpdateOutput.setText(_translate("Form", "TODO"))
        self.flashLampEnergyLabel.setText(_translate("Form", "Flashlamp Energy:"))
        self.temperatureOutput.setText(_translate("Form", "TODO"))
        self.PowerEstimateLabel.setText(_translate("Form", "Approximate\n"
"Power @ 10Hz:"))
        self.temperatureLabel.setText(_translate("Form", "Temperature: "))
        self.flashLampEnergyValue.setText(_translate("Form", "TODO"))
        self.lastUpdateLabel.setText(_translate("Form", "Last Updated:"))
        self.PowerEstimateValue.setText(_translate("Form", "TODO"))
        self.lampActivationButton.setText(_translate("Form", "START"))
        self.stopButton.setText(_translate("Form", "STOP"))
        self.terminalOutputLabel.setText(_translate("Form", "Terminal\n"
"Output:"))
        self.toggleInputButton.setText(_translate("Form", "Toggle \n"
"terminal input"))
        self.terminalInputLabel.setText(_translate("Form", "Terminal\n"
"Commands:\n"
"(Advanced)"))
        self.label_2.setText(_translate("Form", "Questions: alexjbrinson@gmail.com"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Form = QtWidgets.QWidget()
    ui = Ui_Form()
    ui.setupUi(Form)
    Form.show()
    sys.exit(app.exec())
