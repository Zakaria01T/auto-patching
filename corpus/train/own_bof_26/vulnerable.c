#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void save_comment(const char *text) {
    char *c = malloc(32);
    if (c == NULL)
        return;
    strcpy(c, text);
    puts(c);
    free(c);
}
