QT       += core gui
QT += svg

greaterThan(QT_MAJOR_VERSION, 4): QT += widgets

CONFIG += c++17

# You can make your code fail to compile if it uses deprecated APIs.
# In order to do so, uncomment the following line.
#DEFINES += QT_DISABLE_DEPRECATED_BEFORE=0x060000    # disables all the APIs deprecated before Qt 6.0.0

#INCLUDEPATH += Strategy

SOURCES += \
    Facade/Facade.cpp \
    Facade/Navigation.cpp \
    Facade/Power.cpp \
    Facade/Rocket.cpp \
    Facade/SubSystemA.cpp \
    Facade/SubSystemB.cpp \
    Strategy/BubbleSort.cpp \
    Strategy/ConcreteStrategyA.cpp \
    Strategy/ConcreteStrategyB.cpp \
    Strategy/QuickSort.cpp \
    Strategy/SortAlgorithm.cpp \
    Strategy/Strategy.cpp \
    Strategy/StrategyContext.cpp \
    TemplateMethod/ConcreteClassA.cpp \
    TemplateMethod/ConcreteClassB.cpp \
    TemplateMethod/M1A1.cpp \
    TemplateMethod/T90.cpp \
    main.cpp \
    mainwindow.cpp

HEADERS += \
    Facade/Facade.h \
    Facade/Navigation.h \
    Facade/Power.h \
    Facade/Rocket.h \
    Facade/SubSystemA.h \
    Facade/SubSystemB.h \
    Strategy/BubbleSort.h \
    Strategy/ConcreteStrategyA.h \
    Strategy/ConcreteStrategyB.h \
    Strategy/QuickSort.h \
    Strategy/SortAlgorithm.h \
    Strategy/Strategy.h \
    Strategy/StrategyContext.h \
    TemplateMethod/AbstractClass.h \
    TemplateMethod/ConcreteClassA.h \
    TemplateMethod/ConcreteClassB.h \
    TemplateMethod/M1A1.h \
    TemplateMethod/T90.h \
    TemplateMethod/Tank.h \
    mainwindow.h

FORMS += \
    mainwindow.ui


# Default rules for deployment.
qnx: target.path = /tmp/$${TARGET}/bin
else: unix:!android: target.path = /opt/$${TARGET}/bin
!isEmpty(target.path): INSTALLS += target

DISTFILES += \
    Facade/Facade.vpp \
    Strategy/Strategy.vpp \
    Strategy/strategy.mdj

RESOURCES += \
    resource.qrc
