# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Blank_ProcessWidget.ui'
##
## Created by: Qt User Interface Compiler version 6.9.1
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLineEdit, QSizePolicy,
    QToolButton, QVBoxLayout, QWidget)
import res_rc

class Ui_Form_Blank_ProcessWidget(object):
    def setupUi(self, Form_Blank_ProcessWidget):
        if not Form_Blank_ProcessWidget.objectName():
            Form_Blank_ProcessWidget.setObjectName(u"Form_Blank_ProcessWidget")
        Form_Blank_ProcessWidget.resize(250, 20)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Form_Blank_ProcessWidget.sizePolicy().hasHeightForWidth())
        Form_Blank_ProcessWidget.setSizePolicy(sizePolicy)
        Form_Blank_ProcessWidget.setMinimumSize(QSize(240, 20))
        Form_Blank_ProcessWidget.setMaximumSize(QSize(250, 20))
        Form_Blank_ProcessWidget.setBaseSize(QSize(250, 20))
        Form_Blank_ProcessWidget.setStyleSheet(u"background-color: rgb(30, 30, 30);")
        self.verticalLayout = QVBoxLayout(Form_Blank_ProcessWidget)
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.ProcessWidget = QWidget(Form_Blank_ProcessWidget)
        self.ProcessWidget.setObjectName(u"ProcessWidget")
        sizePolicy.setHeightForWidth(self.ProcessWidget.sizePolicy().hasHeightForWidth())
        self.ProcessWidget.setSizePolicy(sizePolicy)
        self.ProcessWidget.setMinimumSize(QSize(200, 20))
        self.ProcessWidget.setMaximumSize(QSize(300, 20))
        self.ProcessWidget.setBaseSize(QSize(190, 20))
        self.ProcessWidget.setStyleSheet(u" QLineEdit {\n"
"	background-color: rgb(50, 50, 50);\n"
"	color: rgb(255, 255, 255);\n"
"	border-radius: 0px;\n"
"	font: 10pt \"Arial\";\n"
"	border: none;\n"
"}\n"
"\n"
"QToolButton {\n"
"	color: rgb(255, 255, 255);\n"
"	background-color: rgb(30, 30, 30);\n"
"	border: 1px solid rgb(150, 150, 150);\n"
"	border-radius: 5px;\n"
"}\n"
"\n"
"QToolButton:hover {\n"
"	background-color: rgb(50, 60, 255);\n"
"}\n"
"\n"
"QToolButton:pressed {	\n"
"	color: rgb(255, 255, 255);\n"
"	background-color: rgb(50, 75, 255);\n"
"	border: 1px solid rgba(0, 170, 0, 255);\n"
"	border-radius: 5px;\n"
"}\n"
"\n"
"QToolButton:checked {\n"
"	background-color: rgb(30, 30, 30);\n"
"	border: 1px solid rgb(255, 255, 255);\n"
"}")
        self.horizontalLayout_202 = QHBoxLayout(self.ProcessWidget)
        self.horizontalLayout_202.setSpacing(5)
        self.horizontalLayout_202.setObjectName(u"horizontalLayout_202")
        self.horizontalLayout_202.setContentsMargins(0, 0, 0, 0)
        self.toolButton_ProcessActivation = QToolButton(self.ProcessWidget)
        self.toolButton_ProcessActivation.setObjectName(u"toolButton_ProcessActivation")
        self.toolButton_ProcessActivation.setMinimumSize(QSize(20, 20))
        self.toolButton_ProcessActivation.setMaximumSize(QSize(20, 20))
        icon = QIcon()
        icon.addFile(u":/icon/icons/alpha_chanal.png", QSize(), QIcon.Mode.Active, QIcon.State.Off)
        icon.addFile(u":/icon/icons/Check_White.svg", QSize(), QIcon.Mode.Active, QIcon.State.On)
        icon.addFile(u":/icon/icons/Check_White.svg", QSize(), QIcon.Mode.Selected, QIcon.State.On)
        self.toolButton_ProcessActivation.setIcon(icon)
        self.toolButton_ProcessActivation.setIconSize(QSize(14, 14))
        self.toolButton_ProcessActivation.setCheckable(True)

        self.horizontalLayout_202.addWidget(self.toolButton_ProcessActivation)

        self.toolButton_ActivatingVariables = QToolButton(self.ProcessWidget)
        self.toolButton_ActivatingVariables.setObjectName(u"toolButton_ActivatingVariables")
        self.toolButton_ActivatingVariables.setMinimumSize(QSize(20, 20))
        self.toolButton_ActivatingVariables.setMaximumSize(QSize(20, 20))
        icon1 = QIcon()
        icon1.addFile(u":/icon/icons/alpha_chanal.png", QSize(), QIcon.Mode.Disabled, QIcon.State.On)
        icon1.addFile(u":/icon/icons/folder-closed_white.svg", QSize(), QIcon.Mode.Active, QIcon.State.Off)
        icon1.addFile(u":/icon/icons/folder-opened.svg", QSize(), QIcon.Mode.Active, QIcon.State.On)
        icon1.addFile(u":/icon/icons/folder-closed_white.svg", QSize(), QIcon.Mode.Selected, QIcon.State.On)
        self.toolButton_ActivatingVariables.setIcon(icon1)
        self.toolButton_ActivatingVariables.setCheckable(True)
        self.toolButton_ActivatingVariables.setAutoRaise(True)

        self.horizontalLayout_202.addWidget(self.toolButton_ActivatingVariables)

        self.lineEdit_VariableName = QLineEdit(self.ProcessWidget)
        self.lineEdit_VariableName.setObjectName(u"lineEdit_VariableName")
        sizePolicy.setHeightForWidth(self.lineEdit_VariableName.sizePolicy().hasHeightForWidth())
        self.lineEdit_VariableName.setSizePolicy(sizePolicy)
        self.lineEdit_VariableName.setMinimumSize(QSize(100, 20))
        self.lineEdit_VariableName.setMaximumSize(QSize(225, 16777215))
        self.lineEdit_VariableName.setStyleSheet(u"")

        self.horizontalLayout_202.addWidget(self.lineEdit_VariableName)

        self.toolButton_DeletingVariable = QToolButton(self.ProcessWidget)
        self.toolButton_DeletingVariable.setObjectName(u"toolButton_DeletingVariable")
        self.toolButton_DeletingVariable.setMinimumSize(QSize(20, 20))
        self.toolButton_DeletingVariable.setMaximumSize(QSize(20, 20))
        icon2 = QIcon()
        icon2.addFile(u":/icon/icons/close_24dp.svg", QSize(), QIcon.Mode.Normal, QIcon.State.Off)
        self.toolButton_DeletingVariable.setIcon(icon2)
        self.toolButton_DeletingVariable.setAutoRaise(True)

        self.horizontalLayout_202.addWidget(self.toolButton_DeletingVariable)


        self.verticalLayout.addWidget(self.ProcessWidget)


        self.retranslateUi(Form_Blank_ProcessWidget)

        QMetaObject.connectSlotsByName(Form_Blank_ProcessWidget)
    # setupUi

    def retranslateUi(self, Form_Blank_ProcessWidget):
        Form_Blank_ProcessWidget.setWindowTitle(QCoreApplication.translate("Form_Blank_ProcessWidget", u"Form", None))
        self.toolButton_ProcessActivation.setText("")
        self.toolButton_ActivatingVariables.setText("")
        self.toolButton_DeletingVariable.setText(QCoreApplication.translate("Form_Blank_ProcessWidget", u"...", None))
    # retranslateUi

