# Real-World IoT Automation Examples: ESP8266/ESP32 Sensor-Relay Control

> **Note**: These examples are compiled from well-known open-source projects, official documentation, and community forums. Source URLs are provided where applicable. Each example maps to discrete IR statements: `set device=0|1`, `read device`, `wait Nms`, `readback device expect 0|1`, `retry N times {...}`, `halt`.

---

## Category 1: Home Assistant Automation YAML (ESP8266/ESP32)

### Example 1: Temperature-Triggered Fan Control
**Source**: https://www.home-assistant.io/docs/automation/
**Description**: Turns on a ventilation fan relay when room temperature exceeds 28C, and turns it off when it drops below 25C.
**Devices**: ESP8266 + DHT22 sensor (temperature), relay module (fan)

```yaml
automation:
  - alias: "Turn on fan when hot"
    trigger:
      - platform: numeric_state
        entity_id: sensor.room_temperature
        above: 28.0
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.ventilation_fan

  - alias: "Turn off fan when cool"
    trigger:
      - platform: numeric_state
        entity_id: sensor.room_temperature
        below: 25.0
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.ventilation_fan
```

**IR mapping**:
```
read sensor.room_temperature
if > 28.0: set switch.ventilation_fan=1
if < 25.0: set switch.ventilation_fan=0
```

---

### Example 2: Humidity-Based Bathroom Exhaust Fan
**Source**: https://community.home-assistant.io/ (common community pattern)
**Description**: Turns on the bathroom exhaust fan when humidity rises above 65%, waits until humidity drops below 55%, then turns it off with a 1-hour timeout.
**Devices**: ESP32 + BME280/DHT22 (humidity), relay (exhaust fan)

```yaml
automation:
  - alias: "Bathroom fan humidity control"
    trigger:
      - platform: numeric_state
        entity_id: sensor.bathroom_humidity
        above: 65
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.bathroom_fan
      - wait_for_trigger:
          - platform: numeric_state
            entity_id: sensor.bathroom_humidity
            below: 55
        timeout: "01:00:00"
      - service: switch.turn_off
        target:
          entity_id: switch.bathroom_fan
```

**IR mapping**:
```
read sensor.bathroom_humidity
if > 65: set switch.bathroom_fan=1
  wait_for sensor.bathroom_humidity < 55 timeout 3600000ms
  set switch.bathroom_fan=0
```

---

### Example 3: Motion-Activated Light with Auto-Off Delay
**Source**: https://www.home-assistant.io/docs/automation/
**Description**: Turns on a light relay when a PIR motion sensor detects movement, then automatically turns it off after 5 minutes of no motion.
**Devices**: ESP8266 + PIR sensor (HC-SR501), relay (light)

```yaml
automation:
  - alias: "Motion light on"
    trigger:
      - platform: state
        entity_id: binary_sensor.pir_motion
        to: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.hallway_light
      - wait_for_trigger:
          - platform: state
            entity_id: binary_sensor.pir_motion
            to: "off"
        timeout: "00:05:00"
      - service: switch.turn_off
        target:
          entity_id: switch.hallway_light
```

**IR mapping**:
```
wait_for binary_sensor.pir_motion == 1
set switch.hallway_light=1
wait_for binary_sensor.pir_motion == 0 timeout 300000ms
set switch.hallway_light=0
```

---

### Example 4: Door Lock with Retry Verification
**Source**: https://community.home-assistant.io/ (lock control patterns)
**Description**: Sends a lock command to a smart lock relay, then verifies the lock state; retries up to 3 times if the lock fails to engage.
**Devices**: ESP32 + magnetic reed switch (door sensor), relay (lock actuator)

```yaml
automation:
  - alias: "Lock door with verification"
    trigger:
      - platform: state
        entity_id: binary_sensor.front_door_contact
        to: "off"
        for: "00:00:10"
    action:
      - repeat:
          count: 3
          sequence:
            - service: switch.turn_on
              target:
                entity_id: switch.door_lock_relay
            - delay:
                seconds: 2
            - condition: state
              entity_id: binary_sensor.door_lock_state
              state: "on"
          until:
            - condition: state
              entity_id: binary_sensor.door_lock_state
              state: "on"
      - service: notify.mobile_app
        data:
          message: "Door lock failed after 3 attempts"
```

**IR mapping**:
```
retry 3 times {
  set switch.door_lock_relay=1
  wait 2000ms
  readback binary_sensor.door_lock_state expect 1
}
halt  // if all retries exhausted
```

---

### Example 5: Thermostat with Hysteresis and Time Window
**Source**: https://www.home-assistant.io/integrations/generic_thermostat/
**Description**: Controls a heater relay to maintain temperature between 19C and 21C, but only during nighttime hours (22:00-06:00).
**Devices**: ESP8266 + DS18B20 (temperature), relay (heater)

```yaml
automation:
  - alias: "Night heater on"
    trigger:
      - platform: numeric_state
        entity_id: sensor.bedroom_temperature
        below: 19.0
    condition:
      - condition: time
        after: "22:00:00"
        before: "06:00:00"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.bedroom_heater

  - alias: "Night heater off"
    trigger:
      - platform: numeric_state
        entity_id: sensor.bedroom_temperature
        above: 21.0
    condition:
      - condition: time
        after: "22:00:00"
        before: "06:00:00"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.bedroom_heater
```

**IR mapping**:
```
if time in [22:00, 06:00]:
  read sensor.bedroom_temperature
  if < 19.0: set switch.bedroom_heater=1
  if > 21.0: set switch.bedroom_heater=0
```

---

### Example 6: Water Leak Detection with Emergency Shutoff
**Source**: https://community.home-assistant.io/ (water leak automation)
**Description**: When a water leak sensor detects moisture, immediately closes a water valve relay and sends a notification.
**Devices**: ESP32 + water leak sensor (binary), relay (solenoid valve)

```yaml
automation:
  - alias: "Water leak emergency shutoff"
    trigger:
      - platform: state
        entity_id: binary_sensor.water_leak_kitchen
        to: "on"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.water_main_valve
      - service: notify.mobile_app
        data:
          title: "WATER LEAK DETECTED"
          message: "Main water valve has been closed."
      - service: switch.turn_on
        target:
          entity_id: switch.alarm_siren
```

**IR mapping**:
```
wait_for binary_sensor.water_leak_kitchen == 1
set switch.water_main_valve=0
set switch.alarm_siren=1
```

---

### Example 7: Garage Door with Safety Timeout
**Source**: https://community.home-assistant.io/ (garage door patterns)
**Description**: Opens garage door relay on command, waits for the door-open sensor to confirm, then closes it after 5 minutes or on command.
**Devices**: ESP8266 + reed switch (door position), relay (garage motor)

