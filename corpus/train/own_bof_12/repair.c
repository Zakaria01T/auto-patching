#include <stdio.h>
#include <string.h>

void temp_path(const char *dir, int id) {
    char p[20];
    snprintf(p, sizeof(p), "%s/tmp%d", dir, id);
    puts(p);
}
