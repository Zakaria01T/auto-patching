#include <stdio.h>
#include <string.h>

void copy_name(const char *input) {
    char buf[16];
    strcpy(buf, input);
    puts(buf);
}