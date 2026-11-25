from ocupacion_terminales import ocupacion_maxima


def fila(tipo, origen, destino, inicio, fin):
    return dict(tipo=tipo, origen=origen, destino=destino, inicio_s=str(inicio), fin_s=str(fin))


def test_cuenta_esperas_solapadas_en_el_mismo_terminal():
    filas = [fila('espera', 'T01', 'T01', 0, 100), fila('espera', 'T01', 'T01', 50, 150),
             fila('espera', 'T01', 'T01', 120, 200)]
    assert ocupacion_maxima(filas)['T01'] == (2, 50)


def test_un_bus_que_sale_cuando_otro_llega_no_se_cuenta_dos_veces():
    filas = [fila('espera', 'T02', 'T02', 0, 100), fila('espera', 'T02', 'T02', 100, 200)]
    assert ocupacion_maxima(filas)['T02'] == (1, 0)


def test_ignora_esperas_en_paraderos_y_traslados():
    filas = [fila('espera', 'S:P1', 'S:P1', 0, 100), fila('vacio', 'T01', 'S:P1', 0, 50)]
    assert ocupacion_maxima(filas) == {}
