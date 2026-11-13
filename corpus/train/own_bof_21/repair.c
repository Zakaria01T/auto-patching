#include <stdio.h>
#include <string.h>

void parse_command(const char *line) {
    char cmd[8];
    int n;
    if (sscanf(line, "%7s %d", cmd, &n) == 2)
        printf("%s x%d\n", cmd, n);
}
