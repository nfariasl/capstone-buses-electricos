# Escenarios de sensibilidad

`crear_escenarios.py` crea copias de una instancia con otro `escenario.json`, una por escenario, más
un `indice.csv`. Las corridas y las distancias no cambian. El método híbrido corre estos escenarios sin
modificar su código, porque ya lee plazas, conexiones y tarifas desde `escenario.json`.

| Escenario | Cambio | Pregunta de gestión |
|---|---|---|
| `plazas_-20`, `plazas_+20`, `plazas_+50` | Plazas y conexiones de cada electroterminal × 0,8, 1,2 y 1,5 | ¿Cuánto vale ampliar o perder espacio, que hoy es el recurso que se llena? |
| `conexiones_-50` | La mitad de los cargadores, mismas plazas | ¿Hacen falta todos los cargadores? |
| `cierre_E1` … `cierre_E5` | Un electroterminal cerrado (0 plazas y 0 conexiones) | Resiliencia: ¿cuánto cuesta perder cada terminal? |
| `tarifa_punta_+50` | Precio de los tramos de punta × 1,5 | ¿Se mueve la carga de horario? |
| `plazas_por_demanda` | Las 700 plazas repartidas según las corridas de cada sector | El desbalance entre sectores que preguntó el profesor |

## Uso

```bash
python3 09-entrega3/sensibilidad/crear_escenarios.py --instancia metodo_hibrido/instancia_417 \
    --destino metodo_hibrido/sensibilidad_417_L
python3 -m pytest -q 09-entrega3/sensibilidad/test_crear_escenarios.py
```

La instancia completa (`metodo_hibrido/instancia_417`) no está en GitHub; se prepara con
`metodo_hibrido/preparar_completa.py`. Cada escenario se corre igual que la instancia base, con
`buscar_mejor.py` o `09-entrega3/octetos/correr_metodos.py --instancias ...`, y después se mide con
`09-entrega3/kpi/` agregando la carpeta del resultado en `PLANES`.

Para correr los 11 escenarios y la base de una vez (4 en paralelo, 20 min de cuartetos cada uno, ~70 min):

```bash
caffeinate -i -s bash 09-entrega3/sensibilidad/correr_sensibilidad.sh 1200 \
    > 09-entrega3/sensibilidad/resultados/sensibilidad.log 2>&1
python3 09-entrega3/sensibilidad/resumir.py 09-entrega3/sensibilidad/resultados/sensibilidad_417_L.csv
```

## Resultados (corrida del 22 al 23-nov, día laboral)

Mac M1 de 8 GB, 4 corridas en paralelo, plan inicial + cuartetos al azar (semilla 1) con 1.200 s. La
base se corrió **en la misma tanda**: con 4 en paralelo rinde menos que sola (7.389 buses contra 7.364),
así que cada Δ se compara solo contra esta base. Tabla completa en `resultados/tabla_sensibilidad.csv`.

| Escenario | Buses (cuartetos) | Δ buses | Δ costo | Δ buses (plan inicial) | Δ costo (plan inicial) |
|---|---:|---:|---:|---:|---:|
| Base | 7.389 | — | — (USD 2.631.699) | — (7.570) | — (USD 2.677.608) |
| Cierre E2 | 7.459 | +70 | **+0,62 %** | +110 | +0,92 % |
| Cierre E4 | 7.442 | +53 | **+0,51 %** | +79 | +0,70 % |
| Cierre E1 | 7.421 | +32 | **+0,29 %** | +56 | +0,47 % |
| Cierre E5 | 7.397 | +8 | +0,03 % | +18 | +0,15 % |
| Cierre E3 | 7.383 | −6 | −0,06 % | +8 | +0,07 % |
| Tarifa de punta +50 % | 7.381 | −8 | +0,04 % | 0 | **+0,16 %** |
| Plazas −20 % | 7.381 | −8 | −0,06 % | 0 | +0,01 % |
| Plazas +20 % | 7.382 | −7 | −0,08 % | 0 | −0,01 % |
| Plazas +50 % | 7.370 | −19 | −0,22 % | 0 | −0,02 % |
| Mitad de conexiones | 7.380 | −9 | −0,08 % | 0 | 0,00 % |
| Plazas según demanda | 7.386 | −3 | −0,05 % | 0 | 0,00 % |

