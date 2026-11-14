#include <stdio.h>
#include <string.h>

void make_filename(const char *name, const char *ext) {
    char f[16];
    sprintf(f, "%s.%s", name, ext);
    puts(f);
}
