# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'CommandEditorDialog.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QScrollArea, QSizePolicy,
    QSpacerItem, QVBoxLayout, QWidget)

class Ui_Dialog_CommandEditor(object):
    def setupUi(self, Dialog_CommandEditor):
        if not Dialog_CommandEditor.objectName():
            Dialog_CommandEditor.setObjectName(u"Dialog_CommandEditor")
        Dialog_CommandEditor.resize(800, 600)
        self.verticalLayout = QVBoxLayout(Dialog_CommandEditor)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label_command_name = QLabel(Dialog_CommandEditor)
        self.label_command_name.setObjectName(u"label_command_name")
        self.label_command_name.setAlignment(Qt.AlignCenter)

        self.verticalLayout.addWidget(self.label_command_name)

        self.horizontalLayout_keywords = QHBoxLayout()
        self.horizontalLayout_keywords.setObjectName(u"horizontalLayout_keywords")
        self.label_keywords = QLabel(Dialog_CommandEditor)
        self.label_keywords.setObjectName(u"label_keywords")

        self.horizontalLayout_keywords.addWidget(self.label_keywords)

        self.lineEdit_keywords = QLineEdit(Dialog_CommandEditor)
        self.lineEdit_keywords.setObjectName(u"lineEdit_keywords")

        self.horizontalLayout_keywords.addWidget(self.lineEdit_keywords)


        self.verticalLayout.addLayout(self.horizontalLayout_keywords)

        self.label_pseudocode = QLabel(Dialog_CommandEditor)
        self.label_pseudocode.setObjectName(u"label_pseudocode")

        self.verticalLayout.addWidget(self.label_pseudocode)

        self.scrollArea_pseudocode = QScrollArea(Dialog_CommandEditor)
        self.scrollArea_pseudocode.setObjectName(u"scrollArea_pseudocode")
        self.scrollArea_pseudocode.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 780, 450))
        self.verticalLayout_pseudocode = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_pseudocode.setSpacing(5)
        self.verticalLayout_pseudocode.setObjectName(u"verticalLayout_pseudocode")
        self.verticalLayout_pseudocode.setContentsMargins(5, 5, 5, 5)
        self.scrollArea_pseudocode.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea_pseudocode)

        self.horizontalLayout_buttons = QHBoxLayout()
        self.horizontalLayout_buttons.setObjectName(u"horizontalLayout_buttons")
        self.pushButton_test = QPushButton(Dialog_CommandEditor)
        self.pushButton_test.setObjectName(u"pushButton_test")

        self.horizontalLayout_buttons.addWidget(self.pushButton_test)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_buttons.addItem(self.horizontalSpacer)

        self.pushButton_save = QPushButton(Dialog_CommandEditor)
        self.pushButton_save.setObjectName(u"pushButton_save")

        self.horizontalLayout_buttons.addWidget(self.pushButton_save)

        self.pushButton_cancel = QPushButton(Dialog_CommandEditor)
        self.pushButton_cancel.setObjectName(u"pushButton_cancel")

        self.horizontalLayout_buttons.addWidget(self.pushButton_cancel)


        self.verticalLayout.addLayout(self.horizontalLayout_buttons)


        self.retranslateUi(Dialog_CommandEditor)

        QMetaObject.connectSlotsByName(Dialog_CommandEditor)
    # setupUi

    def retranslateUi(self, Dialog_CommandEditor):
        Dialog_CommandEditor.setWindowTitle(QCoreApplication.translate("Dialog_CommandEditor", u"\u0420\u0435\u0434\u0430\u043a\u0442\u043e\u0440 \u043a\u043e\u043c\u0430\u043d\u0434\u044b", None))
        self.label_command_name.setText(QCoreApplication.translate("Dialog_CommandEditor", u"\u0420\u0435\u0434\u0430\u043a\u0442\u043e\u0440 \u043a\u043e\u043c\u0430\u043d\u0434\u044b", None))
        self.label_keywords.setText(QCoreApplication.translate("Dialog_CommandEditor", u"\u041a\u043b\u044e\u0447\u0435\u0432\u044b\u0435 \u0441\u043b\u043e\u0432\u0430:", None))
        self.lineEdit_keywords.setPlaceholderText(QCoreApplication.translate("Dialog_CommandEditor", u"\u0412\u0432\u0435\u0434\u0438\u0442\u0435 \u043a\u043b\u044e\u0447\u0435\u0432\u044b\u0435 \u0441\u043b\u043e\u0432\u0430 \u0447\u0435\u0440\u0435\u0437 \u0437\u0430\u043f\u044f\u0442\u0443\u044e", None))
        self.label_pseudocode.setText(QCoreApplication.translate("Dialog_CommandEditor", u"\u041f\u0441\u0435\u0432\u0434\u043e\u043a\u043e\u0434:", None))
        self.pushButton_test.setText(QCoreApplication.translate("Dialog_CommandEditor", u"\u0422\u0435\u0441\u0442\u0438\u0440\u043e\u0432\u0430\u0442\u044c", None))
        self.pushButton_save.setText(QCoreApplication.translate("Dialog_CommandEditor", u"\u0421\u043e\u0445\u0440\u0430\u043d\u0438\u0442\u044c", None))
        self.pushButton_cancel.setText(QCoreApplication.translate("Dialog_CommandEditor", u"\u041e\u0442\u043c\u0435\u043d\u0430", None))
    # retranslateUi

