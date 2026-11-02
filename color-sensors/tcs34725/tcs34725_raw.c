/**
 * tcs34725_raw.c - Wiring smoke test for a TCS34725 colour sensor
 *
 * Target : Raspberry Pi Pico 2 W (see CMakeLists.txt), Pico SDK 2.2.0
 * Output : USB serial, "C:<n> R:<n> G:<n> B:<n>" four times a second
 *
 * Minimal program that initialises the sensor over I2C (50 ms integration,
 * 4x gain) and streams the raw 16-bit clear/red/green/blue counts.  Use it
 * first to confirm wiring and the I2C address, then flash
 * tcs34725_classify.c for the colour-naming version.
 *
 * Wiring (I2C0):  SDA -> GP4, SCL -> GP5, VIN -> 3V3, GND -> GND.
 * Address 0x29.  The chip ID printed at boot should be 0x44 (or 0x4D).
 */

#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"

#define I2C_PORT i2c0
#define SDA_PIN 4
#define SCL_PIN 5

#define TCS34725_ADDR 0x29
#define CMD_BIT 0x80

// Registers
#define REG_ENABLE  0x00
#define REG_ATIME   0x01
#define REG_CONTROL 0x0F
#define REG_ID      0x12
#define REG_CDATAL  0x14  // Clear data low, then +1 +2 +3 ... for R,G,B

// ENABLE bits

#define ENABLE_PON  0x01
#define ENABLE_AEN  0x02

static inline int tcs_write8(uint8_t reg, uint8_t val) {
    uint8_t buf[2] = { (uint8_t)(CMD_BIT | reg), val };
    return i2c_write_blocking(I2C_PORT, TCS34725_ADDR, buf, 2, false);
}

static inline int tcs_read8(uint8_t reg, uint8_t *val) {
    uint8_t r = (uint8_t)(CMD_BIT | reg);
    int ok = i2c_write_blocking(I2C_PORT, TCS34725_ADDR, &r, 1, true);
    if (ok < 0) return ok;
    return i2c_read_blocking(I2C_PORT, TCS34725_ADDR, val, 1, false);
}

static inline int tcs_read16(uint8_t reg, uint16_t *val) {
    uint8_t r = (uint8_t)(CMD_BIT | reg);
    int ok = i2c_write_blocking(I2C_PORT, TCS34725_ADDR, &r, 1, true);
    if (ok < 0) return ok;

    uint8_t buf[2];
    ok = i2c_read_blocking(I2C_PORT, TCS34725_ADDR, buf, 2, false);
    if (ok < 0) return ok;

    *val = (uint16_t)(buf[0] | (buf[1] << 8));
    return ok;
}

static bool tcs34725_init(void) {
    uint8_t id = 0;
    if (tcs_read8(REG_ID, &id) < 0) return false;

    // ID is often 0x44 or 0x4D depending on variant/breakout.
    printf("TCS34725 ID: 0x%02X\n", id);

    // Power ON
    if (tcs_write8(REG_ENABLE, ENABLE_PON) < 0) return false;
    sleep_ms(3);

    // Integration time: 0xEB ~ 50ms (good starter)
    if (tcs_write8(REG_ATIME, 0xEB) < 0) return false;

    // Gain: 0x01 = 4x (0x00=1x, 0x01=4x, 0x02=16x, 0x03=60x)
    if (tcs_write8(REG_CONTROL, 0x01) < 0) return false;

    // Enable RGBC
    if (tcs_write8(REG_ENABLE, ENABLE_PON | ENABLE_AEN) < 0) return false;

    return true;
}

int main() {
    stdio_init_all();
    sleep_ms(2000);

    i2c_init(I2C_PORT, 100 * 1000);
    gpio_set_function(SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(SCL_PIN, GPIO_FUNC_I2C);
    gpio_pull_up(SDA_PIN);
    gpio_pull_up(SCL_PIN);

    if (!tcs34725_init()) {
        printf("TCS34725 init failed. Check wiring/address.\n");
        while (true) sleep_ms(1000);
    }

    while (true) {
        uint16_t c, r, g, b;
        tcs_read16(REG_CDATAL + 0, &c);
        tcs_read16(REG_CDATAL + 2, &r);
        tcs_read16(REG_CDATAL + 4, &g);
        tcs_read16(REG_CDATAL + 6, &b);

        printf("C:%u R:%u G:%u B:%u\n", c, r, g, b);
        sleep_ms(250);
    }
}
