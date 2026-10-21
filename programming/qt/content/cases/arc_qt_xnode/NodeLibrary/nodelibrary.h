#ifndef NODELIBRARY_H
#define NODELIBRARY_H

#include "NodeLibrary_global.h"
#include "message.h"
#include "servernode.h"

class NODELIBRARY_EXPORT NodeLibrary
{
public:
    NodeLibrary();
    int add(int x, int y);
};

#endif // NODELIBRARY_H
