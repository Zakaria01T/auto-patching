#include <stdio.h>
#include <string.h>

void show_path(const char *file) {
    char path[32] = "/data/";
    strcat(path, file);
    puts(path);
}
