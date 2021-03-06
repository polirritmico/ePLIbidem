#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright © 2021 Titivillus
# www.epublibre.org
# Distributed under the terms of the GNU General Public License v2

from src.note import Note
from src.highlight import highlight
from src.regex import REGEX_SPLIT_IBID
from collections import OrderedDict
try:
    from PyQt5 import uic, QtWidgets
    from PyQt5.QtCore import QEvent, QTimer
    from PyQt5.QtWidgets import QTreeWidgetItem
    from PyQt5.QtGui import QIcon
except Exception as e:
    print("Error en linea {}: ".format(sys.exc_info()[-1].tb_lineno), type(
        e).__name__, e, "\n\nEste plugin requiere Sigil >0.9.8 y PyQt5.")
    sys.exit()


class ConfigWindow(QtWidgets.QDialog):
    def __init__(self, dark_theme, path, bk):
        super(ConfigWindow, self).__init__()
        uic.loadUi(path + "configWindow.ui", self)

        self.bk = CopyBK() if bk is None else bk

        # Set Icons
        if dark_theme:
            theme = ":/dark-theme/"
        else:
            theme = ":/light-theme/"
        self.DialogAcceptButton.setIcon(QIcon(theme + "dialog-ok-apply.svg"))
        self.DialogCancelButton.setIcon(QIcon(theme + "dialog-cancel.svg"))

        # Connect Buttons
        self.DialogAcceptButton.clicked.connect(self.acceptButton_pressed)
        self.DialogDefaultButton.clicked.connect(self.defaultButton_pressed)
        self.DialogCancelButton.clicked.connect(self.cancelButton_pressed)
        self.TestButton.clicked.connect(self.testButton_pressed)

        # Preferences
        self.regex_search_list = ["Default", "Personalizada"]
        self.regex_search_entries = [REGEX_SPLIT_IBID, REGEX_SPLIT_IBID]

        self.ibid_label_list = [
            "<i>Ibid</i>",
            "<i>Ibidem</i>",
            "Ibid (redonda)",
            "Ibidem (redonda)",
            "Ibíd (con tilde)",
            "Ibídem (con tilde)",
            "Nada",
            "Personalizada"
        ]
        self.ibid_label_entries = [
            '<i xml:lang="la">Ibid</i>.',
            '<i xml:lang="la">Ibidem</i>.',
            '<span xml:lang="la">Ibid</span>.',
            '<span xml:lang="la">Ibidem</span>',
            'Ibíd.',
            'Ibídem.',
            '',
            '<i xml:lang="la">Ibid</i>.'
        ]

        self.separator_label_list = ["Default", "Nada", "Personalizado"]
        self.separator_label_entries = ["TEXTO_ADICIONAL:", "", "SEPARADOR"]

        self.demo_note = "Nota de texto ibíd. Con texto posterior pp. 116-119"
        self.demo_base_note = "Nota base, en pág. 75. Revisar pág 20-22."

        self.cancel_regex = ""
        self.cancel_ibid_label = ""
        self.cancel_separator = ""
        self.cancel_regex_idx = 0
        self.cancel_ibid_label_idx = 0
        self.cancel_separator_idx = 0

        # Variables usadas por book.processIbid() para procesar los ibíd.
        self.regex = ""
        self.ibid_label = ""
        self.separator = ""

        # Populate ComboBoxes
        self.RegexComboBox.addItems(self.regex_search_list)
        self.IbidLabelComboBox.addItems(self.ibid_label_list)
        self.SeparatorComboBox.addItems(self.separator_label_list)
        # Concect ComboBoxes
        self.RegexComboBox.currentIndexChanged.connect(self.regexComboBox_newValue)
        self.IbidLabelComboBox.currentIndexChanged.connect(self.ibidLabelComboBox_newValue)
        self.SeparatorComboBox.currentIndexChanged.connect(self.separatorComboBox_newValue)

        # Texts
        self.OriginalNote.setText("Nota Base:\n{}\n\nNota ibíd.:\n{}".
                                  format(self.demo_base_note, self.demo_note))

        # Load Prefs
        self.prefs = self.bk.getPrefs()
        self.checkNewVersion()

        # Set Defaults
        self.prefs.defaults["RegEx_combobox"] = 0
        self.prefs.defaults["RegEx"] = self.regex_search_entries[0]
        self.prefs.defaults["Ibid_combobox"] = 0
        self.prefs.defaults["Ibid"] = self.ibid_label_entries[0]
        self.prefs.defaults["Separator_combobox"] = 0
        self.prefs.defaults["Separator"] = self.separator_label_entries[0]
        self.prefs.defaults["Text_zoom_size"] = 0

        # Load Values
        self.regex = self.prefs["RegEx"]
        self.ibid_label = self.prefs["Ibid"]
        self.separator = self.prefs["Separator"]
        self.text_zoom_level = self.prefs["Text_zoom_size"]

        # Set Currents
        self.RegexComboBox.setCurrentIndex(self.prefs["RegEx_combobox"])
        self.IbidLabelComboBox.setCurrentIndex(self.prefs["Ibid_combobox"])
        self.SeparatorComboBox.setCurrentIndex(self.prefs["Separator_combobox"])

        self.regexComboBox_newValue(self.RegexComboBox.currentIndex())
        self.ibidLabelComboBox_newValue(self.IbidLabelComboBox.currentIndex())
        self.separatorComboBox_newValue(self.SeparatorComboBox.currentIndex())

        self.RegexEntry.setText(self.regex)
        self.IbidLabelEntry.setText(self.ibid_label)
        self.SeparatorEntry.setText(self.separator)

        self.saveCancelValues()

    def changeZoomLevel(self, zoom) -> bool:
        new_val = self.text_zoom_level + zoom
        if new_val > 10 or new_val < -5:
            return False
        self.text_zoom_level = new_val
        self.prefs["Text_zoom_size"] = new_val
        self.bk.savePrefs(self.prefs)
        return True

    def checkNewVersion(self):
        from plugin import version
        if "version" not in self.prefs or self.prefs["version"] != version:
            self.prefs.clear()
            self.prefs["version"] = version
            self.bk.savePrefs(self.prefs)

    def saveCancelValues(self):
        # Seteamos los valores a restaurar para el botón cancelar
        self.cancel_regex_idx = self.RegexComboBox.currentIndex()
        self.cancel_ibid_label_idx = self.IbidLabelComboBox.currentIndex()
        self.cancel_separator_idx = self.SeparatorComboBox.currentIndex()
        self.cancel_regex = self.regex
        self.cancel_ibid_label = self.ibid_label
        self.cancel_separator = self.separator

    def regexComboBox_newValue(self, index):
        if index == len(self.regex_search_entries) - 1:
            self.RegexEntry.setEnabled(True)
        else:
            self.RegexEntry.setEnabled(False)
        
        self.RegexEntry.setText(self.regex_search_entries[index])

    def ibidLabelComboBox_newValue(self, index):
        if index == len(self.ibid_label_entries) - 1:
            self.IbidLabelEntry.setEnabled(True)
        else:
            self.IbidLabelEntry.setEnabled(False)
        
        self.IbidLabelEntry.setText(self.ibid_label_entries[index])

    def separatorComboBox_newValue(self, index):
        if index == len(self.separator_label_entries) - 1:
            self.SeparatorEntry.setEnabled(True)
        else:
            self.SeparatorEntry.setEnabled(False)
        
        self.SeparatorEntry.setText(self.separator_label_entries[index])

    def testButton_pressed(self):
        # Preparamos los objetos para la prueba
        parent = Note("nt1", "1", self.demo_base_note, "href", 1)
        child = Note("nt2", "2", self.demo_note, "href", 2)
        child.parent = parent
        child.is_ibid = True

        test = child.processIbid(self.RegexEntry.text(),
                self.IbidLabelEntry.text(), self.SeparatorEntry.text())
        self.ProccesedNote.setPlainText(test)

        highlight(self.ProccesedNote, self.SeparatorEntry.text())

    def acceptButton_pressed(self):
        # Obtenemos los valores actualizados desde la interfaz
        self.prefs["RegEx_combobox"] = self.RegexComboBox.currentIndex()
        self.prefs["Ibid_combobox"] = self.IbidLabelComboBox.currentIndex()
        self.prefs["Separator_combobox"] = self.SeparatorComboBox.currentIndex()
        self.prefs["RegEx"] = self.RegexEntry.text()
        self.prefs["Ibid"] = self.IbidLabelEntry.text()
        self.prefs["Separator"] = self.SeparatorEntry.text()

        self.regex = self.prefs["RegEx"]
        self.ibid_label = self.prefs["Ibid"]
        self.separator = self.prefs["Separator"]

        self.bk.savePrefs(self.prefs)
        self.saveCancelValues()

        self.close()

    def defaultButton_pressed(self):
        # Set defaults
        self.prefs["RegEx_combobox"] = self.prefs.defaults["RegEx_combobox"]
        self.prefs["Ibid_combobox"] = self.prefs.defaults["Ibid_combobox"]
        self.prefs["Separator_combobox"] = self.prefs.defaults["Separator_combobox"]
        self.prefs["RegEx"] = self.prefs.defaults["RegEx"]
        self.prefs["Ibid"] = self.prefs.defaults["Ibid"]
        self.prefs["Separator"] = self.prefs.defaults["Separator"]
        
        # Restauramos los valores
        self.RegexComboBox.setCurrentIndex(self.prefs["RegEx_combobox"])
        self.IbidLabelComboBox.setCurrentIndex(self.prefs["Ibid_combobox"])
        self.SeparatorComboBox.setCurrentIndex(self.prefs["Separator_combobox"])
        self.regex = self.prefs["RegEx"]
        self.ibid_label = self.prefs["Ibid"]
        self.separator = self.prefs["Separator"]
        
        # Actualizamos
        self.RegexComboBox.setCurrentIndex(self.prefs["RegEx_combobox"])
        self.IbidLabelComboBox.setCurrentIndex(self.prefs["Ibid_combobox"])
        self.SeparatorComboBox.setCurrentIndex(self.prefs["Separator_combobox"])
        
        self.regexComboBox_newValue(self.RegexComboBox.currentIndex())
        self.ibidLabelComboBox_newValue(self.IbidLabelComboBox.currentIndex())
        self.separatorComboBox_newValue(self.SeparatorComboBox.currentIndex())
        
        self.RegexEntry.setText(self.regex)
        self.IbidLabelEntry.setText(self.ibid_label)
        self.SeparatorEntry.setText(self.separator)
        
        self.bk.savePrefs(self.prefs)

    def cancelButton_pressed(self):
        # Restauramos los valores guardados
        self.RegexComboBox.setCurrentIndex(self.cancel_regex_idx)
        self.IbidLabelComboBox.setCurrentIndex(self.cancel_ibid_label_idx)
        self.SeparatorComboBox.setCurrentIndex(self.cancel_separator_idx)
        self.regex = self.cancel_regex
        self.ibid_label = self.cancel_ibid_label
        self.separator = self.cancel_separator
        
        self.RegexEntry.setText(self.regex)
        self.IbidLabelEntry.setText(self.ibid_label)
        self.SeparatorEntry.setText(self.separator)

        self.reject()

    def showDialog(self):
        self.show()

class CopyBK():
    def __init__(self):
        self.prefs = Prefs()

    def getPrefs(self):
        return self.prefs

    def savePrefs(self, preferences):
        pass

class Prefs(dict):
    def __init__(self):
        dict.__init__(self)
        self.defaults = OrderedDict()

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return self.defaults[key]
