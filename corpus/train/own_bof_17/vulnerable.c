#include <stdio.h>
#include <string.h>

void set_title(const char *title) {
    char t[16];
    strncpy(t, title, strlen(title) + 1);
    puts(t);
}
