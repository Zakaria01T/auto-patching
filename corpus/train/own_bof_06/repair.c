#include <stdio.h>
#include <string.h>

void add_extension(const char *base) {
    char file[24] = "";
    strncat(file, base, sizeof(file) - strlen(file) - 1);
    strncat(file, ".txt", sizeof(file) - strlen(file) - 1);
    puts(file);
}
