#include <stdio.h>
#include <string.h>

void parse_name(const char *line) {
    char first[10], last[10];
    if (sscanf(line, "%9s %9s", first, last) == 2)
        printf("%s, %s\n", last, first);
}