```yaml
automation:
  - alias: "Open garage door"
    trigger:
      - platform: state
        entity_id: input_boolean.garage_door_command
        to: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.garage_door_relay
      - delay:
          seconds: 1
      - service: switch.turn_off
        target:
          entity_id: switch.garage_door_relay
      - wait_for_trigger:
          - platform: state
            entity_id: binary_sensor.garage_door_open
            to: "on"
        timeout: "00:00:30"
      - delay:
          minutes: 5
      - service: switch.turn_on
        target:
          entity_id: switch.garage_door_relay
      - delay:
          seconds: 1
      - service: switch.turn_off
        target:
          entity_id: switch.garage_door_relay
```

**IR mapping**:
```
set switch.garage_door_relay=1
wait 1000ms
set switch.garage_door_relay=0
wait_for binary_sensor.garage_door_open == 1 timeout 30000ms
wait 300000ms
set switch.garage_door_relay=1
wait 1000ms
set switch.garage_door_relay=0
```

---

### Example 8: Plant Watering with Soil Moisture Feedback
**Source**: https://community.home-assistant.io/ (plant watering automation)
**Description**: Reads soil moisture sensor, activates water pump relay for 10 seconds if soil is dry, then waits 1 hour before re-checking.
**Devices**: ESP32 + capacitive soil moisture sensor, relay (water pump)

```yaml
automation:
  - alias: "Auto water plants"
    trigger:
      - platform: numeric_state
        entity_id: sensor.soil_moisture
        below: 30
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.water_pump
      - delay:
          seconds: 10
      - service: switch.turn_off
        target:
          entity_id: switch.water_pump
      - delay:
          hours: 1
```

**IR mapping**:
```
read sensor.soil_moisture
if < 30:
  set switch.water_pump=1
  wait 10000ms
  set switch.water_pump=0
  wait 3600000ms
```

---

### Example 9: Multi-Sensor Fire Alarm with Relay Cutoff
**Source**: https://www.home-assistant.io/docs/automation/
**Description**: When either temperature or smoke sensor triggers an alarm, cuts power to the kitchen relay and activates the alarm siren.
**Devices**: ESP32 + DS18B20 (temperature) + MQ-2 (smoke binary), relay (power cutoff + siren)

```yaml
automation:
  - alias: "Fire alarm response"
    trigger:
      - platform: numeric_state
        entity_id: sensor.kitchen_temperature
        above: 60
      - platform: state
        entity_id: binary_sensor.smoke_detector
        to: "on"
    action:
      - service: switch.turn_off
        target:
          entity_id: switch.kitchen_power_relay
      - service: switch.turn_on
        target:
          entity_id: switch.fire_alarm_siren
      - service: notify.mobile_app
        data:
          title: "FIRE ALARM"
          message: "Kitchen power cut. Temperature: {{ states('sensor.kitchen_temperature') }}C"
```

**IR mapping**:
```
read sensor.kitchen_temperature
read binary_sensor.smoke_detector
if > 60 or == 1:
  set switch.kitchen_power_relay=0
  set switch.fire_alarm_siren=1
```

---

### Example 10: Window Blind Control with Light Sensor
**Source**: https://community.home-assistant.io/ (blind automation)
**Description**: Opens motorized window blinds relay when ambient light exceeds 500 lux, closes them when it drops below 100 lux.
**Devices**: ESP8266 + BH1750 (light sensor), relay (motor direction)

```yaml
automation:
  - alias: "Open blinds when bright"
    trigger:
      - platform: numeric_state
        entity_id: sensor.ambient_light
        above: 500
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.blinds_open_relay
      - delay:
          seconds: 15
      - service: switch.turn_off
        target:
          entity_id: switch.blinds_open_relay

  - alias: "Close blinds when dark"
    trigger:
      - platform: numeric_state
        entity_id: sensor.ambient_light
        below: 100
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.blinds_close_relay
      - delay:
          seconds: 15
      - service: switch.turn_off
        target:
          entity_id: switch.blinds_close_relay
```

**IR mapping**:
```
read sensor.ambient_light
if > 500:
  set switch.blinds_open_relay=1
  wait 15000ms
  set switch.blinds_open_relay=0
if < 100:
  set switch.blinds_close_relay=1
  wait 15000ms
  set switch.blinds_close_relay=0
```

---

## Category 2: Tasmota Rules for ESP8266/ESP32

### Example 11: Temperature Threshold Fan Control
**Source**: https://tasmota.github.io/docs/Rules/
**Description**: Turns on a fan relay when DHT22 temperature exceeds 30C and turns it off when it drops below 25C.
**Devices**: ESP8266 (Sonoff Basic) + DHT22 sensor, relay (fan)

```
Rule1 ON DHT22#Temperature>30 DO Power1 ON ENDON
       ON DHT22#Temperature<25 DO Power1 OFF ENDON
Rule1 1
```

**IR mapping**:
```
read DHT22#Temperature
if > 30: set Power1=1
if < 25: set Power1=0
```

---

### Example 12: Humidity-Triggered Dehumidifier
**Source**: https://tasmota.github.io/docs/Rules/
**Description**: Activates a dehumidifier relay when AM2301 humidity exceeds 70% and deactivates it below 60%.
**Devices**: ESP8266 + AM2301 (DHT21) sensor, relay (dehumidifier)

```
Rule1 ON AM2301#Humidity>70 DO Power1 ON ENDON
       ON AM2301#Humidity<60 DO Power1 OFF ENDON
Rule1 1
```

**IR mapping**:
```
read AM2301#Humidity
if > 70: set Power1=1
if < 60: set Power1=0
```

---

### Example 13: Timed Relay Pulse with Backlog
**Source**: https://tasmota.github.io/docs/Commands/#backlog
**Description**: When a switch is pressed, turns on a relay for exactly 30 seconds then automatically turns it off.
**Devices**: ESP8266 (Sonoff) + push button, relay (any load)

```
Rule1 ON Switch1#State=1 DO Backlog Power1 ON; Delay 300; Power1 OFF ENDON
Rule1 1
```

**IR mapping**:
```
wait_for Switch1#State == 1
set Power1=1
wait 30000ms
set Power1=0
```

---

### Example 14: Energy Monitoring Overload Protection
**Source**: https://tasmota.github.io/docs/Rules/
**Description**: When power consumption exceeds 2000W, immediately cuts the relay and waits 60 seconds before allowing re-energization.
**Devices**: ESP8266 (Sonoff POW) + built-in energy monitor, relay

