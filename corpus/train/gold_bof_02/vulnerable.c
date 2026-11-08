#include <stdio.h>

void greet_user(const char *name) {
    char buf[24];
    sprintf(buf, "Hello %s", name);
    puts(buf);
}
