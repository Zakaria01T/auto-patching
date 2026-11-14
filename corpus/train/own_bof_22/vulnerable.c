#include <stdio.h>
#include <string.h>

void parse_setting(const char *line) {
    char key[8], value[8];
    if (sscanf(line, "%[^=]=%s", key, value) == 2)
        printf("%s -> %s\n", key, value);
}
