# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'Dialog_WarningRename.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QProgressBar, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget)

class Ui_Dialog_WarningRename(object):
    def setupUi(self, Dialog_WarningRename):
        if not Dialog_WarningRename.objectName():
            Dialog_WarningRename.setObjectName(u"Dialog_WarningRename")
        Dialog_WarningRename.resize(421, 122)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog_WarningRename.sizePolicy().hasHeightForWidth())
        Dialog_WarningRename.setSizePolicy(sizePolicy)
        Dialog_WarningRename.setMinimumSize(QSize(421, 122))
        Dialog_WarningRename.setMaximumSize(QSize(421, 132))
        Dialog_WarningRename.setBaseSize(QSize(421, 122))
        Dialog_WarningRename.setStyleSheet(u"background-color: rgb(40, 40, 40);")
        self.widget_WarningRename1 = QWidget(Dialog_WarningRename)
        self.widget_WarningRename1.setObjectName(u"widget_WarningRename1")
        self.widget_WarningRename1.setGeometry(QRect(0, 0, 420, 122))
        sizePolicy.setHeightForWidth(self.widget_WarningRename1.sizePolicy().hasHeightForWidth())
        self.widget_WarningRename1.setSizePolicy(sizePolicy)
        self.widget_WarningRename1.setMinimumSize(QSize(420, 122))
        self.widget_WarningRename1.setMaximumSize(QSize(420, 122))
        self.widget_WarningRename1.setBaseSize(QSize(420, 122))
        self.widget_WarningRename1.setStyleSheet(u"background-color: rgb(30, 30, 30);\n"
"border: 1px solid rgb(255, 255, 255);\n"
"border-top: none;\n"
"border-bottom-left-radius: 5px;\n"
"border-bottom-right-radius: 5px;\n"
"border-top-left-radius: 0px;\n"
"border-top-right-radius: 0px;\n"
"")
        self.verticalLayout = QVBoxLayout(self.widget_WarningRename1)
        self.verticalLayout.setSpacing(5)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.verticalLayout.setContentsMargins(15, 25, 15, 15)
        self.widget_WarningRename2 = QWidget(self.widget_WarningRename1)
        self.widget_WarningRename2.setObjectName(u"widget_WarningRename2")
        sizePolicy.setHeightForWidth(self.widget_WarningRename2.sizePolicy().hasHeightForWidth())
        self.widget_WarningRename2.setSizePolicy(sizePolicy)
        self.widget_WarningRename2.setMinimumSize(QSize(390, 22))
        self.widget_WarningRename2.setMaximumSize(QSize(390, 22))
        self.widget_WarningRename2.setBaseSize(QSize(390, 22))
        self.widget_WarningRename2.setStyleSheet(u"QWidget {\n"
"	border: none;\n"
"}")
        self.horizontalLayout_2 = QHBoxLayout(self.widget_WarningRename2)
        self.horizontalLayout_2.setSpacing(0)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.lineEdit_EnterUniqueName = QLineEdit(self.widget_WarningRename2)
        self.lineEdit_EnterUniqueName.setObjectName(u"lineEdit_EnterUniqueName")
        sizePolicy.setHeightForWidth(self.lineEdit_EnterUniqueName.sizePolicy().hasHeightForWidth())
        self.lineEdit_EnterUniqueName.setSizePolicy(sizePolicy)
        self.lineEdit_EnterUniqueName.setMinimumSize(QSize(225, 22))
        self.lineEdit_EnterUniqueName.setMaximumSize(QSize(225, 22))
        self.lineEdit_EnterUniqueName.setBaseSize(QSize(225, 22))
        self.lineEdit_EnterUniqueName.setStyleSheet(u"background-color: rgb(50, 50, 50);\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 0px;\n"
"font: 10pt \"Arial\";\n"
"border-top: none;\n"
"border-left: none;\n"
"border-right: none;\n"
"border-bottom: none;")

        self.horizontalLayout_2.addWidget(self.lineEdit_EnterUniqueName)

        self.label_DuplicateWarning = QLabel(self.widget_WarningRename2)
        self.label_DuplicateWarning.setObjectName(u"label_DuplicateWarning")
        self.label_DuplicateWarning.setEnabled(True)
        sizePolicy.setHeightForWidth(self.label_DuplicateWarning.sizePolicy().hasHeightForWidth())
        self.label_DuplicateWarning.setSizePolicy(sizePolicy)
        self.label_DuplicateWarning.setMinimumSize(QSize(165, 22))
        self.label_DuplicateWarning.setMaximumSize(QSize(165, 22))
        self.label_DuplicateWarning.setSizeIncrement(QSize(0, 0))
        self.label_DuplicateWarning.setBaseSize(QSize(165, 22))
        self.label_DuplicateWarning.setStyleSheet(u"background-color: rgb(50, 50, 50);\n"
"color: rgba(255, 94, 0, 0);\n"
"border-radius: 0px;\n"
"font: 10pt \"Arial\";\n"
"border: none;")
        self.label_DuplicateWarning.setFrameShadow(QFrame.Shadow.Plain)

        self.horizontalLayout_2.addWidget(self.label_DuplicateWarning)


        self.verticalLayout.addWidget(self.widget_WarningRename2)

        self.progressBar_WarningRename = QProgressBar(self.widget_WarningRename1)
        self.progressBar_WarningRename.setObjectName(u"progressBar_WarningRename")
        sizePolicy.setHeightForWidth(self.progressBar_WarningRename.sizePolicy().hasHeightForWidth())
        self.progressBar_WarningRename.setSizePolicy(sizePolicy)
        self.progressBar_WarningRename.setMinimumSize(QSize(390, 22))
        self.progressBar_WarningRename.setMaximumSize(QSize(390, 22))
        self.progressBar_WarningRename.setBaseSize(QSize(390, 22))
        self.progressBar_WarningRename.setStyleSheet(u"border: none;")
        self.progressBar_WarningRename.setValue(0)
        self.progressBar_WarningRename.setTextVisible(False)

        self.verticalLayout.addWidget(self.progressBar_WarningRename)

        self.widget_WarningRename3 = QWidget(self.widget_WarningRename1)
        self.widget_WarningRename3.setObjectName(u"widget_WarningRename3")
        sizePolicy.setHeightForWidth(self.widget_WarningRename3.sizePolicy().hasHeightForWidth())
        self.widget_WarningRename3.setSizePolicy(sizePolicy)
        self.widget_WarningRename3.setMinimumSize(QSize(390, 28))
        self.widget_WarningRename3.setMaximumSize(QSize(390, 28))
        self.widget_WarningRename3.setBaseSize(QSize(390, 28))
        self.widget_WarningRename3.setStyleSheet(u"QWidget {\n"
"	border: none;\n"
"}\n"
"\n"
"QPushButton {\n"
"	color: rgb(180, 180, 180);\n"
"	font: 10pt \"Arial\";	\n"
"	background-color: rgba(0, 4, 255, 45);\n"
"	border: 1px solid rgb(80, 80, 80);\n"
"	border-radius: 5px;\n"
"}\n"
"\n"
"QPushButton:hover {\n"
"	background-color: rgb(40, 40, 40);\n"
"}\n"
"\n"
"QPushButton:pressed {	\n"
"	color: rgb(255, 255, 255);\n"
"	background-color: rgb(50, 50, 50);\n"
"	border: 1px solid rgb(0, 170, 0);\n"
"	border-radius: 5px;\n"
"}")
        self.horizontalLayout = QHBoxLayout(self.widget_WarningRename3)
        self.horizontalLayout.setSpacing(11)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 6, 0, 0)
        self.label_WarningRename = QLabel(self.widget_WarningRename3)
        self.label_WarningRename.setObjectName(u"label_WarningRename")
        sizePolicy.setHeightForWidth(self.label_WarningRename.sizePolicy().hasHeightForWidth())
        self.label_WarningRename.setSizePolicy(sizePolicy)
        self.label_WarningRename.setMinimumSize(QSize(234, 22))
        self.label_WarningRename.setMaximumSize(QSize(234, 22))
        self.label_WarningRename.setSizeIncrement(QSize(0, 0))
        self.label_WarningRename.setBaseSize(QSize(234, 22))
        self.label_WarningRename.setStyleSheet(u"background-color: rgb(30, 30, 30);\n"
"color: rgb(255, 255, 255);\n"
"border-radius: 0px;\n"
"font: 10pt \"Arial\";\n"
"border: none;")

        self.horizontalLayout.addWidget(self.label_WarningRename)

        self.pushButton_WarningRenameOk = QPushButton(self.widget_WarningRename3)
        self.pushButton_WarningRenameOk.setObjectName(u"pushButton_WarningRenameOk")
        sizePolicy.setHeightForWidth(self.pushButton_WarningRenameOk.sizePolicy().hasHeightForWidth())
        self.pushButton_WarningRenameOk.setSizePolicy(sizePolicy)
        self.pushButton_WarningRenameOk.setMinimumSize(QSize(67, 22))
        self.pushButton_WarningRenameOk.setMaximumSize(QSize(67, 22))
        self.pushButton_WarningRenameOk.setBaseSize(QSize(67, 22))

        self.horizontalLayout.addWidget(self.pushButton_WarningRenameOk)

        self.pushButton_WarningRenameCancel = QPushButton(self.widget_WarningRename3)
        self.pushButton_WarningRenameCancel.setObjectName(u"pushButton_WarningRenameCancel")
        sizePolicy.setHeightForWidth(self.pushButton_WarningRenameCancel.sizePolicy().hasHeightForWidth())
        self.pushButton_WarningRenameCancel.setSizePolicy(sizePolicy)
        self.pushButton_WarningRenameCancel.setMinimumSize(QSize(67, 22))
        self.pushButton_WarningRenameCancel.setMaximumSize(QSize(67, 22))
        self.pushButton_WarningRenameCancel.setBaseSize(QSize(67, 22))

        self.horizontalLayout.addWidget(self.pushButton_WarningRenameCancel)


        self.verticalLayout.addWidget(self.widget_WarningRename3)


        self.retranslateUi(Dialog_WarningRename)

        QMetaObject.connectSlotsByName(Dialog_WarningRename)
    # setupUi

    def retranslateUi(self, Dialog_WarningRename):
        Dialog_WarningRename.setWindowTitle(QCoreApplication.translate("Dialog_WarningRename", u"Dialog", None))
        self.lineEdit_EnterUniqueName.setPlaceholderText(QCoreApplication.translate("Dialog_WarningRename", u" \u0412\u0432\u043e\u0434 \u0443\u043d\u0438\u043a\u0430\u043b\u044c\u043d\u043e\u0433\u043e \u0438\u043c\u0435\u043d\u0438", None))
        self.label_DuplicateWarning.setText(QCoreApplication.translate("Dialog_WarningRename", u"<html><head/><body><p>\u0422\u0430\u043a\u043e\u0435 \u0438\u043c\u044f \u0443\u0436\u0435 \u0441\u0443\u0449\u0435\u0441\u0442\u0432\u0443\u0435\u0442</p></body></html>", None))
        self.progressBar_WarningRename.setFormat("")
        self.label_WarningRename.setText(QCoreApplication.translate("Dialog_WarningRename", u"\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u0435 \u0438\u043c\u044f \u0432 \u0442\u0435\u0447\u0435\u043d\u0438\u0438 60 \u0441\u0435\u043a\u0443\u043d\u0434", None))
        self.pushButton_WarningRenameOk.setText(QCoreApplication.translate("Dialog_WarningRename", u"Ok", None))
        self.pushButton_WarningRenameCancel.setText(QCoreApplication.translate("Dialog_WarningRename", u"Cancel", None))
    # retranslateUi