**Cómo leerla.** Con una sola semilla, la búsqueda tiene ruido: las tres semillas de la base en 1.200 s
difieren en ~0,10 % (USD 2.623.502 a 2.626.148, `octetos/resultados/red_completa_417_L.csv`). Un Δ menor a
~0,15 % no se distingue del ruido; el plan inicial es determinista y sirve para confirmar el signo.

- **Cerrar un electroterminal es lo único que mueve el costo**, y depende de cuál: E2 (+70 buses) y E4
  (+53) son críticos, E1 intermedio, y E5 y E3 casi no importan. El orden es el mismo en el plan inicial.
- **Plazas y conexiones no mueven el costo diario** entre −20 % y +50 %: en el día aislado el espacio no
  limita la flota. Con la mitad de las conexiones el plan inicial sale idéntico, coherente con que la carga
  simultánea no restringe. El espacio sí puede importar en la recarga nocturna (§D), que el modelo de un
  día no mide.
- **Tarifa de punta +50 %** sube el plan inicial en USD 4.200 al día (+0,16 %). Con cuartetos la diferencia
  queda dentro del ruido; la carga total baja de 71.065 a 70.151 kWh, pero no se midió cuánta salió de punta.
- Plazas +50 % (−19 buses, −0,22 %) queda en el borde del ruido; para afirmarlo harían falta más semillas.

## Escenarios del bus, precios y espera (23-nov, día laboral)

**Batería y consumo** (`correr_fisicos.sh`). Cuartetos al azar, semilla 1, 1.200 s, 4 en paralelo, con la
base corrida en la misma tanda (7.384 buses, USD 2.631.915). La reserva es el 10 % de la batería.
Resultados en `resultados/fisicos_417_L.csv`.

| Escenario | Buses | Δ buses | Δ costo | Plan inicial |
|---|---:|---:|---:|---:|
| Base | 7.384 | — | — | 7.570 |
| Batería de 300 kWh | 8.640 | +17,0 % | +13,8 % | 8.845 |
| Batería de 250 kWh | 9.552 | +29,4 % | +25,2 % | 10.038 |
| Consumo +10 % (1,54 kWh/km) | 8.173 | +10,7 % | +8,7 % | 8.439 |
| Consumo +20 % (1,68 kWh/km) | 8.742 | +18,4 % | +15,3 % | — |

Lectura: el bus mismo pesa mucho más que la capacidad de carga o las tarifas. Con menos autonomía, cada
bus alcanza a hacer menos corridas y hacen falta más buses. **Limitación:** el caso base no se corrió con
estos parámetros (no lee las variables de entorno), así que no se sabe si el ahorro contra él se mantiene.

**Costo por bus y por km ±20 %** (`evaluar_costos.py`), sobre los mismos planes y sin reoptimizar: el
ahorro del día laboral contra el caso base queda entre −14,07 % (km +20 %) y −15,08 % (km −20 %).
Resultados en `resultados/costos_evaluados.csv`.

**Costo de espera** (`09-entrega3/kpi/costo_espera.py`): cobrar 0,03 USD/min de espera entre corridas
suma ~1,9 % al costo de ambos planes; el ahorro del día laboral pasa de −14,54 % a −14,59 %.

## Lo que todavía no cubre

- **Consumo, batería, estado de carga inicial y final, velocidad en vacío, potencia, costo por bus y
  costo por km.** Están fijos en el código de `metodo_hibrido/` (`calendario.py`, `recarga.py`,
  `conjunta.py`, `exacto.py`, `verificar.py` y `caso_base.py`), y `load_instance` rechaza un escenario
  que declare otros valores. Para variarlos hay que llevarlos a `escenario.json`.
- **El caso base en estos escenarios.** `codigo/tres_fases/caso_base.py` toma plazas y tarifas de
  `codigo/`, no de `escenario.json`.
