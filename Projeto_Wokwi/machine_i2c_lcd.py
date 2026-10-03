import utime
from machine import I2C

# LCD Commands
LCD_CLR = 0x01
LCD_RET_HOME = 0x02
LCD_ENTRY_MODE = 0x04
LCD_DISPLAY_CTRL = 0x08
LCD_CURSOR_SHIFT = 0x10
LCD_FUNCTION_SET = 0x20
LCD_SET_CGRAM_ADDR = 0x40
LCD_SET_DDRAM_ADDR = 0x80

# Flags for display entry mode
LCD_ENTRY_LEFT = 0x02
LCD_ENTRY_SHIFT_DECREMENT = 0x00

# Flags for display on/off control
LCD_DISPLAY_ON = 0x04
LCD_CURSOR_OFF = 0x00
LCD_BLINK_OFF = 0x00

# Flags for function set
LCD_4BIT_MODE = 0x00
LCD_2_LINE = 0x08
LCD_5x8_DOTS = 0x00

# Flags for backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

En = 0b00000100 # Enable bit
Rw = 0b00000010 # Read/Write bit
Rs = 0b00000001 # Register select bit

class I2cLcd:
    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self.i2c = i2c
        self.i2c_addr = i2c_addr
        self.num_lines = num_lines
        self.num_columns = num_columns
        self.backlight = LCD_BACKLIGHT
        
        self.i2c.writeto(self.i2c_addr, bytes([0]))
        utime.sleep_ms(20)
        
        self.hal_write_init(0x03)
        utime.sleep_ms(5)
        self.hal_write_init(0x03)
        utime.sleep_ms(5)
        self.hal_write_init(0x03)
        self.hal_write_init(0x02)
        
        self.display_cmd(LCD_FUNCTION_SET | LCD_2_LINE | LCD_5x8_DOTS | LCD_4BIT_MODE)
        self.display_cmd(LCD_DISPLAY_CTRL | LCD_DISPLAY_ON | LCD_CURSOR_OFF | LCD_BLINK_OFF)
        self.display_cmd(LCD_ENTRY_MODE | LCD_ENTRY_LEFT)
        self.clear()

    def hal_write_init(self, data):
        self.hal_write_four_bits(data << 4)

    def hal_write_four_bits(self, data):
        self.i2c.writeto(self.i2c_addr, bytes([data | self.backlight]))
        self.hal_pulse_enable(data)

    def hal_pulse_enable(self, data):
        self.i2c.writeto(self.i2c_addr, bytes([data | En | self.backlight]))
        utime.sleep_us(1)
        self.i2c.writeto(self.i2c_addr, bytes([(data & ~En) | self.backlight]))
        utime.sleep_us(50)

    def hal_write_command(self, cmd):
        self.hal_write_four_bits(cmd & 0xF0)
        self.hal_write_four_bits((cmd << 4) & 0xF0)

    def hal_write_data(self, data):
        self.hal_write_four_bits((data & 0xF0) | Rs)
        self.hal_write_four_bits(((data << 4) & 0xF0) | Rs)

    def display_cmd(self, cmd):
        self.hal_write_command(cmd)

    def clear(self):
        self.display_cmd(LCD_CLR)
        utime.sleep_ms(2)

    def move_to(self, cursor_x, cursor_y):
        addr = cursor_x & 0x3f
        if cursor_y & 1:
            addr += 0x40
        self.display_cmd(LCD_SET_DDRAM_ADDR | addr)

    def putstr(self, string):
        for char in string:
            self.hal_write_data(ord(char))