#include <stddef.h>
#include <string.h>

void copy_data(const char *src, size_t len) {
    char buf[16];
    memcpy(buf, src, len);
}
