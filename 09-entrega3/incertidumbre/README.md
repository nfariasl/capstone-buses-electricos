# Incertidumbre: atrasos y tiempos de viaje

`simular_atrasos.py` toma un plan ya auditado y simula su día con tiempos de viaje aleatorios. Cada corrida y cada traslado en vacío dura su tiempo programado multiplicado por un factor lognormal de media 1. Se prueban tres coeficientes de variación: 10, 20 y 30 %.

Reglas de la simulación:
- Un bus nunca sale antes de su horario. Si llega tarde, sale tarde y el atraso se arrastra a lo que sigue. La espera programada absorbe atrasos.
- El cargador está reservado hasta la hora programada de término. Si el bus llega tarde, carga solo el tiempo que le queda; si llega después del término, no carga.
- No hay despachadores, buses de reserva ni reprogramación.

Plan evaluado: cuartetos al azar, semilla 1, día laboral (7.351 buses), contra el caso base (8.684 buses). Son 20 réplicas por nivel de variabilidad, con los mismos números aleatorios para los dos planes.

```bash
python3 09-entrega3/incertidumbre/simular_atrasos.py --replicas 20
python3 -m pytest -q 09-entrega3/incertidumbre/test_simular_atrasos.py
```

**Validación.** Con variabilidad cero, la simulación reproduce los dos planes exactos: ningún atraso y ningún bus bajo la reserva.

## Resultados (23-nov, día laboral)

Promedio de 20 réplicas; entre paréntesis, el rango.

| Variabilidad | Plan | Corridas con más de 5 min de atraso | Atraso medio | Percentil 95 | Buses bajo la reserva | Buses sin energía |
|---|---|---|---|---|---|---|
| 10 % | Caso base | 4,4 % (4,2–4,6) | 0,7 min | 4,4 min | 4 | 1 |
| 10 % | Nuestro plan | 16,8 % (16,4–17,1) | 2,7 min | 15,1 min | 778 | 92 |
| 20 % | Caso base | 12,3 % (12,0–12,7) | 2,4 min | 16,0 min | 40 | 22 |
| 20 % | Nuestro plan | 31,6 % (31,0–32,1) | 8,0 min | 41,2 min | 825 | 234 |
| 30 % | Caso base | 18,7 % (18,3–19,1) | 5,3 min | 33,6 min | 111 | 67 |
| 30 % | Nuestro plan | 38,3 % (37,7–38,6) | 14,1 min | 70,3 min | 838 | 315 |

Fuente: `resultados/atrasos.csv`.

## Lectura

- **El plan optimizado es más frágil que el caso base.** Con 15 % menos buses hay menos holgura: con una variabilidad baja (10 %), las corridas atrasadas son casi cuatro veces más que en el caso base.
- **La batería es el punto débil.** El método carga solo lo justo: 1.445 buses terminan a menos de 1 kWh de la reserva, contra 47 en el caso base, que carga al 100 %. Si un retraso acorta una carga, el bus queda bajo la reserva. Con 10 % de variabilidad le pasa a 778 buses (de los 1.123 que cargan de día).
- **Qué implica.** Antes de operarlo hay que agregar holgura: un margen de energía sobre la reserva en el modelo de recarga, tiempo de colchón antes de cada carga o buses de reserva. Esa holgura le resta parte del ahorro; cuánto, queda por medir.
- **Límites.** Los factores son independientes; en la realidad, la congestión afecta a muchas corridas a la vez, lo que empeora el resultado. La regla de recarga es un extremo: si el bus cargara completo y saliera tarde, habría menos buses bajo la reserva, pero más atrasos.
