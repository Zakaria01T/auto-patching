#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <alloca.h>

void append_text(void)
{
    char * data;
    char * dataBuffer = (char *)alloca(100*sizeof(char));
    data = dataBuffer;
    memset(data, 'A', 100-1);
    data[100-1] = '\0';
    {
        char dest[50] = "";
        strncat(dest, data, 50 - strlen(dest) - 1);
        dest[50-1] = '\0';
        printf("%s\n", data);
    }
}
