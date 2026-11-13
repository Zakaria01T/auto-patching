#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void copy_text(void)
{
    char * data;
    char dataBuffer[50];
    data = dataBuffer;
    data[0] = '\0';
    {
        char source[100];
        memset(source, 'C', 100-1);
        source[100-1] = '\0';
        strncpy(data, source, 50 - 1);
        data[50 - 1] = '\0';
        printf("%s\n", data);
    }
}
