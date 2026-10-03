# controle.py - Logica de controle do ChargeGrid FIAP (sem dependencia de hardware)
# Simula o despacho inteligente entre solar, bateria Goodwe e rede.
# Todos os parametros de potencia/energia sao PREMISSAS de simulacao.

ADC_MAX = 4095           # ADC de 12 bits do ESP32

# --- Parametros do sistema simulado (ajustaveis) ---
P_MAX_KW = 11.0          # demanda maxima da estacao (potenciometro a 100%)
SOLAR_KW = 6.0           # geracao solar disponivel
BAT_KW = 5.0             # potencia maxima de descarga da bateria
BAT_KWH = 10.0           # capacidade util da bateria
SOC_INICIAL = 80.0       # estado de carga inicial (%)
SOC_MIN = 20.0           # reserva minima da bateria (%)
LIMITE_ALTO = 2500       # liga a bateria acima deste valor ADC (~61%)
LIMITE_BAIXO = 2200      # desliga abaixo deste valor (histerese)
AMOSTRAS = 8             # janela da media movel (filtro de ruido)
ACELERACAO = 120         # 1 s real = 120 s simulados (SoC varia visivelmente)
FATOR_CO2 = 0.0385       # kg CO2 evitado por kWh renovavel (premissa)


class Controlador:
    def __init__(self, dt_s=0.5):
        self.dt_s = dt_s
        self.soc = SOC_INICIAL
        self.reset_sessao()

    def reset_sessao(self):
        self.janela = []
        self.bateria_ativa = False
        self.filtrado = 0
        self.demanda_kw = 0.0
        self.demanda_pct = 0
        self.solar_kw = 0.0
        self.bat_kw = 0.0
        self.rede_kw = 0.0
        self.pico_bat_kw = 0.0
        self.e_dem = 0.0
        self.e_solar = 0.0
        self.e_bat = 0.0
        self.e_rede = 0.0

    @property
    def autonomia_pct(self):
        if self.e_dem <= 0:
            return 0
        return min(100, (self.e_solar + self.e_bat) * 100.0 / self.e_dem)

    @property
    def co2_evitado_kg(self):
        return (self.e_solar + self.e_bat) * FATOR_CO2

    def passo(self, raw):
        # 1) Filtro de media movel
        self.janela.append(raw)
        if len(self.janela) > AMOSTRAS:
            self.janela.pop(0)
        self.filtrado = sum(self.janela) / len(self.janela)
        self.demanda_kw = self.filtrado / ADC_MAX * P_MAX_KW
        self.demanda_pct = int(self.filtrado * 100 / ADC_MAX)

        # 2) Decisao com histerese + protecao de reserva da bateria
        if self.bateria_ativa:
            if self.filtrado < LIMITE_BAIXO or self.soc <= SOC_MIN:
                self.bateria_ativa = False
        else:
            if self.filtrado > LIMITE_ALTO and self.soc > SOC_MIN:
                self.bateria_ativa = True

        # 3) Despacho de energia: solar primeiro, depois bateria, rede por ultimo
        self.solar_kw = min(self.demanda_kw, SOLAR_KW)
        resto = self.demanda_kw - self.solar_kw
        self.bat_kw = min(resto, BAT_KW) if self.bateria_ativa else 0.0
        self.rede_kw = resto - self.bat_kw
        carga_kw = 0.0 if self.bateria_ativa else (SOLAR_KW - self.solar_kw)

        # 4) Integracao de energia e estado de carga
        dt_h = self.dt_s * ACELERACAO / 3600.0
        self.soc += (carga_kw - self.bat_kw) * dt_h / BAT_KWH * 100.0
        self.soc = max(0.0, min(100.0, self.soc))
        self.e_dem += self.demanda_kw * dt_h
        self.e_solar += self.solar_kw * dt_h
        self.e_bat += self.bat_kw * dt_h
        self.e_rede += self.rede_kw * dt_h
        if self.bat_kw > self.pico_bat_kw:
            self.pico_bat_kw = self.bat_kw
