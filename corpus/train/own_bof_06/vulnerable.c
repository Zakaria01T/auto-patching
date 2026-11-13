#include <stdio.h>
#include <string.h>

void add_extension(const char *base) {
    char file[24] = "";
    strcat(file, base);
    strcat(file, ".txt");
    puts(file);
}
