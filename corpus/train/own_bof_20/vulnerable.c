#include <stdio.h>
#include <string.h>

void parse_name(const char *line) {
    char first[10], last[10];
    if (sscanf(line, "%s %s", first, last) == 2)
        printf("%s, %s\n", last, first);
}
