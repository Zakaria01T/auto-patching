#include <stdio.h>
#include <string.h>

struct session {
    char id[16];
    int active;
};

void open_session(const char *id) {
    struct session s;
    memcpy(s.id, id, strlen(id) + 1);
    s.active = 1;
    printf("%s %d\n", s.id, s.active);
}
