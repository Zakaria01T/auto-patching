#include <stdio.h>
#include <string.h>

struct session {
    char id[16];
    int active;
};

void open_session(const char *id) {
    struct session s;
    size_t n = strlen(id);
    if (n >= sizeof(s.id)) {
        puts("session id too long");
        return;
    }
    memcpy(s.id, id, n + 1);
    s.active = 1;
    printf("%s %d\n", s.id, s.active);
}
