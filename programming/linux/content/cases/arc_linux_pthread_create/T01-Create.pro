TEMPLATE = app
CONFIG += console
CONFIG -= app_bundle
CONFIG -= qt

#QMAKE_CFLAGS += -pthread
#LIBS +=-lpthread

#QMAKE_CXXFLAGS += -std=c++0x -pthread


SOURCES += \
        main.c


LIBS += -lpthread
