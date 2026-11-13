#include <stdio.h>
#include <string.h>

void build_query(const char *term) {
    char q[48] = "search?q=";
    if (strlen(q) + strlen(term) >= sizeof(q)) {
        puts("query too long");
        return;
    }
    strcat(q, term);
    puts(q);
}
