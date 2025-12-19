#include <Arduino.h>
#include <avr/sleep.h>
#include <avr/wdt.h>
#include <avr/power.h>

volatile bool watchdogFired = false;

/**
 * Interruption Watchdog
 */
ISR(WDT_vect)
{
    watchdogFired = true;
}

/**
 * Configuration du Watchdog
 * Timeout ~8 secondes (valeur maximale)
 */
void setupWatchdog()
{
    cli();

    wdt_reset();

    // Autorise la modification du watchdog
    WDTCSR |= (1 << WDCE) | (1 << WDE);

    // Mode interruption uniquement, pas de reset
    WDTCSR = (1 << WDIE) | (1 << WDP3) | (1 << WDP0);

    sei();
}

/**
 * Mise en deep sleep (Power-down)
 */
void enterDeepSleep()
{
    set_sleep_mode(SLEEP_MODE_PWR_DOWN);
    sleep_enable();

    // Désactivation des périphériques internes
    power_adc_disable();
    power_spi_disable();
    power_timer0_disable();
    power_timer1_disable();
    power_timer2_disable();
    power_twi_disable();
    power_usart0_disable();

    sleep_cpu(); // CPU endormi ici

    // Réveil
    sleep_disable();

    // Réactivation minimale si nécessaire
    power_all_enable();
}

void setup()
{
    // Désactive le comparateur analogique
    ACSR |= (1 << ACD);

    // Met toutes les broches en entrée sans pull-up
    for (uint8_t pin = 0; pin < 20; pin++)
    {
        pinMode(pin, INPUT);
        digitalWrite(pin, LOW);
    }

    setupWatchdog();
}

void loop()
{
    watchdogFired = false;

    enterDeepSleep();

    if (watchdogFired)
    {
       
    }
}