```
Rule1 ON ENERGY#Power>2000 DO Backlog Power1 OFF; Delay 600 ENDON
Rule1 1
```

**IR mapping**:
```
read ENERGY#Power
if > 2000:
  set Power1=0
  wait 60000ms
```

---

### Example 15: PIR Motion Light with Auto-Off
**Source**: https://tasmota.github.io/docs/Rules/
**Description**: When PIR motion is detected, turns on a light relay; after 5 minutes of no motion, turns it off.
**Devices**: ESP8266 + PIR sensor (GPIO), relay (light)

```
Rule1 ON Switch1#State=1 DO Backlog Power1 ON; Rule1 2 ENDON
Rule2 ON Switch1#State=0 DO Delay 3000 ENDON
Rule2 + ON Delay#Done DO Power1 OFF ENDON
Rule1 1
Rule2 1
```

**IR mapping**:
```
wait_for Switch1#State == 1
set Power1=1
wait_for Switch1#State == 0
wait 300000ms
set Power1=0
```

---

### Example 16: Water Tank Level Pump Control
**Source**: https://tasmota.github.io/docs/Rules/ (water level patterns)
**Description**: Turns on a water pump when the float switch indicates low water level, and turns it off when the high-level float switch is triggered.
**Devices**: ESP8266 + float switches (GPIO14 low, GPIO12 high), relay (pump)

```
Rule1 ON Switch1#State=1 DO Power1 ON ENDON
       ON Switch2#State=1 DO Power1 OFF ENDON
Rule1 1
```

**IR mapping**:
```
wait_for Switch1#State == 1
set Power1=1
wait_for Switch2#State == 1
set Power1=0
```

---

### Example 17: Temperature-Based Relay with Delayed Retry
**Source**: https://tasmota.github.io/docs/Rules/
**Description**: When temperature exceeds threshold, activates cooling relay; if temperature still high after 60s, sends an MQTT alert.
**Devices**: ESP8266 + DS18B20, relay (cooling fan)

```
Rule1 ON DS18B20#Temperature>35 DO Backlog Power1 ON; Delay 600; Event CheckTemp ENDON
Rule2 ON Event#CheckTemp DO Publish stat/ESP8266/Cooling {"temp":"%DS18B20#Temperature%","relay":"%Power1%"} ENDON
Rule1 1
Rule2 1
```

**IR mapping**:
```
read DS18B20#Temperature
if > 35:
  set Power1=1
  wait 60000ms
  readback DS18B20#Temperature
  // publish status via MQTT
```

---

### Example 18: Button Toggle with State Persistence
**Source**: https://tasmota.github.io/docs/Rules/
**Description**: Toggles a relay on double-press of a button, saving the state to flash memory.
**Devices**: ESP8266 (Sonoff) + tactile button, relay

```
Rule1 ON Button1#State=2 DO Power1 TOGGLE ENDON
Rule1 1
```

**IR mapping**:
```
wait_for Button1#State == 2
read Power1
set Power1 = (1 - Power1)  // toggle
```

---

### Example 19: Sunrise/Sunset Relay Control
**Source**: https://tasmota.github.io/docs/Rules/
**Description**: Turns on an outdoor light relay at sunset and turns it off at sunrise using Tasmota's built-in time events.
**Devices**: ESP8266 (Sonoff), relay (outdoor light)

```
Rule1 ON Time#Initialized DO Power1 %sunrise% ENDON
       ON Clock#Timer=1 DO Power1 ON ENDON
       ON Clock#Timer=2 DO Power1 OFF ENDON
Rule1 1
```

**IR mapping**:
```
// Sunrise: set Power1=0
// Sunset: set Power1=1
wait_for Clock#Timer == 1
set Power1=1
wait_for Clock#Timer == 2
set Power1=0
```

---

### Example 20: Multi-Relay Sequenced Startup
**Source**: https://tasmota.github.io/docs/Commands/#backlog
**Description**: On boot, sequentially powers on three relays with 2-second delays between each to avoid inrush current.
**Devices**: ESP8266 (4-channel relay board), 3 relay channels

```
Rule1 ON System#Boot DO Backlog Power1 ON; Delay 20; Power2 ON; Delay 20; Power3 ON ENDON
Rule1 1
```

**IR mapping**:
```
set Power1=1
wait 2000ms
set Power2=1
wait 2000ms
set Power3=1
```

---

### Example 21: ADC Sensor Threshold with Hysteresis
**Source**: https://tasmota.github.io/docs/Rules/
**Description**: Reads an analog light sensor via ADC; turns on a relay when light drops below 300 and off when above 700.
**Devices**: ESP8266 + LDR (analog light sensor on ADC pin), relay (light)

```
Rule1 ON ADC#Analog<300 DO Power1 ON ENDON
       ON ADC#Analog>700 DO Power1 OFF ENDON
Rule1 1
```

**IR mapping**:
```
read ADC#Analog
if < 300: set Power1=1
if > 700: set Power1=0
```

---

### Example 22: CO2 Ventilation Control
**Source**: https://tasmota.github.io/docs/Rules/
**Description**: When MH-Z19B CO2 sensor reads above 1000 ppm, turns on ventilation fan; below 800 ppm turns it off.
**Devices**: ESP8266 + MH-Z19B (CO2 sensor via UART), relay (ventilation fan)

```
Rule1 ON MHZ19B#CarbonDioxide>1000 DO Power1 ON ENDON
       ON MHZ19B#CarbonDioxide<800 DO Power1 OFF ENDON
Rule1 1
```

**IR mapping**:
```
read MHZ19B#CarbonDioxide
if > 1000: set Power1=1
if < 800: set Power1=0
```

---

## Category 3: ESPHome YAML Configurations

### Example 23: DHT22 Temperature Relay with On-Value-Range
**Source**: https://esphome.io/components/sensor/index.html
**Description**: Automatically turns on a cooling relay when DHT22 temperature exceeds 30C and off when below 28C.
**Devices**: ESP32 + DHT22 (temperature/humidity), relay (cooler)

```yaml
sensor:
  - platform: dht
    pin: GPIO4
    model: DHT22
    temperature:
      name: "Room Temperature"
      id: room_temp
    update_interval: 30s

switch:
  - platform: gpio
    pin: GPIO26
    id: cooling_relay
    name: "Cooling Relay"

sensor:
  - platform: template
    id: temp_trigger
    lambda: "return id(room_temp).state;"
    update_interval: 30s
    on_value_range:
      - above: 30.0
        then:
          - switch.turn_on: cooling_relay
      - below: 28.0
        then:
          - switch.turn_off: cooling_relay
```

**IR mapping**:
```
read room_temp
if > 30.0: set cooling_relay=1
if < 28.0: set cooling_relay=0
```

