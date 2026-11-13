#include <stdio.h>
#include <string.h>

struct server {
    char host[32];
    int port;
};

void set_host(const char *host) {
    struct server cfg;
    if (strlen(host) >= sizeof(cfg.host)) {
        puts("host name too long");
        return;
    }
    strcpy(cfg.host, host);
    cfg.port = 80;
    printf("%s:%d\n", cfg.host, cfg.port);
}
