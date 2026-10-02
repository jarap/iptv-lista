#!/usr/bin/env python3
"""Arma la guía de la lista de prueba.

La lista de prueba son siete canales internacionales libres, y sirve para dos
cosas: las capturas de la ficha de Play y que el revisor pueda probar la app sin
que le demos una lista de verdad. Sin guía la app se ve en su peor versión —el
mosaico muestra el grupo en vez del programa—, así que acá se le arma una.

La guía se saca de un XMLTV público y se recorta a estos canales: bajarse el
país entero serían 46 MB para siete canales, y en un televisor eso se nota.

    python3 herramientas/guia_prueba.py

Escribe prueba.xml al lado de prueba.m3u, con guía para DIAS días: lo que la
fuente no alcanza a traer se completa repitiendo su último día. Conviene volver
a correrlo cada tanto: una guía vieja no muestra nada.
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

# De qué canal de la fuente sale cada canal nuestro. CGTN Español y Red Bull no
# están en ninguna guía pública que sirva: quedan sin programación y la app
# muestra "Sin guía", que es lo honesto.
DE_DONDE = {
    "dwes": ("ar", "Canal.DW.(Latinoamérica).ar", "DW Español"),
    "dwen": ("fr", "DW-TV.fr", "DW English"),
    "f24en": ("fr", "France.24.Anglais.fr", "France 24 English"),
    "euronews": ("fr", "Euronews.fr", "Euronews"),
    "aljazeera": ("fr", "Al.Jazeera.English.fr", "Al Jazeera English"),
    "cgtndoc": ("fr", "CGTN-Documentary.fr", "CGTN Documentary"),
}

DIAS = 9

FORMATO = "%Y%m%d%H%M%S %z"
UN_DIA = timedelta(days=1)


def bajar(url):
    pedido = urllib.request.Request(url, headers={"User-Agent": "zapping-guia/1.0"})
    with urllib.request.urlopen(pedido, timeout=180) as r:
        return gzip.decompress(r.read()).decode("utf-8", "replace")


def horario(atributos, cual):
    return datetime.strptime(re.search(cual + r'="([^"]+)"', atributos).group(1), FORMATO)


def rellenar(programas, hasta):
    """La fuente trae tres o cuatro días. Lo que falta hasta `hasta` se completa
    repitiendo el último día que sí trae: son canales de noticias, con la misma
    grilla todos los días, y para una lista de prueba alcanza."""
    if not programas:
        return []
    fin = max(horario(a, "stop") for a, _ in programas)
    ultimo_dia = [(a, c) for a, c in programas
                  if horario(a, "stop") > fin - UN_DIA and horario(a, "start") < fin]
    repetidos = []
    corrido = UN_DIA
    while fin + corrido - UN_DIA < hasta:
        for atributos, cuerpo in ultimo_dia:
            # el que venía empezado de antes arranca donde termina lo anterior
            arranque = max(horario(atributos, "start") + corrido, fin + corrido - UN_DIA)
            cierre = horario(atributos, "stop") + corrido
            if arranque >= hasta:
                break
            atributos = re.sub(r'start="[^"]+"', f'start="{arranque.strftime(FORMATO)}"', atributos)
            atributos = re.sub(r'stop="[^"]+"', f'stop="{cierre.strftime(FORMATO)}"', atributos)
            repetidos.append((atributos, cuerpo))
        corrido += UN_DIA
    return repetidos


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
        programas = []
        for m in patron.finditer(texto):
            atributos, cuerpo = m.group(1), m.group(2)
            if horario(atributos, "start") > hasta:
                continue
            atributos = atributos.replace(f'channel="{ajeno}"', f'channel="{nuestro}"')
            programas.append((atributos, cuerpo))
        programas.sort(key=lambda p: horario(p[0], "start"))
        repetidos = rellenar(programas, hasta)
        for atributos, cuerpo in programas + repetidos:
            salida.append(f"  <programme{atributos}>{cuerpo}</programme>")
        print(f"  {nuestro:6s} {len(programas):4d} programas + {len(repetidos):4d} repetidos")
        total += len(programas) + len(repetidos)

    salida.append("</tv>")
    destino = os.path.join(RAIZ, "prueba.xml")
    with open(destino, "w", encoding="utf-8") as f:
        f.write("\n".join(salida))
    print(f"{destino}: {total} programas, {os.path.getsize(destino) / 1024:.0f} KB")


if __name__ == "__main__":
    main()
