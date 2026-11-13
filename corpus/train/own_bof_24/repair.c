#include <stdio.h>
#include <string.h>

void copy_ip(const char *ip) {
    char addr[16];
    if (strlen(ip) >= sizeof(addr)) {
        puts("invalid address");
        return;
    }
    strcpy(addr, ip);
    printf("ip %s\n", addr);
}
