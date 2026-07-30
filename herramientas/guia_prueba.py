#!/usr/bin/env python3
"""Arma la guía de la lista de prueba.

La lista de prueba son siete canales internacionales libres, y sirve para dos
cosas: las capturas de la ficha de Play y que el revisor pueda probar la app sin
que le demos una lista de verdad. Sin guía la app se ve en su peor versión —el
mosaico muestra el grupo en vez del programa—, así que acá se le arma una.

La guía se saca de un XMLTV público y se recorta a estos canales: bajarse el
país entero serían 46 MB para siete canales, y en un televisor eso se nota.

    python3 herramientas/guia_prueba.py

Escribe prueba.xml al lado de prueba.m3u. Conviene volver a correrlo cada tanto:
una guía vieja no muestra nada.
"""
import gzip
import os
import re
import urllib.request
from datetime import datetime, timedelta, timezone

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)

FUENTES = {
    "ar": "https://epgshare01.online/epgshare01/epg_ripper_AR1.xml.gz",
    "fr": "https://epgshare01.online/epgshare01/epg_ripper_FR1.xml.gz",
}

# De qué canal de la fuente sale cada canal nuestro. NASA y Red Bull no están en
# ninguna guía pública que sirva: quedan sin programación y la app muestra
# "Sin guía", que es lo honesto.
DE_DONDE = {
    "dwes": ("ar", "Canal.DW.(Latinoamérica).ar", "DW Español"),
    "dwen": ("fr", "DW-TV.fr", "DW English"),
    "f24es": ("fr", "France.24.Espanol.fr", "France 24 Español"),
    "f24en": ("fr", "France.24.Anglais.fr", "France 24 English"),
    "f24fr": ("fr", "France.24.fr", "France 24 Français"),
}

DIAS = 3


def bajar(url):
    pedido = urllib.request.Request(url, headers={"User-Agent": "zapping-guia/1.0"})
    with urllib.request.urlopen(pedido, timeout=180) as r:
        return gzip.decompress(r.read()).decode("utf-8", "replace")


def main():
    fuentes = {}
    for clave, url in FUENTES.items():
        print(f"bajando {clave}…", flush=True)
        fuentes[clave] = bajar(url)

    hasta = datetime.now(timezone.utc) + timedelta(days=DIAS)
    salida = ['<?xml version="1.0" encoding="UTF-8"?>',
              '<tv generator-info-name="zapping">']
    for nuestro, (fuente, ajeno, nombre) in DE_DONDE.items():
        salida.append(f'  <channel id="{nuestro}">'
                      f'<display-name>{nombre}</display-name></channel>')

    total = 0
    for nuestro, (fuente, ajeno, _) in DE_DONDE.items():
        texto = fuentes[fuente]
        patron = re.compile(
            r'<programme([^>]*channel="' + re.escape(ajeno) + r'"[^>]*)>(.*?)</programme>',
            re.S)
        puestos = 0
        for m in patron.finditer(texto):
            atributos, cuerpo = m.group(1), m.group(2)
            arranque = re.search(r'start="(\d{14})', atributos)
            if arranque and datetime.strptime(arranque.group(1), "%Y%m%d%H%M%S").replace(
                    tzinfo=timezone.utc) > hasta:
                continue
            atributos = atributos.replace(f'channel="{ajeno}"', f'channel="{nuestro}"')
            salida.append(f"  <programme{atributos}>{cuerpo}</programme>")
            puestos += 1
        print(f"  {nuestro:6s} {puestos:4d} programas")
        total += puestos

    salida.append("</tv>")
    destino = os.path.join(RAIZ, "prueba.xml")
    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n".join(salida))
    print(f"{destino}: {total} programas, {os.path.getsize(destino) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
