#include <stdio.h>
#include <string.h>

void set_title(const char *title) {
    char t[16];
    strncpy(t, title, sizeof(t) - 1);
    t[sizeof(t) - 1] = '\0';
    puts(t);
}
