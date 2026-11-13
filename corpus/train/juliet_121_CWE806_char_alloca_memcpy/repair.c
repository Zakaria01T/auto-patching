#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <alloca.h>

void copy_block(void)
{
    char * data;
    char * dataBuffer = (char *)alloca(100*sizeof(char));
    data = dataBuffer;
    memset(data, 'A', 100-1);
    data[100-1] = '\0';
    {
        char dest[50] = "";
        size_t len = strlen(data);
        if (len > 50 - 1)
            len = 50 - 1;
        memcpy(dest, data, len*sizeof(char));
        dest[50-1] = '\0';
        printf("%s\n", data);
    }
}
