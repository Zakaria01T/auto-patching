#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void save_comment(const char *text) {
    char *c = malloc(32);
    if (c == NULL)
        return;
    snprintf(c, 32, "%s", text);
    puts(c);
    free(c);
}
