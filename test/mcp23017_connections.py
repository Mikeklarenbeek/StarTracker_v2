from machine import Pin, I2C
from lib import mcp23017
from lib.mcp_rotary_encoder import MCPRotaryEncoder
import time

# =====================================================
# =============== HARDWARE SETUP ======================
# =====================================================

i2c = I2C(1, scl=Pin(15), sda=Pin(14)) # I2C1 op GPIO14(SDA) en GPIO15(SCL)
mcp = mcp23017.MCP23017(i2c, 0x20)     # MCP23017 op adres 0x20
print("MCP23017 geinitialiseerd op adres 0x20")

# ---------------- Inputs ----------------
ALT_dec_button = 3
ALT_inc_button = 7
AZ_dec_button  = 4
AZ_inc_button  = 6
SET_button     = 5

encoder_S1  = 10
encoder_S2  = 11
encoder_KEY = 12
joystick_sw = 13

buttons = [
    ALT_dec_button, ALT_inc_button,
    AZ_dec_button, AZ_inc_button,
    SET_button
]

# ---------------- Outputs ----------------
led_green  = 0   # SET / reset indicatie
led_yellow = 1   # stap = 1 graden
led_red    = 2   # stap = 0.1 graden

select_leds = [led_red, led_yellow]

# =====================================================
# =============== ENCODER SETUP =======================
# =====================================================

encoder = MCPRotaryEncoder(
    mcp,
    pin_a=encoder_S1,
    pin_b=encoder_S2,
    min_val=0,
    max_val=19
)

# Pull-ups
for pin in buttons + [encoder_S1, encoder_S2, encoder_KEY, joystick_sw]:
    mcp[pin].input(pull=1)

# =====================================================
# =============== CONSTANTEN ==========================
# =====================================================

STEP_RED    = 0.1 # stapgrootte in graden
STEP_YELLOW = 1   # stapgrootte in graden

KEY_DEBOUNCE = 0.2         # debounce tijd voor KEY knop (seconden)
ENCODER_SETTLE_TIME = 0.05 # tijd om encoder te laten settelen (seconden)

BLINK_INTERVAL = 0.5 # LED knipper interval in seconden
SECOND = 1           # één seconde

# =====================================================
# =============== STATUS VARIABELEN ===================
# =====================================================

ALT_value = 0.0 # huidige ALT waarde
AZ_value  = 0.0 # huidige AZ waarde

min_ALT, max_ALT = -90, 90 # beperk ALT tussen -90 en +90 graden
min_AZ,  max_AZ  = 0, 360  # volledige rotatie

rotary_value = encoder.value # huidige encoder waarde
current_selection = -1       # huidige selectie (0=rode LED, 1=gele LED)

encoder_moving = False # status of encoder wordt gedraaid
encoder_last_time = 0  # tijdstempel voor encoder beweging

key_last = 1 # laatste status van KEY knop
key_time = 0 # tijdstempel voor KEY knop

blink_selection = False # knipper selectie LED
last_blink_time = 0     # tijdstempel voor selectie LED

blink_green = False       # groene LED knipperen
green_state = 0           # huidige status groene LED
last_blink_time_green = 0 # tijdstempel voor groene LED

SET_press_start = 0 # tijdstempel voor SET knop

# Reset knipperpatroon (heeft PRIORITEIT)
reset_blink = False
reset_blink_times = [0.2, 0.2, 1.5, 0.2, 0.2, 0.2] # aan/uit tijden
reset_blink_index = 0                              # huidige index
reset_blink_start = 0                              # start tijdstempel

# =====================================================
# =============== HULPFUNCTIES ========================
# =====================================================
#-- stop het knipperen van de groene LED --
def stop_green_led():
    global blink_green, reset_blink # stop knipperen
    blink_green = False 
    reset_blink = False
    mcp[led_green].output(0)

#-- clamp ALT waarde en wrap AZ waarde --
def clamp_and_wrap_values():
    global ALT_value, AZ_value

    ALT_value = max(min_ALT, min(max_ALT, ALT_value)) # clamp tussen min/max
    AZ_value  = AZ_value % max_AZ # wrap rond 360 graden

#-- update de LED's voor de huidige selectie --
def update_led_selection(selection): 
    global current_selection # huidige selectie
    
#- update alleen als selectie is veranderd
    if selection != current_selection:                # alleen updaten bij verandering
        current_selection = selection                 # update LED's
        for pin in select_leds:                       # zet alle LEDs uit
            mcp[pin].output(0) 
        mcp[select_leds[current_selection]].output(1) # zet geselecteerde LED aan
        print("LED selectie:", current_selection) 


# =====================================================
# =============== ENCODER LOGICA ======================
# =====================================================
#-- update de encoder status --
def update_encoder(now): # updates the encoder state
    global rotary_value, encoder_moving, encoder_last_time 
    global blink_selection

    new_value = encoder.update() # get the new encoder value

    if new_value != rotary_value: # waarde is veranderd
        rotary_value = new_value  # update de tijd en status
        encoder_moving = True     # gebruiker is aan het draaien
        encoder_last_time = now   # update tijdstempel

        blink_selection = False # stop knipperen
        stop_green_led()        # stop groene LED

        selection = rotary_value // 10 # bepaal selectie (0 of 1)
        if selection > 1:              # limiet naar 1
            selection = 1 

        update_led_selection(selection) # update LED selectie

    if encoder_moving and now - encoder_last_time > ENCODER_SETTLE_TIME:
        encoder_moving = False


