#include <stdio.h>
#include <string.h>

void build_path(const char *name) {
    char path[32] = "/home/";
    strcat(path, name);
    puts(path);
}