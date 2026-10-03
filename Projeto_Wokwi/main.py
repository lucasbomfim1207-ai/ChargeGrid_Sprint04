# ChargeGrid FIAP - Sprint 4 (Goodwe) - ESP32 + MicroPython (Wokwi)
import machine
import time
from machine_i2c_lcd import I2cLcd
from controle import Controlador

# ---------------- Hardware ----------------
i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21), freq=400000)
lcd = I2cLcd(i2c, 0x27, 2, 16)

botao = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP)   # ID do usuario
potenciometro = machine.ADC(machine.Pin(34))                  # demanda simulada
potenciometro.atten(machine.ADC.ATTN_11DB)
led_bateria = machine.Pin(13, machine.Pin.OUT)                # bateria Goodwe
led_bateria.value(0)

CICLO_MS = 500
CICLOS_POR_PAGINA = 6    # troca de tela a cada 3 s
CABECALHO = "t_s,adc,demanda_kw,solar_kw,bateria_kw,rede_kw,bat_on,soc_pct,autonomia_pct,co2_kg"

ctrl = Controlador(CICLO_MS / 1000)


def linha(row, texto):
    lcd.move_to(0, row)
    lcd.putstr(("%-16s" % texto)[:16])


def pressionado():
    if botao.value() == 0:
        time.sleep_ms(30)          # debounce
        return botao.value() == 0
    return False


def aguardar_solto():
    while botao.value() == 0:
        time.sleep_ms(20)
    time.sleep_ms(30)


def mostrar(pagina):
    if pagina == 0:
        linha(0, "Dem:%3d%% %4.1fkW" % (ctrl.demanda_pct, ctrl.demanda_kw))
        estado = "BAT ON  " if ctrl.bateria_ativa else "BAT OFF "
        linha(1, estado + "SoC:%3d%%" % int(ctrl.soc))
    else:
        linha(0, "Rede%4.1f Sol%4.1f" % (ctrl.rede_kw, ctrl.solar_kw))
        linha(1, "CO2 evit %5.2fkg" % ctrl.co2_evitado_kg)


while True:
    # ---------- Estado: aguardando ID ----------
    lcd.clear()
    linha(0, "ChargeGrid FIAP")
    linha(1, "Aguardando ID...")
    led_bateria.value(0)
    while not pressionado():
        time.sleep_ms(50)
    aguardar_solto()

    # ---------- Inicio da sessao ----------
    ctrl.reset_sessao()
    lcd.clear()
    linha(0, "Sistema Ativo!")
    linha(1, "ID lido (botao)")
    print(CABECALHO)
    time.sleep(1.5)
    t0 = time.ticks_ms()
    ciclo = 0

    # ---------- Sessao ativa ----------
    encerrar = False
    while not encerrar:
        ctrl.passo(potenciometro.read())
        led_bateria.value(1 if ctrl.bateria_ativa else 0)
        mostrar((ciclo // CICLOS_POR_PAGINA) % 2)
        print("%.1f,%d,%.2f,%.2f,%.2f,%.2f,%d,%d,%d,%.4f" % (
            time.ticks_diff(time.ticks_ms(), t0) / 1000, int(ctrl.filtrado),
            ctrl.demanda_kw, ctrl.solar_kw, ctrl.bat_kw, ctrl.rede_kw,
            int(ctrl.bateria_ativa), int(ctrl.soc),
            int(ctrl.autonomia_pct), ctrl.co2_evitado_kg))
        ciclo += 1

        fim = time.ticks_add(time.ticks_ms(), CICLO_MS)
        while time.ticks_diff(fim, time.ticks_ms()) > 0:
            if pressionado():
                encerrar = True
                break
            time.sleep_ms(20)

    # ---------- Encerramento e resumo ----------
    aguardar_solto()
    led_bateria.value(0)
    lcd.clear()
    linha(0, "Sessao encerrada")
    linha(1, "Autonomia %3d%%" % int(ctrl.autonomia_pct))
    time.sleep(2.5)
    linha(0, "CO2 evit %5.3fkg" % ctrl.co2_evitado_kg)
    linha(1, "Pico bat %4.1fkW" % ctrl.pico_bat_kw)
    time.sleep(2.5)
