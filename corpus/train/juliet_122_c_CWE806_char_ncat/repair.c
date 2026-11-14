#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void append_text(void)
{
    char * data;
    data = (char *)malloc(100*sizeof(char));
    if (data == NULL) {exit(-1);}
    memset(data, 'A', 100-1);
    data[100-1] = '\0';
    {
        char dest[50] = "";
        strncat(dest, data, 50 - strlen(dest) - 1);
        dest[50-1] = '\0';
        printf("%s\n", data);
        free(data);
    }
}
