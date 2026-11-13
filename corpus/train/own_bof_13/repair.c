#include <stdio.h>
#include <string.h>

void copy_packet(const char *payload, size_t len) {
    char buf[32];
    if (len > sizeof(buf)) {
        puts("packet too large");
        return;
    }
    memcpy(buf, payload, len);
    printf("%zu bytes, first %c\n", len, buf[0]);
}
