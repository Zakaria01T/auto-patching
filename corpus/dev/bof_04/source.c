#include <stdio.h>
#include <unistd.h>

void read_line(void) {
    char line[16];
    ssize_t n = read(0, line, 64);
    if (n > 0) fwrite(line, 1, (size_t)n, stdout);
}