#include <stdio.h>
#include <string.h>

void country_code(const char *country) {
    char code[4];
    memcpy(code, country, strlen(country));
    code[3] = '\0';
    puts(code);
}