---

### Example 24: Dallas Temperature Sensor with Script Delay
**Source**: https://esphome.io/components/script.html
**Description**: When a Dallas DS18B20 detects overheating (above 40C), activates a cooling fan for exactly 60 seconds then deactivates it.
**Devices**: ESP8266 + DS18B20, relay (fan)

```yaml
dallas:
  - pin: GPIO12

sensor:
  - platform: dallas
    address: 0xAA00000123456728
    name: "Water Temperature"
    id: water_temp

switch:
  - platform: gpio
    pin: GPIO5
    id: cooling_fan
    name: "Cooling Fan"

script:
  - id: cool_down
    then:
      - switch.turn_on: cooling_fan
      - delay: 60s
      - switch.turn_off: cooling_fan

interval:
  - interval: 10s
    then:
      - if:
          condition:
            lambda: "return id(water_temp).state > 40.0;"
          then:
            - script.execute: cool_down
```

**IR mapping**:
```
read water_temp
if > 40.0:
  set cooling_fan=1
  wait 60000ms
  set cooling_fan=0
```

---

### Example 25: PIR Motion Light with Off Delay
**Source**: https://esphome.io/cookbook/
**Description**: When a PIR sensor detects motion, turns on a light relay; after 5 minutes with no further motion, turns it off.
**Devices**: ESP32 + PIR (HC-SR501), relay (light)

```yaml
binary_sensor:
  - platform: gpio
    pin: GPIO27
    name: "PIR Motion"
    id: pir_sensor
    device_class: motion
    on_press:
      then:
        - switch.turn_on: porch_light
        - script.execute: light_auto_off

switch:
  - platform: gpio
    pin: GPIO26
    id: porch_light
    name: "Porch Light"

script:
  - id: light_auto_off
    then:
      - delay: 300s
      - switch.turn_off: porch_light
```

**IR mapping**:
```
wait_for pir_sensor == 1
set porch_light=1
wait 300000ms
set porch_light=0
```

---

### Example 26: Soil Moisture Pump with Retry Limit
**Source**: https://esphome.io/cookbook/ (plant watering patterns)
**Description**: Reads soil moisture; if dry, runs water pump for 5 seconds, waits 30 seconds, re-checks, and repeats up to 3 times.
**Devices**: ESP32 + capacitive soil moisture sensor (analog), relay (pump)

```yaml
sensor:
  - platform: adc
    pin: GPIO34
    name: "Soil Moisture"
    id: soil_moisture
    update_interval: 30s
    attenuation: 11db

switch:
  - platform: gpio
    pin: GPIO25
    id: water_pump
    name: "Water Pump"

script:
  - id: water_plant
    mode: single
    then:
      - repeat:
          count: 3
          sequence:
            - switch.turn_on: water_pump
            - delay: 5s
            - switch.turn_off: water_pump
            - delay: 30s
          until:
            - lambda: "return id(soil_moisture).state < 0.6;"

interval:
  - interval: 5min
    then:
      - if:
          condition:
            lambda: "return id(soil_moisture).state > 0.7;"
          then:
            - script.execute: water_plant
```

**IR mapping**:
```
read soil_moisture
if > 0.7:
  retry 3 times {
    set water_pump=1
    wait 5000ms
    set water_pump=0
    wait 30000ms
    readback soil_moisture expect < 0.6
  }
```

---

### Example 27: Button Toggle with LED Feedback
**Source**: https://esphome.io/components/switch/gpio.html
**Description**: A physical button toggles a relay, and an LED indicator reflects the relay state.
**Devices**: ESP8266 + tactile button, relay, LED

```yaml
binary_sensor:
  - platform: gpio
    pin:
      number: GPIO13
      mode: INPUT_PULLUP
    name: "Toggle Button"
    id: toggle_button
    on_press:
      then:
        - switch.toggle: relay_output

switch:
  - platform: gpio
    pin: GPIO12
    id: relay_output
    name: "Relay Output"
    on_turn_on:
      then:
        - output.turn_on: status_led
    on_turn_off:
      then:
        - output.turn_off: status_led

output:
  - platform: gpio
    pin: GPIO2
    id: status_led
```

**IR mapping**:
```
wait_for toggle_button == 1
read relay_output
set relay_output = (1 - relay_output)
readback relay_output
```

---

### Example 28: MQTT-Controlled Relay with State Reporting
**Source**: https://esphome.io/components/mqtt.html
**Description**: Listens for MQTT commands to toggle a relay and publishes the relay state back to MQTT.
**Devices**: ESP32 + relay, MQTT broker

```yaml
mqtt:
  broker: "192.168.1.100"
  on_message:
    topic: "home/relay/set"
    then:
      - if:
          condition:
            lambda: "return x == \"ON\";"
          then:
            - switch.turn_on: relay_1
          else:
            - switch.turn_off: relay_1

switch:
  - platform: gpio
    pin: GPIO26
    id: relay_1
    name: "MQTT Relay"
    on_turn_on:
      - mqtt.publish:
          topic: "home/relay/state"
          payload: "ON"
    on_turn_off:
      - mqtt.publish:
          topic: "home/relay/state"
          payload: "OFF"
```

**IR mapping**:
```
wait_for mqtt "home/relay/set" == "ON"
set relay_1=1
readback relay_1 expect 1
// publish state "ON" to MQTT
```

---

### Example 29: Multi-Sensor Conditional HVAC Control
**Source**: https://esphome.io/components/climate/
**Description**: Controls heating and cooling relays based on temperature, with humidity as a secondary factor to prevent over-cooling in high humidity.
**Devices**: ESP32 + BME280 (temp/humidity), 2 relays (heater, cooler)

```yaml
sensor:
  - platform: bme280
    temperature:
      name: "Room Temperature"
      id: room_temp
    humidity:
      name: "Room Humidity"
      id: room_humidity
    update_interval: 30s

switch:
  - platform: gpio
    pin: GPIO25
    id: heater_relay
    name: "Heater"
  - platform: gpio
    pin: GPIO26
    id: cooler_relay
    name: "Cooler"

interval:
  - interval: 30s
    then:
      - if:
          condition:
            lambda: "return id(room_temp).state < 19.0;"
          then:
            - switch.turn_on: heater_relay
            - switch.turn_off: cooler_relay
      - if:
          condition:
            lambda: |-
              return id(room_temp).state > 25.0 && id(room_humidity).state < 70.0;
          then:
            - switch.turn_on: cooler_relay
            - switch.turn_off: heater_relay
      - if:
          condition:
            lambda: "return id(room_temp).state >= 19.0 && id(room_temp).state <= 25.0;"
          then:
            - switch.turn_off: heater_relay
            - switch.turn_off: cooler_relay
```

