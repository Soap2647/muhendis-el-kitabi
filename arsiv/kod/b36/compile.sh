g++ -std=c++17 -O2 -Wall -Wextra \
    -Iengine/include dump.cpp \
    engine/src/Lexer.cpp engine/src/Token.cpp \
    engine/src/Diagnostics.cpp -o dump
