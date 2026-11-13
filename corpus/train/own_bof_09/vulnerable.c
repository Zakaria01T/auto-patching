#include <stdio.h>
#include <string.h>

void format_price(const char *product, int cents) {
    char line[24];
    sprintf(line, "%s: %d.%02d", product, cents / 100, cents % 100);
    puts(line);
}
