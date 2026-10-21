#include <stdio.h>
#include <SDL2/SDL.h>
//#include <SDL/

int main()
{
    printf("Hello World!\n");

    SDL_Init(SDL_INIT_VIDEO);

    SDL_Window *window = SDL_CreateWindow("SDL Tutorial",
                                          SDL_WINDOWPOS_UNDEFINED,
                                          SDL_WINDOWPOS_UNDEFINED,
                                          1920,
                                          1080,
                                          SDL_WINDOW_SHOWN
                                          );

    SDL_Surface *screen = SDL_GetWindowSurface(window);

    SDL_FillRect(screen, NULL, SDL_MapRGB(screen->format, 254, 40, 14));

    SDL_UpdateWindowSurface(window);

    SDL_Delay(5000);

    SDL_DestroyWindow(window);

    SDL_Quit();

//    SDL_Surface * screen = SDL_SetVideoMode(640, 480, 16, SDL_SWSURFACE);



//    atexit(SDL_Quit);

//    Draw_Line(screen, 240, 180, 400, 300, SDL_MapRGB(screen->format, 255, 255, 255));


    return 0;
}
