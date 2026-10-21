TEMPLATE = app
CONFIG += console
CONFIG -= app_bundle
CONFIG -= qt
QMAKE_CXXFLAGS += -pthread
SOURCES += \
        main.c

LIBS += -lpthread
