#include <stdio.h>
#include <string.h>

void tag_list(const char *a, const char *b) {
    char tags[20] = "";
    strncat(tags, a, sizeof(tags) - strlen(tags) - 1);
    strncat(tags, ",", sizeof(tags) - strlen(tags) - 1);
    strncat(tags, b, sizeof(tags) - strlen(tags) - 1);
    puts(tags);
}
