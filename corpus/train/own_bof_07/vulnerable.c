#include <stdio.h>
#include <string.h>

void build_query(const char *term) {
    char q[48] = "search?q=";
    strcat(q, term);
    puts(q);
}
