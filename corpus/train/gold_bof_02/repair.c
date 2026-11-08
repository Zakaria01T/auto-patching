#include <stdio.h>

void greet_user(const char *name) {
    char buf[24];
    snprintf(buf, sizeof(buf), "Hello %s", name);
    puts(buf);
}
