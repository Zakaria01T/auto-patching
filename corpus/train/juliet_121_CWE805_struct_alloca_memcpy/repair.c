#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <alloca.h>

typedef struct {
    int intOne;
    int intTwo;
} twoIntsStruct;

void copy_block(void)
{
    twoIntsStruct * data;
    twoIntsStruct * dataBuffer = (twoIntsStruct *)alloca(50*sizeof(twoIntsStruct));
    data = dataBuffer;
    {
        twoIntsStruct source[100];
        {
            size_t i;
            for (i = 0; i < 100; i++)
            {
                source[i].intOne = 0;
                source[i].intTwo = 0;
            }
        }
        memcpy(data, source, 50*sizeof(twoIntsStruct));
        printf("%d -- %d\n", data[0].intOne, data[0].intTwo);
    }
}
