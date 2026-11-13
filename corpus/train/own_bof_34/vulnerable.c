#include <stdio.h>
#include <string.h>

void menu_item(const char *dish, const char *price) {
    char item[20];
    strcpy(item, dish);
    strcat(item, " ... ");
    strcat(item, price);
    puts(item);
}
