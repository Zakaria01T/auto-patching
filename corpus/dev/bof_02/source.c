#include <stdio.h>

void greet(const char *name) {
    char buf[32];
    sprintf(buf, "Hello %s", name);
    puts(buf);
}
