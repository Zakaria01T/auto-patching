#include <stdio.h>
#include <string.h>

void copy_packet(const char *payload, size_t len) {
    char buf[32];
    memcpy(buf, payload, len);
    printf("%zu bytes, first %c\n", len, buf[0]);
}
