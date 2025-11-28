# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'DeletionWarning.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QGridLayout, QLabel,
    QProgressBar, QPushButton, QSizePolicy, QWidget)

class Ui_Dialog_DeletionWarning(object):
    def setupUi(self, Dialog_DeletionWarning):
        if not Dialog_DeletionWarning.objectName():
            Dialog_DeletionWarning.setObjectName(u"Dialog_DeletionWarning")
        Dialog_DeletionWarning.resize(463, 116)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Dialog_DeletionWarning.sizePolicy().hasHeightForWidth())
        Dialog_DeletionWarning.setSizePolicy(sizePolicy)
        Dialog_DeletionWarning.setMinimumSize(QSize(463, 116))
        Dialog_DeletionWarning.setMaximumSize(QSize(463, 184))
        Dialog_DeletionWarning.setBaseSize(QSize(463, 116))
        Dialog_DeletionWarning.setStyleSheet(u"background-color: rgb(40, 40, 40);\n"
"\n"
"")
        self.widget_DeletionWarning = QWidget(Dialog_DeletionWarning)
        self.widget_DeletionWarning.setObjectName(u"widget_DeletionWarning")
        self.widget_DeletionWarning.setGeometry(QRect(0, 0, 463, 116))
        sizePolicy.setHeightForWidth(self.widget_DeletionWarning.sizePolicy().hasHeightForWidth())
        self.widget_DeletionWarning.setSizePolicy(sizePolicy)
        self.widget_DeletionWarning.setMinimumSize(QSize(463, 116))
        self.widget_DeletionWarning.setMaximumSize(QSize(463, 116))
        self.widget_DeletionWarning.setBaseSize(QSize(463, 116))
        self.widget_DeletionWarning.setStyleSheet(u"QWidget {\n"
"	background-color: rgb(30, 30, 30);\n"
"	border: 1px solid rgb(255, 255, 255);\n"
"	border-top: none;\n"
"	border-bottom-left-radius: 5px;\n"
"	border-bottom-right-radius: 5px;\n"
"	border-top-left-radius: 0px;\n"
"	border-top-right-radius: 0px;\n"
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
"}\n"
"\n"
"QPushButton:checked {\n"
"	background-color: rgb(30, 30, 30);\n"
"	border: 1px solid rgb(255, 255, 255);\n"
"}\n"
"\n"
"QLabel {\n"
"	background-color: rgb(30, 30, 30);\n"
"	color: rgb(255, 255, 255);\n"
"	border-radius: 0px;\n"
"	font: 10pt \"Arial\";\n"
"	border: none;\n"
"}")
        self.gridLayout = QGridLayout(self.widget_DeletionWarning)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setHorizontalSpacing(15)
        self.gridLayout.setVerticalSpacing(10)
        self.gridLayout.setContentsMargins(15, 15, 15, 15)
        self.pushButton_Ok = QPushButton(self.widget_DeletionWarning)
        self.pushButton_Ok.setObjectName(u"pushButton_Ok")
        self.pushButton_Ok.setMinimumSize(QSize(67, 22))
        self.pushButton_Ok.setMaximumSize(QSize(67, 54))
        self.pushButton_Ok.setBaseSize(QSize(67, 54))

        self.gridLayout.addWidget(self.pushButton_Ok, 2, 1, 1, 1)

        self.progressBar_Warning = QProgressBar(self.widget_DeletionWarning)
        self.progressBar_Warning.setObjectName(u"progressBar_Warning")
        sizePolicy.setHeightForWidth(self.progressBar_Warning.sizePolicy().hasHeightForWidth())
        self.progressBar_Warning.setSizePolicy(sizePolicy)
        self.progressBar_Warning.setMinimumSize(QSize(433, 22))
        self.progressBar_Warning.setMaximumSize(QSize(433, 22))
        self.progressBar_Warning.setBaseSize(QSize(433, 22))
        self.progressBar_Warning.setStyleSheet(u"border: none;")
        self.progressBar_Warning.setValue(0)
        self.progressBar_Warning.setTextVisible(False)

        self.gridLayout.addWidget(self.progressBar_Warning, 0, 0, 1, 3)

        self.pushButton_WarningCancel = QPushButton(self.widget_DeletionWarning)
        self.pushButton_WarningCancel.setObjectName(u"pushButton_WarningCancel")
        self.pushButton_WarningCancel.setMinimumSize(QSize(67, 22))
        self.pushButton_WarningCancel.setMaximumSize(QSize(67, 22))
        self.pushButton_WarningCancel.setBaseSize(QSize(67, 22))

        self.gridLayout.addWidget(self.pushButton_WarningCancel, 2, 2, 1, 1)

        self.label_Warning = QLabel(self.widget_DeletionWarning)
        self.label_Warning.setObjectName(u"label_Warning")
        sizePolicy.setHeightForWidth(self.label_Warning.sizePolicy().hasHeightForWidth())
        self.label_Warning.setSizePolicy(sizePolicy)
        self.label_Warning.setMinimumSize(QSize(433, 22))
        self.label_Warning.setMaximumSize(QSize(433, 22))
        self.label_Warning.setBaseSize(QSize(433, 22))
        self.label_Warning.setStyleSheet(u"")

        self.gridLayout.addWidget(self.label_Warning, 1, 0, 1, 1)

        self.label_Warning_2 = QLabel(self.widget_DeletionWarning)
        self.label_Warning_2.setObjectName(u"label_Warning_2")
        sizePolicy.setHeightForWidth(self.label_Warning_2.sizePolicy().hasHeightForWidth())
        self.label_Warning_2.setSizePolicy(sizePolicy)
        self.label_Warning_2.setMinimumSize(QSize(269, 22))
        self.label_Warning_2.setMaximumSize(QSize(269, 22))
        self.label_Warning_2.setBaseSize(QSize(269, 22))

        self.gridLayout.addWidget(self.label_Warning_2, 2, 0, 1, 1)


        self.retranslateUi(Dialog_DeletionWarning)

        QMetaObject.connectSlotsByName(Dialog_DeletionWarning)
    # setupUi

    def retranslateUi(self, Dialog_DeletionWarning):
        Dialog_DeletionWarning.setWindowTitle(QCoreApplication.translate("Dialog_DeletionWarning", u"Dialog", None))
        self.pushButton_Ok.setText(QCoreApplication.translate("Dialog_DeletionWarning", u"Ok", None))
        self.progressBar_Warning.setFormat("")
        self.pushButton_WarningCancel.setText(QCoreApplication.translate("Dialog_DeletionWarning", u"Cancel", None))
        self.label_Warning.setText(QCoreApplication.translate("Dialog_DeletionWarning", u"\u041f\u043e\u0434\u0442\u0432\u0435\u0440\u0434\u0438\u0442\u0435 \u0443\u0434\u0430\u043b\u0435\u043d\u0438\u0435 \u0432 \u0442\u0435\u0447\u0435\u043d\u0438\u0435 20 \u0441\u0435\u043a\u0443\u043d\u0434", None))
        self.label_Warning_2.setText("")
    # retranslateUi

