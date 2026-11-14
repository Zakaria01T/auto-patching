#include <stdio.h>
#include <string.h>

void header_line(const char *name, const char *value) {
    char h[32];
    snprintf(h, sizeof(h), "%s: %s", name, value);
    puts(h);
}
