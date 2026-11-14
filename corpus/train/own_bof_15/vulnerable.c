#include <stdio.h>
#include <string.h>

void save_key(const char *key) {
    char k[16];
    memcpy(k, key, strlen(key) + 1);
    puts(k);
}
