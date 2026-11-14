#include <stdio.h>
#include <string.h>

void header_line(const char *name, const char *value) {
    char h[32];
    sprintf(h, "%s: %s", name, value);
    puts(h);
}
