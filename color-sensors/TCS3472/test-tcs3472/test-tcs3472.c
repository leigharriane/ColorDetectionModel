#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>
#include "pico/stdlib.h"
#include "hardware/i2c.h"

// -------------------- Pico 2 I2C --------------------
#define I2C_PORT i2c0
#define SDA_PIN  4
#define SCL_PIN  5

// -------------------- TCS3472x / TCS34725 --------------------
#define TCS3472X_ADDR 0x29
#define CMD_BIT       0x80

// Registers (TCS34725/TCS3472x family)
#define REG_ENABLE    0x00
#define REG_ATIME     0x01
#define REG_WTIME     0x03
#define REG_CONTROL   0x0F
#define REG_ID        0x12
#define REG_STATUS    0x13
#define REG_CDATAL    0x14  // C low, then C high, R low, R high, G low, G high, B low, B high

// ENABLE bits
#define ENABLE_PON    0x01
#define ENABLE_AEN    0x02

// STATUS bits
#define STATUS_AVALID 0x01  // RGBC valid

// Gain values (CONTROL)
#define GAIN_1X   0x00
#define GAIN_4X   0x01
#define GAIN_16X  0x02
#define GAIN_60X  0x03

// ---------- I2C helpers ----------
static inline int tcs_write8(uint8_t reg, uint8_t val) {
    uint8_t buf[2] = { (uint8_t)(CMD_BIT | reg), val };
    return i2c_write_blocking(I2C_PORT, TCS3472X_ADDR, buf, 2, false);
}

static inline int tcs_read8(uint8_t reg, uint8_t *val) {
    uint8_t r = (uint8_t)(CMD_BIT | reg);
    int ok = i2c_write_blocking(I2C_PORT, TCS3472X_ADDR, &r, 1, true);
    if (ok < 0) return ok;
    return i2c_read_blocking(I2C_PORT, TCS3472X_ADDR, val, 1, false);
}

static inline int tcs_read16(uint8_t reg, uint16_t *val) {
    uint8_t r = (uint8_t)(CMD_BIT | reg);
    int ok = i2c_write_blocking(I2C_PORT, TCS3472X_ADDR, &r, 1, true);
    if (ok < 0) return ok;

    uint8_t buf[2];
    ok = i2c_read_blocking(I2C_PORT, TCS3472X_ADDR, buf, 2, false);
    if (ok < 0) return ok;

    *val = (uint16_t)(buf[0] | ((uint16_t)buf[1] << 8));
    return ok;
}

static bool tcs_read_rgba(uint16_t *c, uint16_t *r, uint16_t *g, uint16_t *b) {
    // Reads C, R, G, B from consecutive 16-bit regs
    if (tcs_read16(REG_CDATAL + 0, c) < 0) return false;
    if (tcs_read16(REG_CDATAL + 2, r) < 0) return false;
    if (tcs_read16(REG_CDATAL + 4, g) < 0) return false;
    if (tcs_read16(REG_CDATAL + 6, b) < 0) return false;
    return true;
}

// ---------- Init ----------
static bool tcs3472x_init(void) {
    uint8_t id = 0;
    if (tcs_read8(REG_ID, &id) < 0) return false;

    // Common IDs:
    // TCS34725 often reports 0x44; other variants may differ (some show 0x4D, etc.).
    printf("TCS3472x ID: 0x%02X\n", id);

    // Power on
    if (tcs_write8(REG_ENABLE, ENABLE_PON) < 0) return false;
    sleep_ms(3);

    // Integration time (ATIME)
    // 0xEB ~ 50ms (good starting point)
    if (tcs_write8(REG_ATIME, 0xEB) < 0) return false;

    // Gain (CONTROL)
    if (tcs_write8(REG_CONTROL, GAIN_4X) < 0) return false;

    // Enable RGBC
    if (tcs_write8(REG_ENABLE, ENABLE_PON | ENABLE_AEN) < 0) return false;

    return true;
}

// ---------- Math helpers ----------
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

// ---------- Your classifier (unchanged) ----------
static const char* classify_color(uint16_t c, uint16_t r_raw, uint16_t g_raw, uint16_t b_raw) {
    if (c < 120) return "BLACK";

    float r = (float)r_raw / (float)c;
    float g = (float)g_raw / (float)c;
    float b = (float)b_raw / (float)c;

    r = clamp01(r);
    g = clamp01(g);
    b = clamp01(b);

    float mx = max3(r, g, b);
    float mn = min3(r, g, b);
    float sat = mx - mn;
    float avg = (r + g + b) / 3.0f;

    if (sat < 0.08f) {
        if (c < 250) return "BLACK";
        if (c > 1200 && avg > 0.28f) return "WHITE";
        return "GRAY";
    }

    if (c < 900 && r > 0.28f && g > 0.16f && b < 0.12f && r > g && (r - b) > 0.18f) {
        return "BROWN";
    }

    if (r > 0.32f && r > g + 0.10f && r > b + 0.10f) {
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

    if (r > 0.26f && g > 0.24f && b < 0.14f) {
        return "YELLOW";
    }

    if (r > 0.22f && b > 0.22f && g < 0.18f) {
        return "PURPLE";
    }

    return "UNKNOWN";
}

int main(void) {
    stdio_init_all();
    sleep_ms(2000);

    // I2C init
    i2c_init(I2C_PORT, 100 * 1000);
    gpio_set_function(SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(SCL_PIN, GPIO_FUNC_I2C);
    gpio_pull_up(SDA_PIN);
    gpio_pull_up(SCL_PIN);

    if (!tcs3472x_init()) {
        printf("TCS3472x init failed. Check wiring/address.\n");
        while (true) sleep_ms(1000);
    }

    while (true) {
        uint16_t c, r, g, b;

        // Optional: wait until data valid (prevents “same values” / stale reads sometimes)
        uint8_t status = 0;
        if (tcs_read8(REG_STATUS, &status) >= 0) {
            if (!(status & STATUS_AVALID)) {
                sleep_ms(10);
                continue;
            }
        }

        if (!tcs_read_rgba(&c, &r, &g, &b)) {
            printf("Read error.\n");
            sleep_ms(250);
            continue;
        }

        const char* color = classify_color(c, r, g, b);

        float rn = c ? (float)r / (float)c : 0.0f;
        float gn = c ? (float)g / (float)c : 0.0f;
        float bn = c ? (float)b / (float)c : 0.0f;

        printf("%-7s | C:%u R:%u G:%u B:%u | rn:%.2f gn:%.2f bn:%.2f\n",
               color, c, r, g, b, rn, gn, bn);

        sleep_ms(250);
    }
}
