#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void append_text(void)
{
    char * data;
    char dataBuffer[50];
    data = dataBuffer;
    data[0] = '\0';
    {
        char source[100];
        memset(source, 'C', 100-1);
        source[100-1] = '\0';
        strncat(data, source, 100);
        printf("%s\n", data);
    }
}
