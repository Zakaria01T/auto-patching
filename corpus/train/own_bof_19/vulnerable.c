#include <stdio.h>
#include <string.h>

void tag_list(const char *a, const char *b) {
    char tags[20] = "";
    strncat(tags, a, 20);
    strncat(tags, ",", 1);
    strncat(tags, b, 20);
    puts(tags);
}
