#include <stdio.h>
#include <string.h>

void parse_date(const char *s) {
    char month[4];
    int day, year;
    if (sscanf(s, "%d %s %d", &day, month, &year) == 3)
        printf("%s %d, %d\n", month, day, year);
}
