#include <string.h>

void full_name(const char *first, const char *last) {
    char name[20];
    strcpy(name, first);
    strcat(name, " ");
    strcat(name, last);
}
