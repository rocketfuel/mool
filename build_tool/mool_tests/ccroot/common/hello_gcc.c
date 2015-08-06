#include <stdio.h>

int main()
{
    // g++ defines this macro along with __GNUC__, so we check this first.
    #ifdef __GNUG__
        printf("Detected g++ but looking for gcc!\n");
        return 1;
    #elif __GNUC__
        printf("Detected gcc.\n");
        return 0;
    #else
        printf("Unknown compiler!\n");
        return 1;
    #endif
}