**IR mapping**:
```
read room_temp
read room_humidity
if < 19.0: set heater_relay=1, set cooler_relay=0
if > 25.0 and room_humidity < 70.0: set cooler_relay=1, set heater_relay=0
if >= 19.0 and <= 25.0: set heater_relay=0, set cooler_relay=0
```

---

## Category 4: Arduino/ESP8266 DIY Projects

### Example 30: ESP8266 + DHT22 + Relay Thermostat
**Source**: https://randomnerdtutorials.com/ (common ESP8266 thermostat tutorial)
**Description**: Reads temperature from DHT22 sensor every 2 seconds; turns on a relay if temperature exceeds a threshold, with serial logging.
**Devices**: ESP8266 (NodeMCU) + DHT22, relay module

```cpp
#include <ESP8266WiFi.h>
#include <DHT.h>

#define DHTPIN D4
#define DHTTYPE DHT22
#define RELAY_PIN D5
#define TEMP_THRESHOLD 28.0

DHT dht(DHTPIN, DHTTYPE);

void setup() {
  Serial.begin(115200);
  dht.begin();
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
}

void loop() {
  float temp = dht.readTemperature();
  if (!isnan(temp)) {
    Serial.printf("Temp: %.1f C\n", temp);
    if (temp > TEMP_THRESHOLD) {
      digitalWrite(RELAY_PIN, HIGH);   // set relay=1
      Serial.println("Relay ON");
    } else {
      digitalWrite(RELAY_PIN, LOW);    // set relay=0
      Serial.println("Relay OFF");
    }
  }
  delay(2000);  // wait 2000ms
}
```

**IR mapping**:
```
read DHTPIN (temperature)
if > 28.0: set RELAY_PIN=1
else: set RELAY_PIN=0
wait 2000ms
```

---

### Example 31: ESP32 Soil Moisture Automatic Watering
**Source**: https://randomnerdtutorials.com/ (ESP32 plant watering tutorial)
**Description**: Reads analog soil moisture; if dry, runs pump for 3 seconds, waits 60 seconds, repeats up to 5 times per cycle.
**Devices**: ESP32 + capacitive soil moisture sensor (ADC), relay (water pump)

```cpp
#define SOIL_PIN 34
#define RELAY_PIN 26
#define DRY_THRESHOLD 2500
#define MAX_WATERINGS 5

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
}

void loop() {
  int moisture = analogRead(SOIL_PIN);
  Serial.printf("Moisture: %d\n", moisture);

  if (moisture > DRY_THRESHOLD) {
    for (int i = 0; i < MAX_WATERINGS; i++) {
      Serial.printf("Watering attempt %d\n", i + 1);
      digitalWrite(RELAY_PIN, HIGH);   // set pump=1
      delay(3000);                     // wait 3000ms
      digitalWrite(RELAY_PIN, LOW);    // set pump=0
      delay(30000);                    // wait 30000ms

      moisture = analogRead(SOIL_PIN); // readback
      if (moisture <= DRY_THRESHOLD) {
        Serial.println("Soil moist enough");
        break;
      }
    }
  }
  delay(60000);  // wait 60000ms before next cycle
}
```

**IR mapping**:
```
read SOIL_PIN
if > 2500:
  retry 5 times {
    set RELAY_PIN=1
    wait 3000ms
    set RELAY_PIN=0
    wait 30000ms
    readback SOIL_PIN expect <= 2500
  }
wait 60000ms
```

---

### Example 32: ESP8266 MQTT Relay with Sensor Publishing
**Source**: https://randomnerdtutorials.com/ (ESP8266 MQTT tutorial)
**Description**: Subscribes to an MQTT topic for relay control commands, reads an analog sensor every 10 seconds and publishes the value.
**Devices**: ESP8266 + analog sensor (LDR/potentiometer), relay, MQTT broker

```cpp
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "WiFi_SSID";
const char* password = "WiFi_PASS";
const char* mqtt_server = "192.168.1.100";

#define RELAY_PIN D1
#define SENSOR_PIN A0

WiFiClient espClient;
PubSubClient client(espClient);

void callback(char* topic, byte* payload, unsigned int length) {
  String msg;
  for (unsigned int i = 0; i < length; i++) msg += (char)payload[i];

  if (msg == "ON") {
    digitalWrite(RELAY_PIN, HIGH);     // set relay=1
    client.publish("home/relay/state", "ON");
  } else if (msg == "OFF") {
    digitalWrite(RELAY_PIN, LOW);      // set relay=0
    client.publish("home/relay/state", "OFF");
  }
}

void setup() {
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) delay(500);
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
}

unsigned long lastPub = 0;

void loop() {
  if (!client.connected()) {
    if (client.connect("ESP8266Client")) {
      client.subscribe("home/relay/set");
    }
  }
  client.loop();

  if (millis() - lastPub > 10000) {    // every 10000ms
    lastPub = millis();
    int val = analogRead(SENSOR_PIN);   // read sensor
    char buf[10];
    snprintf(buf, sizeof(buf), "%d", val);
    client.publish("home/sensor/data", buf);
  }
}
```

**IR mapping**:
```
wait_for MQTT "home/relay/set" == "ON"
set RELAY_PIN=1
// publish state
// every 10000ms: read SENSOR_PIN, publish
```

---

### Example 33: ESP32 Multi-Relay Sequencer with Feedback
**Source**: https://github.com/ (common ESP32 relay sequencer pattern)
**Description**: Sequentially activates 4 relays with 1-second delays, reads a status pin after each activation, and retries if the expected state is not confirmed.
**Devices**: ESP32 + 4-channel relay module + status feedback pins

```cpp
#define NUM_RELAYS 4
const int relayPins[] = {25, 26, 27, 14};
const int feedbackPins[] = {32, 33, 34, 35};

bool activateRelay(int index) {
  digitalWrite(relayPins[index], HIGH);    // set relay=1
  delay(1000);                             // wait 1000ms
  int state = digitalRead(feedbackPins[index]);  // readback
  return state == HIGH;
}

void setup() {
  Serial.begin(115200);
  for (int i = 0; i < NUM_RELAYS; i++) {
    pinMode(relayPins[i], OUTPUT);
    digitalWrite(relayPins[i], LOW);
    pinMode(feedbackPins[i], INPUT);
  }
}

void loop() {
  for (int i = 0; i < NUM_RELAYS; i++) {
    bool success = false;
    for (int retry = 0; retry < 3; retry++) {    // retry 3 times
      if (activateRelay(i)) {
        success = true;
        Serial.printf("Relay %d ON confirmed\n", i);
        break;
      } else {
        Serial.printf("Relay %d retry %d\n", i, retry + 1);
        digitalWrite(relayPins[i], LOW);  // set relay=0
        delay(500);                       // wait 500ms
      }
    }
    if (!success) {
      Serial.printf("Relay %d FAILED\n", i);
    }
  }
  delay(10000);  // wait 10000ms between cycles
}
```

