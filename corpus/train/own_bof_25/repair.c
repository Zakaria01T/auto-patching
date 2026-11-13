#include <stdio.h>
#include <string.h>

void country_code(const char *country) {
    char code[4];
    size_t n = strlen(country);
    if (n > 3)
        n = 3;
    memcpy(code, country, n);
    code[n] = '\0';
    puts(code);
}
