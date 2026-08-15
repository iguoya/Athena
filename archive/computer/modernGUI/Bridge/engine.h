#ifndef ENGINE_H
#define ENGINE_H


class Engine
{
public:
    Engine();

    virtual void start() = 0;

    virtual ~Engine() = default;
};

#endif // ENGINE_H
