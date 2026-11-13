#include <stdio.h>
#include <string.h>

void print_level(const char *level) {
    char tag[8];
    snprintf(tag, sizeof(tag), "%s", level);
    printf("[%s]\n", tag);
}
