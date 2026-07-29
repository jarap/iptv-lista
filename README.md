# Lista de canales

`tv.m3u` — la lista que sale directo de Astra, con la guía y los logos ya
puestos. Se carga pegando esta dirección en el reproductor:

```
https://jarap.github.io/iptv-lista/tv.m3u
```

## Las direcciones son privadas

Los canales apuntan a `10.10.19.246`, que es el Astra. La lista se publica acá
para poder cargarla de una sola vez desde cualquier aparato, pero **se ve
únicamente desde la red interna**: desde afuera, la dirección no resuelve a
ningún lado.

## La guía viene sola

La cabecera declara `url-tvg` con nuestra propia guía, la que se arma con el
EIT que emiten los canales dentro de su propia señal. El reproductor la adopta
sin que nadie configure nada. Los identificadores son los mismos que trae la
lista en `tvg-id`, así que empareja exacto en vez de adivinar por nombre.

## De dónde sale cada canal

El Astra recibe dos satélites, INTV y Movistar, y muchos canales llegan por los
dos. La lista se queda con una sola versión de cada uno, elegida así:

1. **Audio en español.** Un canal en inglés no sirve por más resolución que
   tenga. HBO llega en 480p inglés por INTV y en 1080p español por Movistar:
   gana Movistar.
2. **Mayor resolución**, cuando los dos están en español.
3. **Mayor bitrate real**, medido sobre unos segundos de emisión.

No se publica lo que no se ve: los canales sin señal al momento de armarla
quedan afuera.

## Cómo se rehace

Los canales del satélite cambian, así que la lista se vuelve a armar midiendo de
nuevo. Está todo en el proyecto de Zapping, en `herramientas/`.
