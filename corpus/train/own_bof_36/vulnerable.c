#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void copy_lines(const char *a, const char *b) {
    char *out = malloc(24);
    if (out == NULL)
        return;
    sprintf(out, "%s|%s", a, b);
    puts(out);
    free(out);
}
