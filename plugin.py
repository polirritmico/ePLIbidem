#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
IbidEpl v0.4_beta

Una ayuda para manejar notas ibid.
Titivillus
"""

import sys
import os
# import re
import src.mainWindow
from src.book import Book


def run(bk):
    if not bk.launcher_version() >= 20170115:
        print("Este plugin requiere Sigil >0.9.8 \
        \n\nHaga clic en Aceptar para cerrar.")
        return -1

    selected_files = []
    for i in bk.selected_iter():
        selected_files.append(i)
    filename = selected_files[0][1]

    try:
        print("Leyendo archivo seleccionado...")
        html = bk.readfile(filename)
    except:
        print("ERROR: No se puede abrir el archivo seleccionado.")
        return -1

    book = Book(filename)
    book.readHTML(html)
    book.parseNotes()

    book.autocheckIbidNotes()
    book.setParentsAndChilds()
    book.updateNextAndPrevNotes()
    book.updateNotesLabels()

    print("Archivo \"" + filename + "\" indexado exitosamente.")
    print("Abriendo interfaz QT...")

    dark_theme = False
    if (bk.launcher_version() >= 20200117) and bk.colorMode() == "dark":
        dark_theme = True

    path = os.path.join(bk._w.plugin_dir, bk._w.plugin_name) + "/src/"
    overwrite_xhtml = src.mainWindow.run(book, dark_theme, path)

    if overwrite_xhtml:
        bk.writefile(book.bookToXHTML())
        print("Archivo escrito correctamente.")
    else:
        print("No se han escrito cambios.")

    print("Pulse OK para volver a Sigil.")
    return 0


def main():
    # print("Error: Ejecutar desde Sigil.\n")
    # return -1
    filename = "testFiles/test_04.xhtml"

    file = open(filename, "r")
    html = file.read()
    file.close()

    book = Book(filename)
    book.readHTML(html)
    book.parseNotes()

    book.autocheckIbidNotes()
    book.setParentsAndChilds()
    book.updateNextAndPrevNotes()
    book.updateNotesLabels()

    print("Archivo \"" + filename + "\" indexado exitosamente.")
    print("Abriendo interfaz QT...")
    dark_theme = True
    path = "src/"
    overwrite_xhtml = src.mainWindow.run(book, dark_theme, path)

    if overwrite_xhtml:
        file = open("outTest_04.xhtml", "w")
        file.write(book.bookToXHTML())
        file.close()
        print("Archivo escrito correctamente.")
    else:
        print("No se han escrito cambios.")

    print("Pulse OK para volver a Sigil.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
