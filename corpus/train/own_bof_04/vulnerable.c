#include <stdio.h>
#include <string.h>

void print_level(const char *level) {
    char tag[8];
    strcpy(tag, level);
    printf("[%s]\n", tag);
}