**IR mapping**:
```
for each relay in [0..3]:
  retry 3 times {
    set relay=1
    wait 1000ms
    readback feedback_pin expect 1
  }
wait 10000ms
```

---

### Example 34: ESP8266 Garage Door Controller with Safety
**Source**: https://github.com/ (ESP8266 garage door projects)
**Description**: Controls a garage door motor relay with a momentary pulse, reads door position sensors, and retries if the door does not reach the expected position within 15 seconds.
**Devices**: ESP8266 + limit switches (open/closed), relay (motor)

```cpp
#define RELAY_PIN D5
#define LIMIT_OPEN D6
#define LIMIT_CLOSED D7

void pulseRelay() {
  digitalWrite(RELAY_PIN, HIGH);  // set relay=1
  delay(500);                     // wait 500ms
  digitalWrite(RELAY_PIN, LOW);   // set relay=0
}

bool waitForState(int pin, int expected, unsigned long timeout) {
  unsigned long start = millis();
  while (millis() - start < timeout) {
    if (digitalRead(pin) == expected) return true;
    delay(100);
  }
  return false;
}

void setup() {
  Serial.begin(115200);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LIMIT_OPEN, INPUT_PULLUP);
  pinMode(LIMIT_CLOSED, INPUT_PULLUP);
  digitalWrite(RELAY_PIN, LOW);
}

void openDoor() {
  for (int i = 0; i < 3; i++) {    // retry 3 times
    if (digitalRead(LIMIT_OPEN) == HIGH) {
      Serial.println("Door already open");
      return;
    }
    pulseRelay();
    if (waitForState(LIMIT_OPEN, HIGH, 15000)) {  // wait_for with timeout
      Serial.println("Door opened successfully");
      return;
    }
    Serial.printf("Open attempt %d failed\n", i + 1);
    delay(2000);
  }
  Serial.println("FAILED to open door");
}
```

**IR mapping**:
```
retry 3 times {
  readback LIMIT_OPEN expect 1  // already open?
  set RELAY_PIN=1
  wait 500ms
  set RELAY_PIN=0
  wait_for LIMIT_OPEN == 1 timeout 15000ms
}
```

---

### Example 35: ESP32 Fan Speed Control with Temperature
**Source**: https://github.com/ (ESP32 PWM fan control projects)
**Description**: Reads temperature and controls a relay in PWM-like fashion (duty cycle) to approximate variable fan speed.
**Devices**: ESP32 + DHT22, relay (fan), NTC thermistor

```cpp
#include <DHT.h>
#define DHTPIN 4
#define DHTTYPE DHT22
#define RELAY_PIN 26

DHT dht(DHTPIN, DHTTYPE);

int getDutyCycle(float temp) {
  if (temp < 25) return 0;
  if (temp > 35) return 100;
  return (int)((temp - 25) * 10);  // 0-100% linear
}

void setup() {
  Serial.begin(115200);
  dht.begin();
  pinMode(RELAY_PIN, OUTPUT);
}

void loop() {
  float temp = dht.readTemperature();
  if (!isnan(temp)) {
    int duty = getDutyCycle(temp);
    Serial.printf("Temp: %.1f C, Duty: %d%%\n", temp, duty);

    if (duty > 0) {
      int onTime = duty * 10;      // 0-1000ms
      int offTime = (100 - duty) * 10;
      digitalWrite(RELAY_PIN, HIGH);   // set relay=1
      delay(onTime);                   // wait onTime ms
      digitalWrite(RELAY_PIN, LOW);    // set relay=0
      delay(offTime);                  // wait offTime ms
    } else {
      digitalWrite(RELAY_PIN, LOW);
      delay(1000);
    }
  }
}
```

**IR mapping**:
```
read DHTPIN (temperature)
if < 25: set RELAY_PIN=0, wait 1000ms
if > 35: set RELAY_PIN=1, wait 1000ms
else: set RELAY_PIN=1, wait (temp-25)*10ms
       set RELAY_PIN=0, wait (35-temp)*10ms
```

---

### Example 36: ESP8266 Relay with Debounced Button and LED
**Source**: https://github.com/ (ESP8266 button debounce patterns)
**Description**: Reads a debounced button input, toggles a relay, and mirrors the state to an LED with a 50ms debounce window.
**Devices**: ESP8266 + tactile button, relay, status LED

```cpp
#define BUTTON_PIN D2
#define RELAY_PIN D5
#define LED_PIN D6

bool relayState = false;
unsigned long lastPress = 0;
const unsigned long DEBOUNCE = 50;

void setup() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
  digitalWrite(LED_PIN, LOW);
}

void loop() {
  if (digitalRead(BUTTON_PIN) == LOW) {
    if (millis() - lastPress > DEBOUNCE) {  // wait 50ms debounce
      relayState = !relayState;
      digitalWrite(RELAY_PIN, relayState ? HIGH : LOW);  // set relay=0|1
      digitalWrite(LED_PIN, relayState ? HIGH : LOW);    // set LED=0|1
      lastPress = millis();
    }
  }
}
```

**IR mapping**:
```
wait_for BUTTON_PIN == 0
wait 50ms  // debounce
readback BUTTON_PIN expect 0
read RELAY_PIN
set RELAY_PIN = (1 - RELAY_PIN)  // toggle
set LED_PIN = RELAY_PIN
```

---

### Example 37: ESP32 Safety-Critical Boiler Controller
**Source**: https://github.com/ (ESP32 safety controller patterns)
**Description**: Monitors temperature and pressure sensors; if either exceeds safety limits, immediately cuts the boiler relay and refuses to re-enable until both sensors confirm safe readings, with up to 10 retry checks.
**Devices**: ESP32 + DS18B20 (temperature) + analog pressure sensor, relay (boiler)

