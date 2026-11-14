#include <stdio.h>
#include <string.h>

void add_prefix(const char *word) {
    char w[16] = "pre_";
    strncat(w, word, sizeof(w) - strlen(w) - 1);
    puts(w);
}
