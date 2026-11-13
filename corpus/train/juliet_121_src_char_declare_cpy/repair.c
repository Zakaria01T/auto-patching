#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void copy_text(void)
{
    char * data;
    char dataBuffer[100];
    data = dataBuffer;
    memset(data, 'A', 100-1);
    data[100-1] = '\0';
    {
        char dest[50] = "";
        strncpy(dest, data, 50 - 1);
        dest[50 - 1] = '\0';
        printf("%s\n", data);
    }
}
