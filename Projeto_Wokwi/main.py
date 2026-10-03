import machine
import time
from machine_i2c_lcd import I2cLcd

i2c = machine.I2C(0, scl=machine.Pin(22), sda=machine.Pin(21), freq=400000)
lcd = I2cLcd(i2c, 0x27, 2, 16)

# Pinos: Botão, Potenciómetro e Novo LED (Bateria)
botao = machine.Pin(4, machine.Pin.IN, machine.Pin.PULL_UP)
potenciometro = machine.ADC(machine.Pin(34))
potenciometro.atten(machine.ADC.ATTN_11DB)
led_bateria = machine.Pin(13, machine.Pin.OUT) 
led_bateria.value(0) # Inicia desligado


sessao_ativa = False
limite_critico = 2500 # Limite onde o sistema Goodwe precisa agir

while True:
    if not sessao_ativa:
        lcd.clear()
        lcd.move_to(0, 0)
        lcd.putstr("ChargeGrid FIAP")
        lcd.move_to(0, 1)
        lcd.putstr("Aguardando ID...")
        led_bateria.value(0) # Garante que a bateria está desligada
        
        while botao.value() == 1:
            time.sleep(0.1)
            
        sessao_ativa = True
        lcd.clear()
        lcd.move_to(0, 0)
        lcd.putstr("Sistema Ativo!  ")
        time.sleep(1.5)
        
    else:
        # Lê a demanda simulada
        demanda_rede = potenciometro.read()
        
        lcd.clear()
        lcd.move_to(0, 0)
        
        if demanda_rede > limite_critico:
            lcd.putstr("Alta Demanda!   ")
            lcd.move_to(0, 1)
            lcd.putstr("Bateria Ativada ")
            led_bateria.value(1) # Acende o LED (Simula o acionamento da bateria Goodwe)
        else:
            lcd.putstr("Rede Estavel    ")
            lcd.move_to(0, 1)
            lcd.putstr("Solar 100% Otim.")
            led_bateria.value(0) # Apaga o LED (Desliga a bateria, usa apenas solar)
            
        # Encerramento da sessão
        if botao.value() == 0:
            sessao_ativa = False
            lcd.clear()
            lcd.putstr("A Desligar...   ")
            time.sleep(2)
            
        time.sleep(0.5)