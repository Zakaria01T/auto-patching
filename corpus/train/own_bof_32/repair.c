#include <stdio.h>
#include <string.h>

void line_prefix(const char *line, size_t n) {
    char prefix[10];
    if (n >= sizeof(prefix))
        n = sizeof(prefix) - 1;
    memcpy(prefix, line, n);
    prefix[n] = '\0';
    puts(prefix);
}
