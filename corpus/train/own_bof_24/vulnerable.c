#include <stdio.h>
#include <string.h>

void copy_ip(const char *ip) {
    char addr[16];
    strcpy(addr, ip);
    printf("ip %s\n", addr);
}
