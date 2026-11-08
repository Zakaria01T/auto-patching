#include <stdio.h>
#include <string.h>

void show_path(const char *file) {
    char path[32] = "/data/";
    strncat(path, file, sizeof(path) - strlen(path) - 1);
    puts(path);
}
