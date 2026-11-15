// Sanal olmayan yikici: taban isaretcisiyle delete
#include <cstdio>

class Taban {
public:
#ifdef SANAL_YIKICI
    virtual
#endif
    ~Taban() { std::printf("Taban yikici\n"); }

    virtual void calis() { std::printf("Taban::calis\n"); }
};

class Tureyen : public Taban {
    int* tampon_;
public:
    Tureyen() : tampon_(new int[1000]) {}
    ~Tureyen() {
        std::printf("Tureyen yikici\n");
        delete[] tampon_;
    }
    void calis() override { std::printf("Tureyen::calis\n"); }
};

int main() {
    Taban* p = new Tureyen();   // is-a: Tureyen bir Taban
    p->calis();                 // sanal: Tureyen::calis
    delete p;                   // ~Tureyen calisir mi?
    return 0;
}