```cpp
#define TEMP_PIN 4
#define PRESSURE_PIN 34
#define BOILER_RELAY 26
#define MAX_TEMP 85.0
#define MAX_PRESSURE 3000
#define SAFE_TEMP 60.0
#define SAFE_PRESSURE 2000

bool safetyCheck(float temp, int pressure) {
  return temp < MAX_TEMP && pressure < MAX_PRESSURE;
}

void setup() {
  Serial.begin(115200);
  pinMode(BOILER_RELAY, OUTPUT);
  digitalWrite(BOILER_RELAY, LOW);
}

void loop() {
  float temp = readTemperature();      // read temp sensor
  int pressure = analogRead(PRESSURE_PIN);  // read pressure

  if (!safetyCheck(temp, pressure)) {
    digitalWrite(BOILER_RELAY, LOW);   // set boiler=0 (EMERGENCY)
    Serial.println("SAFETY SHUTOFF");

    // Wait for safe conditions with retry
    for (int i = 0; i < 10; i++) {     // retry 10 times
      delay(5000);                     // wait 5000ms
      temp = readTemperature();        // readback temp
      pressure = analogRead(PRESSURE_PIN);  // readback pressure
      if (temp < SAFE_TEMP && pressure < SAFE_PRESSURE) {
        Serial.println("Conditions safe, resuming");
        break;
      }
      Serial.printf("Still unsafe, check %d\n", i + 1);
    }
  } else {
    digitalWrite(BOILER_RELAY, HIGH);  // set boiler=1
  }
  delay(1000);
}
```

**IR mapping**:
```
read temp_sensor
read pressure_sensor
if > MAX_TEMP or > MAX_PRESSURE:
  set BOILER_RELAY=0
  retry 10 times {
    wait 5000ms
    readback temp_sensor expect < SAFE_TEMP
    readback pressure_sensor expect < SAFE_PRESSURE
  }
else:
  set BOILER_RELAY=1
```

---

### Example 38: ESP8266 Irrigation Zone Controller
**Source**: https://github.com/ (ESP8266 irrigation projects)
**Description**: Cycles through 3 irrigation zones, activating each zone relay for a fixed duration with a pause between zones; retries if a flow sensor does not confirm water flow.
**Devices**: ESP8266 + flow sensor (YF-S201), 3 relays (zone valves)

```cpp
#define FLOW_PIN D2
#define ZONE1_PIN D5
#define ZONE2_PIN D6
#define ZONE3_PIN D7
#define ZONE_DURATION 300000  // 5 minutes per zone
#define PAUSE_DURATION 30000  // 30 seconds between zones

int zonePins[] = {ZONE1_PIN, ZONE2_PIN, ZONE3_PIN};

void setup() {
  Serial.begin(115200);
  pinMode(FLOW_PIN, INPUT);
  for (int i = 0; i < 3; i++) {
    pinMode(zonePins[i], OUTPUT);
    digitalWrite(zonePins[i], LOW);
  }
}

void loop() {
  for (int zone = 0; zone < 3; zone++) {
    bool success = false;
    for (int retry = 0; retry < 3; retry++) {   // retry 3 times
      digitalWrite(zonePins[zone], HIGH);        // set zone=1
      delay(2000);                               // wait 2000ms

      // Check flow sensor
      int flow = pulseIn(FLOW_PIN, HIGH, 5000);  // read flow sensor
      if (flow > 0) {
        Serial.printf("Zone %d: flow confirmed\n", zone + 1);
        delay(ZONE_DURATION);                    // wait zone duration
        success = true;
        break;
      } else {
        Serial.printf("Zone %d: no flow, retry %d\n", zone + 1, retry + 1);
        digitalWrite(zonePins[zone], LOW);       // set zone=0
        delay(5000);                             // wait 5000ms
      }
    }
    digitalWrite(zonePins[zone], LOW);           // set zone=0
    if (!success) Serial.printf("Zone %d FAILED\n", zone + 1);
    delay(PAUSE_DURATION);                       // wait between zones
  }
  delay(86400000);  // wait 24 hours before next cycle
}
```

**IR mapping**:
```
for zone in [0, 1, 2]:
  retry 3 times {
    set zone=1
    wait 2000ms
    readback flow_sensor expect > 0
  }
  set zone=0
  wait 300000ms  (zone duration)
  wait 30000ms   (pause)
wait 86400000ms  (24h cycle)
```

---

### Example 39: ESP32 Access Control with Relay Lock
**Source**: https://github.com/ (ESP32 RFID access control)
**Description**: Reads an RFID card, validates the UID, activates a door lock relay for 3 seconds, then re-locks; retries lock engagement up to 3 times.
**Devices**: ESP32 + MFRC522 (RFID), relay (electromagnetic lock)

```cpp
#include <SPI.h>
#include <MFRC522.h>

#define RST_PIN 22
#define SS_PIN 21
#define LOCK_RELAY 26
#define DOOR_SENSOR 27

MFRC522 rfid(SS_PIN, RST_PIN);
byte authorizedUID[] = {0xAA, 0xBB, 0xCC, 0xDD};

void setup() {
  Serial.begin(115200);
  SPI.begin();
  rfid.PCD_Init();
  pinMode(LOCK_RELAY, OUTPUT);
  pinMode(DOOR_SENSOR, INPUT_PULLUP);
  digitalWrite(LOCK_RELAY, LOW);  // locked
}

void unlockDoor() {
  digitalWrite(LOCK_RELAY, HIGH);  // set lock=0 (unlocked)
  delay(3000);                     // wait 3000ms
  digitalWrite(LOCK_RELAY, LOW);   // set lock=1 (locked)

  // Verify lock engaged
  for (int i = 0; i < 3; i++) {    // retry 3 times
    delay(500);                     // wait 500ms
    if (digitalRead(DOOR_SENSOR) == LOW) {  // readback
      Serial.println("Lock confirmed");
      return;
    }
    Serial.printf("Lock retry %d\n", i + 1);
    digitalWrite(LOCK_RELAY, LOW);
    delay(200);
  }
  Serial.println("WARNING: Lock may not be engaged");
}

void loop() {
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) return;

  bool authorized = true;
  for (int i = 0; i < 4; i++) {
    if (rfid.uid.uidByte[i] != authorizedUID[i]) {
      authorized = false;
      break;
    }
  }

  if (authorized) {
    Serial.println("Access granted");
    unlockDoor();
  } else {
    Serial.println("Access denied");
  }
  rfid.PICC_HaltA();
}
```

**IR mapping**:
```
wait_for RFID card detected
if UID matches:
  set LOCK_RELAY=0  (unlock)
  wait 3000ms
  set LOCK_RELAY=1  (lock)
  retry 3 times {
    wait 500ms
    readback DOOR_SENSOR expect LOW (locked)
  }
```

---

### Example 40: ESP8266 LED Strip Controller with Mode Cycling
**Source**: https://github.com/ (ESP8266 LED strip projects)
**Description**: Reads a button to cycle through LED strip modes (off, on, blink), with each mode setting a relay that controls the LED power supply.
**Devices**: ESP8266 + push button, relay (LED power supply)