# =====================================================
# =============== ALT / AZ KNOPPEN ====================
# =====================================================
#-- verwerk ALT / AZ knoppen --
def handle_alt_az_buttons():
    global ALT_value, AZ_value                                 # huidige ALT/AZ waarden

    step = STEP_RED if current_selection == 0 else STEP_YELLOW # bepaal stapgrootte
    changed = False                                            # status verandering

#- controleer elke knop
    if mcp[ALT_inc_button].value() == 0: 
        ALT_value += step # verhoog ALT waarde
        changed = True
    if mcp[ALT_dec_button].value() == 0:
        ALT_value -= step # verlaag ALT waarde
        changed = True
    if mcp[AZ_inc_button].value() == 0:
        AZ_value += step # verhoog AZ waarde
        changed = True
    if mcp[AZ_dec_button].value() == 0:
        AZ_value -= step # verlaag AZ waarde
        changed = True 

#- bij verandering, clamp/wrap en print waarden
    if changed:
        clamp_and_wrap_values()
        print(f"ALT: {ALT_value:.2f}, AZ: {AZ_value:.2f}") 
        stop_green_led()


# =====================================================
# =============== ROTARY KEY ==========================
# =====================================================
#-- verwerk rotary encoder knop --
def handle_rotary_key(now):
    global key_last, key_time, blink_selection # status variabelen

    key_now = mcp[encoder_KEY].value()         # huidige knop status

#- detecteer falling edge (druk)
    if key_last == 1 and key_now == 0:    # knop is ingedrukt
        if now - key_time > KEY_DEBOUNCE: # debounce check
            key_time = now                # update tijdstempel
            blink_selection = True        # start knipperen
            stop_green_led()              # stop groene LED
            print("KEY → waarden opgeslagen")

    key_last = key_now # update laatste status


# =====================================================
# =============== SET KNOP ============================
# =====================================================
#-- verwerk SET knop --
def handle_set_button(now):
    global SET_press_start                                   # status variabelen
    global blink_green                                       # groene LED knipperen
    global reset_blink, reset_blink_index, reset_blink_start # reset knipperen
    global ALT_value, AZ_value                               # ALT/AZ waarden

#- detecteer drukken en loslaten van SET knop
    if mcp[SET_button].value() == 0:         # knop is ingedrukt
        if SET_press_start == 0:             # nieuw druk
            SET_press_start = now            # start tijdstempel
    else:
        if SET_press_start != 0:             # knop is losgelaten
            duration = now - SET_press_start # bereken duur
            SET_press_start = 0              # reset tijdstempel

            stop_green_led()                 # stop knipperen

#- lange druk = reset naar 0
            if duration >= SECOND:
                ALT_value = 0
                AZ_value = 0
                print("RESET → ALT & AZ = 0")

                reset_blink = True # start reset knipperen
                reset_blink_index = 0 
                reset_blink_start = now 
                mcp[led_green].output(1)
            else:
                blink_green = True # start groene LED knipperen
                mcp[led_green].output(1)
                print("SET → waarden opgeslagen")


# =====================================================
# =============== LED KNIPPER LOGICA ==================
# =====================================================
#-- update de LED knipper status --
def update_led_blinking(now):
    global last_blink_time, last_blink_time_green
    global green_state
    global reset_blink, reset_blink_index, reset_blink_start

#- RESET knipperen heeft prioriteit
    if reset_blink:
        elapsed = now - reset_blink_start                         # tijd sinds laatste wissel
        if elapsed >= reset_blink_times[reset_blink_index]:       # tijd om te wisselen
            reset_blink_index += 1                                # ga naar volgende stap
            if reset_blink_index >= len(reset_blink_times):       # klaar met knipperen
                reset_blink = False                               # stop knipperen
                mcp[led_green].output(0)                          # zet LED uit
            else:
                reset_blink_start = now                           # reset tijdstempel
                mcp[led_green].output(reset_blink_index % 2 == 0) # wissel LED status
        return                                                    # sla de rest over
    
# -SET knipperen
    if blink_green and now - last_blink_time_green > BLINK_INTERVAL: # knipper interval verstreken
        last_blink_time_green = now                                  # update tijdstempel
        green_state ^= 1                                             # toggle status
        mcp[led_green].output(green_state)                           # update LED

# -Selectie knipperen
    if blink_selection and now - last_blink_time > BLINK_INTERVAL: # knipper interval verstreken
        last_blink_time = now                                      # update tijdstempel
        led = select_leds[current_selection]                       # bepaal geselecteerde LED
        mcp[led].output(0 if mcp[led].value() else 1)              # toggle LED


# =====================================================
# =============== MAIN LOOP ===========================
# =====================================================

while True:
    now = time.time()        # huidige tijd in seconden

    update_encoder(now)      # update de encoder status
    handle_alt_az_buttons()  # verwerk ALT/AZ knoppen
    handle_rotary_key(now)   # verwerk rotary encoder knop
    handle_set_button(now)   # verwerk SET knop
    update_led_blinking(now) # update LED knipper status

    time.sleep(0.001)        # korte pauze om CPU te ontlasten
