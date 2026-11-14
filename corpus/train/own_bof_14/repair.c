#include <stdio.h>
#include <string.h>

void first_field(const char *line) {
    char field[12];
    const char *comma = strchr(line, ',');
    size_t n = comma ? (size_t)(comma - line) : strlen(line);
    if (n >= sizeof(field))
        n = sizeof(field) - 1;
    memcpy(field, line, n);
    field[n] = '\0';
    puts(field);
}
