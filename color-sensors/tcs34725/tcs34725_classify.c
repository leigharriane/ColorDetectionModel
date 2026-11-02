/**
 * tcs34725_classify.c - Colour classification with a TCS34725 (I2C) sensor
 *
 * Target : Raspberry Pi Pico 2 W (see CMakeLists.txt), Pico SDK 2.2.0
 * Output : USB serial (printf), one line every ~250 ms
 *
 * Reads the clear/red/green/blue 16-bit counts, divides R, G and B by the
 * clear count so the ratios are mostly independent of brightness, and maps
 * them to a colour name with simple threshold rules (black/white/grey first
 * by saturation and brightness, then brown, then the dominant channel).
 *
 * Same sensor family and register map as ../tcs3472/tcs3472_classify.c; that
 * version additionally waits for the data-valid flag and checks read errors.
 *
 * Wiring (I2C0):  SDA -> GP4, SCL -> GP5, VIN -> 3V3, GND -> GND.
 * Address 0x29.  Tie the breakout's LED pin to GND to switch its LED off.
 *
 * Serial line format:
 *   NAME    | C:<raw> R:<raw> G:<raw> B:<raw> | rn:<R/C> gn:<G/C> bn:<B/C>
 * Use the ratios to retune the constants in classify_color().
 */

#include <stdio.h>
#include <math.h>
#include <stdint.h>
#include <stdbool.h>
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

    printf("TCS34725 ID: 0x%02X\n", id);

    if (tcs_write8(REG_ENABLE, ENABLE_PON) < 0) return false;
    sleep_ms(3);

    // Integration time: 0xEB ~ 50ms (starter)
    if (tcs_write8(REG_ATIME, 0xEB) < 0) return false;

    // Gain: 4x
    if (tcs_write8(REG_CONTROL, 0x01) < 0) return false;

    if (tcs_write8(REG_ENABLE, ENABLE_PON | ENABLE_AEN) < 0) return false;

    return true;
}

static inline float clamp01(float x) {
    if (x < 0.0f) return 0.0f;
    if (x > 1.0f) return 1.0f;
    return x;
}

static inline float max3(float a, float b, float c) {
    float m = a;
    if (b > m) m = b;
    if (c > m) m = c;
    return m;
}

static inline float min3(float a, float b, float c) {
    float m = a;
    if (b < m) m = b;
    if (c < m) m = c;
    return m;
}

// Simple heuristics color classifier.
// Uses normalized r,g,b = channel / clear to reduce brightness dependence.
// Also uses clear (c) to detect black/white/gray.
static const char* classify_color(uint16_t c, uint16_t r_raw, uint16_t g_raw, uint16_t b_raw) {
    // If clear is extremely low, it’s basically dark/black or too far away.
    if (c < 120) return "BLACK";

    float r = (float)r_raw / (float)c;
    float g = (float)g_raw / (float)c;
    float b = (float)b_raw / (float)c;

    r = clamp01(r);
    g = clamp01(g);
    b = clamp01(b);

    float mx = max3(r, g, b);
    float mn = min3(r, g, b);
    float sat = mx - mn; // rough saturation (0 = gray-ish)
    float avg = (r + g + b) / 3.0f;

    // Neutral colors first (low saturation)
    if (sat < 0.08f) {
        if (c < 250) return "BLACK";
        if (c > 1200 && avg > 0.28f) return "WHITE";
        return "GRAY";
    }

    // Brown: usually "dark orange" (red dominant, green somewhat high, blue low) + not super bright
    // This is heuristic; you may need to tune thresholds for your lighting/material.
    if (c < 900 && r > 0.28f && g > 0.16f && b < 0.12f && r > g && (r - b) > 0.18f) {
        return "BROWN";
    }

    // Primary-ish
    if (r > 0.32f && r > g + 0.10f && r > b + 0.10f) {
        // Could be red/pink/orange depending on green/blue
        if (b > 0.20f && g < 0.20f) return "PINK";
        if (g > 0.22f && b < 0.14f) return "ORANGE";
        return "RED";
    }

    if (g > 0.30f && g > r + 0.08f && g > b + 0.08f) {
        return "GREEN";
    }

    if (b > 0.26f && b > r + 0.08f && b > g + 0.08f) {
        return "BLUE";
    }

    // Secondary-ish
    // Yellow: R and G high, B low
    if (r > 0.26f && g > 0.24f && b < 0.14f) {
        return "YELLOW";
    }

    // Purple: R and B relatively high, G low
    if (r > 0.22f && b > 0.22f && g < 0.18f) {
        return "PURPLE";
    }

    return "UNKNOWN";
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

        const char* color = classify_color(c, r, g, b);

        // Print both raw and normalized classification result for easy tuning
        float rn = (c ? (float)r / (float)c : 0.0f);
        float gn = (c ? (float)g / (float)c : 0.0f);
        float bn = (c ? (float)b / (float)c : 0.0f);

        printf("%-7s | C:%u R:%u G:%u B:%u | rn:%.2f gn:%.2f bn:%.2f\n",
               color, c, r, g, b, rn, gn, bn);

        sleep_ms(250);
    }
}
