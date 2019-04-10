

#ifndef __TIMERS__
#define __TIMERS__

#include <avr/io.h>

#ifdef __cplusplus
extern "C"
{
#endif

    void timer0_init(uint8_t ctcon, uint16_t ps, uint8_t ocr0a)
    {
        //set timer0 interrupt at 2kHz

        TCCR0A = 0; // set entire TCCR0A register to 0
        TCCR0B = 0; // same for TCCR0B
        TCNT0 = 0;  //initialize counter value to 0

        if (ctcon)
        {
            // set compare match register for 2khz increments
            OCR0A = ocr0a; // = (16*10^6) / (2000*64) - 1 (must be <256)
            // turn on CTC mode
            TCCR0A |= (1 << WGM01);
        }

        switch (ps)
        {
        case 1:
        {
            TCCR0B |= (1 << CS00);
            break;
        }
        case 8:
        {
            TCCR0B |= (1 << CS01);
            break;
        }
        case 64:
        {
            TCCR0B |= (1 << CS01) | (1 << CS00);
            break;
        }
        case 256:
        {
            TCCR0B |= (1 << CS02);
            break;
        }
        case 1024:
        {
            TCCR0B |= (1 << CS02) | (1 << CS00);
            break;
        }
        default:
        {
            break;
        }
        }

        if (ctcon)
            // enable timer compare interrupt
            TIMSK0 |= (1 << OCIE0A);
        else
            TIMSK0 |= (1 << TOIE0); // enable timer overflow interrupt
    }

    //15624
    void timer1_init(uint8_t ctcon, uint16_t ps, uint16_t ocr1a)
    {
        //set timer1 interrupt at 1Hz
        TCCR1A = 0; // set entire TCCR1A register to 0
        TCCR1B = 0; // same for TCCR1B
        TCNT1 = 0;  //initialize counter value to 0

        if (ctcon)
        {
            // set compare match register for 1hz increments
            OCR1A = ocr1a; // = (16*10^6) / (1*1024) - 1 (must be <65536)
            // turn on CTC mode
            TCCR1B |= (1 << WGM12);
        }

        switch (ps)
        {
        case 1:
        {
            TCCR1B |= (1 << CS10);
            break;
        }
        case 8:
        {
            TCCR1B |= (1 << CS11);
            break;
        }
        case 64:
        {
            TCCR1B |= (1 << CS11) | (1 << CS10);
            break;
        }
        case 256:
        {
            TCCR1B |= (1 << CS12);
            break;
        }
        case 1024:
        {
            TCCR1B |= (1 << CS12) | (1 << CS10);
            break;
        }
        default:
        {
            break;
        }
        }

        // Set CS10 and CS12 bits for 1024 prescaler
        //TCCR1B |= (1 << CS12) | (1 << CS10);
        // enable timer compare interrupt
        if (ctcon)
            TIMSK1 |= (1 << OCIE1A);
        else
            TIMSK1 |= (1 << TOIE1); // enable timer overflow interrupt
    }
    //249
    void timer2_init(uint8_t ctcon, uint16_t ps, uint8_t ocr2a)
    {
        //set timer2 interrupt at 8kHz

        TCCR2A = 0; // set entire TCCR2A register to 0
        TCCR2B = 0; // same for TCCR2B
        TCNT2 = 0;  //initialize counter value to 0

        if (ctcon)
        {
            // set compare match register for 8khz increments
            OCR2A = ocr2a; // = (16*10^6) / (8000*8) - 1 (must be <256)
            // turn on CTC mode
            TCCR2A |= (1 << WGM21);
        }

        switch (ps)
        {
        case 1:
        {
            TCCR2B |= (1 << CS20);
            break;
        }
        case 8:
        {
            TCCR2B |= (1 << CS21);
            break;
        }
        case 32:
        {
            TCCR2B |= (1 << CS21) | (1 << CS20);
            break;
        }
        case 64:
        {
            TCCR2B |= (1 << CS22);
            break;
        }
        default:
        {
            break;
        }
        }

        // Set CS21 bit for 8 prescaler
        //TCCR2B |= (1 << CS21);
        if (ctcon)
            // enable timer compare interrupt
            TIMSK2 |= (1 << OCIE2A);
        else
            TIMSK2 |= (1 << TOIE2); // enable timer overflow interrupt
    }

#ifdef __cplusplus
}
#endif

#endif