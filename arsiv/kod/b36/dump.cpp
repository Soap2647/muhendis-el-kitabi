// dump.cpp: Doruk Lexer'ını çalıştırır, token akışını yazar.
// Kullanım: ./dump dosya.drk   veya   ./dump -s "metin"
#include "Lexer.h"
#include <fstream>
#include <iostream>
#include <sstream>

using namespace Doruk;

int main(int argc, char** argv) {
    std::string kaynak;
    if (argc >= 3 && std::string(argv[1]) == "-s") {
        kaynak = argv[2];
    } else {
        std::ifstream f(argv[1], std::ios::binary);
        std::stringstream ss;
        ss << f.rdbuf();
        kaynak = ss.str();
    }
    Lexer lx(kaynak, "test.drk");
    LexerSonucu r = lx.tara();
    for (const auto& t : r.tokenler) {
        std::cout << t.satir << ":" << t.sutun << "\t"
                  << tokenTuruAdi(t.tur) << "\t[" << t.lexem
                  << "]\n";
    }
    std::cout << "hata var mi: "
              << (r.basarili() ? "hayir" : "evet") << "\n";
    return 0;
}
