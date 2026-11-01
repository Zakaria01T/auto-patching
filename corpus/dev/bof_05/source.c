#include <stdio.h>

void make_label(const char *id, const char *tag) {
    char label[24];
    sprintf(label, "%s-%s", id, tag);
    puts(label);
}