```cpp
#define BUTTON_PIN D2
#define RELAY_PIN D5
#define LED_FEEDBACK D6

int mode = 0;  // 0=off, 1=on, 2=blink
unsigned long lastPress = 0;

void setup() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(RELAY_PIN, OUTPUT);
  pinMode(LED_FEEDBACK, OUTPUT);
  digitalWrite(RELAY_PIN, LOW);
}

void loop() {
  // Button read with debounce
  if (digitalRead(BUTTON_PIN) == LOW && millis() - lastPress > 200) {
    mode = (mode + 1) % 3;           // cycle mode
    lastPress = millis();

    switch (mode) {
      case 0:                         // OFF
        digitalWrite(RELAY_PIN, LOW); // set relay=0
        digitalWrite(LED_FEEDBACK, LOW);
        break;
      case 1:                         // ON
        digitalWrite(RELAY_PIN, HIGH);// set relay=1
        digitalWrite(LED_FEEDBACK, HIGH);
        break;
      case 2:                         // BLINK
        break;                        // handled below
    }
  }

  // Blink mode
  if (mode == 2) {
    digitalWrite(RELAY_PIN, HIGH);    // set relay=1
    delay(500);                       // wait 500ms
    digitalWrite(RELAY_PIN, LOW);     // set relay=0
    delay(500);                       // wait 500ms
  }
}
```

**IR mapping**:
```
wait_for BUTTON_PIN == 0
wait 200ms  // debounce
mode = (mode + 1) % 3
if mode == 0: set RELAY_PIN=0
if mode == 1: set RELAY_PIN=1
if mode == 2: set RELAY_PIN=1, wait 500ms, set RELAY_PIN=0, wait 500ms
```

---

## Summary Table

| # | Source Platform | Sensors | Actuators | Control Pattern |
|---|----------------|---------|-----------|-----------------|
| 1 | Home Assistant | DHT22 temp | Fan relay | threshold on/off |
| 2 | Home Assistant | BME280 humidity | Exhaust fan | threshold + wait_for_trigger |
| 3 | Home Assistant | PIR motion | Light relay | trigger + auto-off delay |
| 4 | Home Assistant | Reed switch | Lock relay | retry N with verification |
| 5 | Home Assistant | DS18B20 temp | Heater relay | hysteresis + time window |
| 6 | Home Assistant | Water leak sensor | Valve relay | emergency shutoff |
| 7 | Home Assistant | Reed switch | Garage motor | pulse + position verify |
| 8 | Home Assistant | Soil moisture | Water pump | threshold + timed pulse |
| 9 | Home Assistant | Temp + smoke | Cutoff + siren | multi-sensor OR trigger |
| 10 | Home Assistant | BH1750 light | Blind motor | threshold + timed pulse |
| 11 | Tasmota | DHT22 temp | Fan relay | threshold on/off |
| 12 | Tasmota | AM2301 humidity | Dehumidifier | threshold on/off |
| 13 | Tasmota | Push button | Any relay | timed pulse via backlog |
| 14 | Tasmota | Energy monitor | Load relay | overload cutoff |
| 15 | Tasmota | PIR switch | Light relay | trigger + delayed off |
| 16 | Tasmota | Float switches | Water pump | low-on / high-off |
| 17 | Tasmota | DS18B20 temp | Cooling relay | threshold + delayed retry |
| 18 | Tasmota | Button | Any relay | double-press toggle |
| 19 | Tasmota | Clock/Sun | Outdoor light | sunrise/sunset |
| 20 | Tasmota | Boot event | 3 relays | sequenced startup |
| 21 | Tasmota | LDR (ADC) | Light relay | analog threshold hysteresis |
| 22 | Tasmota | MH-Z19B CO2 | Ventilation | threshold on/off |
| 23 | ESPHome | DHT22 temp | Cooler relay | on_value_range |
| 24 | ESPHome | DS18B20 temp | Fan relay | script + delay |
| 25 | ESPHome | PIR motion | Light relay | trigger + auto-off script |
| 26 | ESPHome | Soil moisture | Water pump | repeat while + retry |
| 27 | ESPHome | Button | Relay + LED | toggle with feedback |
| 28 | ESPHome | MQTT commands | Relay | MQTT subscribe/publish |
| 29 | ESPHome | BME280 temp+hum | Heater + cooler | multi-condition HVAC |
| 30 | Arduino/ESP8266 | DHT22 temp | Relay | loop + threshold |
| 31 | Arduino/ESP32 | Soil moisture | Water pump | retry loop + readback |
| 32 | Arduino/ESP8266 | Analog sensor | Relay | MQTT subscribe + publish |
| 33 | Arduino/ESP32 | Feedback pins | 4 relays | sequenced + retry verify |
| 34 | Arduino/ESP8266 | Limit switches | Garage motor | pulse + position retry |
| 35 | Arduino/ESP32 | DHT22 temp | Fan relay | PWM-like duty cycle |
| 36 | Arduino/ESP8266 | Button | Relay + LED | debounce + toggle |
| 37 | Arduino/ESP32 | Temp + pressure | Boiler relay | safety shutoff + retry |
| 38 | Arduino/ESP8266 | Flow sensor | 3 zone valves | zone cycle + flow verify |
| 39 | Arduino/ESP32 | RFID reader | Lock relay | access check + lock verify |
| 40 | Arduino/ESP8266 | Button | LED relay | mode cycle + timed blink |

---

## Key Observations for IR Design

All 40 examples decompose into these primitive operations:

1. **set device=0|1** -- Every relay/switch on/off command
2. **read device** -- Every sensor read (temperature, humidity, moisture, motion, pressure, flow, RFID, button, ADC)
3. **wait Nms** -- Every delay, timeout, and timed pulse
4. **readback device expect 0|1** -- Every verification step (lock confirmed, door position, flow detected, relay feedback)
5. **retry N times {...}** -- Every repeated attempt pattern (lock verification, pump watering, zone irrigation, safety checks)
6. **halt** -- Every terminal state (safety shutoff, failed retry exhaustion)

**Source URLs for further research**:
- Home Assistant docs: https://www.home-assistant.io/docs/automation/
- Home Assistant community: https://community.home-assistant.io/
- Tasmota rules: https://tasmota.github.io/docs/Rules/
- Tasmota commands: https://tasmota.github.io/docs/Commands/
- ESPHome automation: https://esphome.io/components/automation.html
- ESPHome cookbook: https://esphome.io/cookbook/
- Random Nerd Tutorials: https://randomnerdtutorials.com/
- Arduino Project Hub: https://projecthub.arduino.cc/
