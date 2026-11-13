#include <stdio.h>
#include <string.h>

void save_key(const char *key) {
    char k[16];
    size_t n = strlen(key);
    if (n > sizeof(k) - 1)
        n = sizeof(k) - 1;
    memcpy(k, key, n);
    k[n] = '\0';
    puts(k);
}
