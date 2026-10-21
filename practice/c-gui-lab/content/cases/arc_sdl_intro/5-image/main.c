#include <stdio.h>
#include <SDL2/SDL.h>
#include <stdbool.h>


#define SCREEN_WIDTH 1920
#define SCREEN_HEIGHT 1080

bool init();
bool loadMedia();
void close();

//初始化我们将要渲染的窗口
SDL_Window* gWindow = NULL;

//The surface contained by the window
//窗口包含的surface
SDL_Surface* gScreenSurface = NULL;

//我们将会载入并在屏幕上展示的图片
SDL_Surface* gHelloWorld = NULL;



int main()
{
    printf("Hello World!\n");
    init();
    loadMedia();
    SDL_BlitSurface( gHelloWorld, NULL, gScreenSurface, NULL );
    SDL_UpdateWindowSurface( gWindow );
    SDL_Delay( 5000 );

    close();

    return 0;
}



bool init()
{
    //初始化标记变量
    bool success = true;

    //初始化 SDL
    if( SDL_Init( SDL_INIT_VIDEO ) < 0 )
    {
        printf( "SDL could not initialize! SDL_Error: %s\n", SDL_GetError() );
        success = false;
    }
    else
    {
        //创建 window
        gWindow = SDL_CreateWindow( "SDL Tutorial", SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, SCREEN_WIDTH, SCREEN_HEIGHT, SDL_WINDOW_SHOWN );
        if( gWindow == NULL )
        {
            printf( "Window could not be created! SDL_Error: %s\n", SDL_GetError() );
            success = false;
        }
        else
        {
            //获取 window surface
            gScreenSurface = SDL_GetWindowSurface( gWindow );
        }
    }

    return success;
}


bool loadMedia()
{
    //用来标记载入成功的变量
    bool success = true;

    //载入 splash image
    gHelloWorld = SDL_LoadBMP( "redflag.bmp" );
    if( gHelloWorld == NULL )
    {
        printf( "Unable to load image %s! SDL Error: %s\n", "02_getting_an_image_on_the_screen/hello_world.bmp", SDL_GetError() );
        success = false;
    }

    return success;
}


void close()
{
    //Deallocate surface
    SDL_FreeSurface( gHelloWorld );
    gHelloWorld = NULL;

    //Destroy window
    SDL_DestroyWindow( gWindow );
    gWindow = NULL;

    //Quit SDL subsystems
    SDL_Quit();
}
