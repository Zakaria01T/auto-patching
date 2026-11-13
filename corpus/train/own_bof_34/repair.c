#include <stdio.h>
#include <string.h>

void menu_item(const char *dish, const char *price) {
    char item[20];
    snprintf(item, sizeof(item), "%s ... %s", dish, price);
    puts(item);
}
